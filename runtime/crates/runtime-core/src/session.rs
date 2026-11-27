use std::fs::{self, File, OpenOptions};
use std::io::Write;
use std::path::{Path, PathBuf};
use std::time::{Duration, SystemTime, UNIX_EPOCH};

use anyhow::{Context, Result};
use fs2::FileExt;
use serde::{Deserialize, Serialize};
use sysinfo::{Pid, ProcessesToUpdate, System};
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize)]
struct SessionRecord {
    session_id: String,
    project_root: String,
    runtime_pid: u32,
    parent_pid: u32,
    parent_start_time: u64,
    started_at_unix: u64,
    ended_at_unix: Option<u64>,
    state: String,
}

#[derive(Debug, Clone, Serialize)]
pub struct SessionSnapshot {
    pub session_id: String,
    pub project_root: String,
    pub runtime_pid: u32,
    pub parent_pid: u32,
    pub parent_start_time: u64,
    pub started_at_unix: u64,
    pub ended_at_unix: Option<u64>,
    pub state: String,
}

fn unix_now() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs()
}

fn prepare_runtime_dir(project_root: &Path) -> Result<PathBuf> {
    let metadata = fs::symlink_metadata(project_root)
        .with_context(|| format!("cannot inspect project root: {}", project_root.display()))?;
    if metadata.file_type().is_symlink() || !metadata.is_dir() {
        anyhow::bail!("project root must be a real directory, not a symlink");
    }

    let rcoder_dir = project_root.join(".rcoder");
    ensure_real_directory(&rcoder_dir)?;
    let runtime_dir = rcoder_dir.join("runtime");
    ensure_private_directory(&runtime_dir)?;
    let sessions_dir = runtime_dir.join("sessions");
    ensure_private_directory(&sessions_dir)?;
    Ok(sessions_dir)
}

fn ensure_real_directory(path: &Path) -> Result<()> {
    if !path.exists() {
        fs::create_dir(path).with_context(|| format!("cannot create {}", path.display()))?;
    }
    let metadata =
        fs::symlink_metadata(path).with_context(|| format!("cannot inspect {}", path.display()))?;
    if metadata.file_type().is_symlink() || !metadata.is_dir() {
        anyhow::bail!("refusing non-directory or symlink at {}", path.display());
    }
    Ok(())
}

fn ensure_private_directory(path: &Path) -> Result<()> {
    ensure_real_directory(path)?;
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        fs::set_permissions(path, fs::Permissions::from_mode(0o700))
            .with_context(|| format!("cannot restrict permissions on {}", path.display()))?;
    }
    Ok(())
}

fn session_paths(sessions_dir: &Path, session_id: &str) -> (PathBuf, PathBuf) {
    (
        sessions_dir.join(format!("{session_id}.json")),
        sessions_dir.join(format!("{session_id}.lock")),
    )
}

fn persist_record(path: &Path, record: &SessionRecord) -> Result<()> {
    let bytes = serde_json::to_vec_pretty(record)?;
    let mut file = File::create(path)
        .with_context(|| format!("cannot write session record {}", path.display()))?;
    file.write_all(&bytes)?;
    file.sync_all()?;
    Ok(())
}

fn lock_is_held(path: &Path) -> Result<bool> {
    let metadata = match fs::symlink_metadata(path) {
        Ok(metadata) => metadata,
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => return Ok(false),
        Err(error) => return Err(error.into()),
    };
    if metadata.file_type().is_symlink() || !metadata.is_file() {
        return Ok(false);
    }

    let file = OpenOptions::new().read(true).write(true).open(path)?;
    match FileExt::try_lock_exclusive(&file) {
        Ok(()) => {
            let _ = FileExt::unlock(&file);
            Ok(false)
        }
        Err(error) if error.kind() == std::io::ErrorKind::WouldBlock => Ok(true),
        Err(error) => Err(error.into()),
    }
}

pub async fn attach_until_parent_exits(project_root: &Path, parent_pid: u32) -> Result<()> {
    let root = project_root
        .canonicalize()
        .with_context(|| format!("cannot resolve project root: {}", project_root.display()))?;
    if !root.is_dir() {
        anyhow::bail!("project root is not a directory");
    }

    let mut system = System::new();
    let parent = Pid::from_u32(parent_pid);
    system.refresh_processes(ProcessesToUpdate::Some(&[parent]), true);
    let parent_start_time = system
        .process(parent)
        .map(|process| process.start_time())
        .context("the parent MCP process is not running or cannot be inspected")?;

    let sessions_dir = prepare_runtime_dir(&root)?;
    let session_id = Uuid::new_v4().to_string();
    let (record_path, lock_path) = session_paths(&sessions_dir, &session_id);

    let lock_file = OpenOptions::new()
        .read(true)
        .write(true)
        .create_new(true)
        .open(&lock_path)
        .with_context(|| format!("cannot create session lock {}", lock_path.display()))?;
    FileExt::try_lock_exclusive(&lock_file).context("cannot acquire the Runtime session lock")?;

    let mut record = SessionRecord {
        session_id,
        project_root: root.display().to_string(),
        runtime_pid: std::process::id(),
        parent_pid,
        parent_start_time,
        started_at_unix: unix_now(),
        ended_at_unix: None,
        state: "active".to_string(),
    };
    persist_record(&record_path, &record)?;

    loop {
        tokio::time::sleep(Duration::from_millis(750)).await;
        system.refresh_processes(ProcessesToUpdate::Some(&[parent]), true);
        let still_same_process = system
            .process(parent)
            .map(|process| process.start_time() == parent_start_time)
            .unwrap_or(false);
        if !still_same_process {
            break;
        }
    }

    record.state = "stopped".to_string();
    record.ended_at_unix = Some(unix_now());
    persist_record(&record_path, &record)?;
    let _ = FileExt::unlock(&lock_file);
    Ok(())
}

pub fn list_sessions(project_root: &Path) -> Result<Vec<SessionSnapshot>> {
    let root = project_root
        .canonicalize()
        .with_context(|| format!("cannot resolve project root: {}", project_root.display()))?;
    let rcoder_dir = root.join(".rcoder");
    let runtime_dir = rcoder_dir.join("runtime");
    let sessions_dir = runtime_dir.join("sessions");
    for directory in [&rcoder_dir, &runtime_dir, &sessions_dir] {
        let metadata = match fs::symlink_metadata(directory) {
            Ok(metadata) => metadata,
            Err(error) if error.kind() == std::io::ErrorKind::NotFound => {
                return Ok(Vec::new());
            }
            Err(error) => return Err(error.into()),
        };
        if metadata.file_type().is_symlink() || !metadata.is_dir() {
            anyhow::bail!(
                "refusing to inspect non-directory or symlink at {}",
                directory.display()
            );
        }
    }

    let mut sessions = Vec::new();
    for entry in fs::read_dir(&sessions_dir)? {
        let entry = entry?;
        let path = entry.path();
        if path.extension().and_then(|value| value.to_str()) != Some("json") {
            continue;
        }
        let metadata = fs::symlink_metadata(&path)?;
        if metadata.file_type().is_symlink() || !metadata.is_file() {
            continue;
        }
        let bytes = fs::read(&path)?;
        let record: SessionRecord = match serde_json::from_slice(&bytes) {
            Ok(record) => record,
            Err(_) => continue,
        };
        let lock_path = path.with_extension("lock");
        let active = lock_is_held(&lock_path)?;
        let state = match (record.state.as_str(), active) {
            ("stopped", _) => "stopped",
            (_, true) => "active",
            _ => "orphaned",
        };
        sessions.push(SessionSnapshot {
            session_id: record.session_id,
            project_root: record.project_root,
            runtime_pid: record.runtime_pid,
            parent_pid: record.parent_pid,
            parent_start_time: record.parent_start_time,
            started_at_unix: record.started_at_unix,
            ended_at_unix: record.ended_at_unix,
            state: state.to_string(),
        });
    }
    sessions.sort_by(|left, right| left.started_at_unix.cmp(&right.started_at_unix));
    Ok(sessions)
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;
    use uuid::Uuid;

    fn fixture() -> PathBuf {
        let path = std::env::temp_dir().join(format!("rcoder-runtime-session-{}", Uuid::new_v4()));
        fs::create_dir_all(&path).expect("create fixture");
        path
    }

    #[test]
    fn reports_stale_unfinished_sessions_as_orphaned() {
        let root = fixture();
        let sessions = prepare_runtime_dir(&root).expect("prepare runtime dir");
        let record = SessionRecord {
            session_id: "session-1".to_string(),
            project_root: root.display().to_string(),
            runtime_pid: 10,
            parent_pid: 11,
            parent_start_time: 12,
            started_at_unix: 13,
            ended_at_unix: None,
            state: "active".to_string(),
        };
        let (record_path, lock_path) = session_paths(&sessions, &record.session_id);
        persist_record(&record_path, &record).expect("write record");
        File::create(&lock_path).expect("write unlocked lock file");

        let snapshots = list_sessions(&root).expect("list sessions");
        assert_eq!(snapshots.len(), 1);
        assert_eq!(snapshots[0].state, "orphaned");

        fs::remove_dir_all(root).expect("remove fixture");
    }

    #[test]
    fn rejects_symlinked_runtime_directory() {
        let root = fixture();
        let outside = fixture();
        #[cfg(unix)]
        {
            std::os::unix::fs::symlink(&outside, root.join(".rcoder")).expect("create symlink");
            assert!(prepare_runtime_dir(&root).is_err());
        }
        #[cfg(windows)]
        {
            let _ = outside;
        }
        fs::remove_dir_all(root).expect("remove root");
        fs::remove_dir_all(outside).expect("remove outside");
    }
}
