//! Task contracts, controlled state transitions, and acceptance evidence.
//!
//! This module records the execution contract; it does not intercept host tools
//! or grant permission to perform filesystem and process operations.

use std::fs::{self, File, OpenOptions};
use std::io::Write;
use std::path::Path;
use std::time::{SystemTime, UNIX_EPOCH};

use anyhow::{Context, Result};
use fs2::FileExt;
use serde::{Deserialize, Serialize};
use uuid::Uuid;

const MAX_OBJECTIVE_CHARS: usize = 10_000;
const MAX_CRITERIA: usize = 50;
const MAX_CONSTRAINTS: usize = 50;
const MAX_CRITERION_CHARS: usize = 2_000;
const MAX_CONSTRAINT_CHARS: usize = 2_000;
const MAX_EVIDENCE_SUMMARY_CHARS: usize = 2_500;
const MAX_EVIDENCE_SOURCE_CHARS: usize = 1_000;
const MAX_TRANSITION_REASON_CHARS: usize = 1_000;
const MAX_EVIDENCE_RECORDS: usize = 500;
const MAX_TRANSITIONS: usize = 200;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum RiskLevel {
    Low,
    Medium,
    High,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum TaskStatus {
    Draft,
    Active,
    Blocked,
    Completed,
    Cancelled,
}

impl TaskStatus {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::Draft => "draft",
            Self::Active => "active",
            Self::Blocked => "blocked",
            Self::Completed => "completed",
            Self::Cancelled => "cancelled",
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum EvidenceOutcome {
    Pass,
    Fail,
    NotRun,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AcceptanceCriterion {
    pub id: String,
    pub description: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EvidenceRecord {
    pub id: String,
    pub criterion_id: String,
    pub outcome: EvidenceOutcome,
    pub summary: String,
    pub source: String,
    pub recorded_at_unix: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StatusTransition {
    pub from: TaskStatus,
    pub to: TaskStatus,
    pub reason: Option<String>,
    pub transitioned_at_unix: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TaskContract {
    pub schema_version: u32,
    pub id: String,
    pub project_root: String,
    pub objective: String,
    pub acceptance_criteria: Vec<AcceptanceCriterion>,
    pub constraints: Vec<String>,
    pub risk_level: RiskLevel,
    pub status: TaskStatus,
    pub evidence: Vec<EvidenceRecord>,
    /// Index of the first evidence record belonging to the current completion cycle.
    /// Evidence before this boundary remains in the audit history but cannot satisfy
    /// acceptance criteria after a completed task has been reopened.
    #[serde(default)]
    pub completion_evidence_start_index: usize,
    pub history: Vec<StatusTransition>,
    pub created_at_unix: u64,
    pub updated_at_unix: u64,
}

fn unix_now() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs()
}

fn validate_text(value: &str, field: &str, max_chars: usize) -> Result<String> {
    let value = value.trim();
    if value.is_empty() {
        anyhow::bail!("{field} must not be empty");
    }
    if value.chars().count() > max_chars {
        anyhow::bail!("{field} exceeds {max_chars} characters");
    }
    Ok(value.to_string())
}

fn ensure_directory(path: &Path) -> Result<()> {
    match fs::symlink_metadata(path) {
        Ok(metadata) => {
            if metadata.file_type().is_symlink() || !metadata.is_dir() {
                anyhow::bail!("refusing non-directory or symlink at {}", path.display());
            }
        }
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => {
            match fs::create_dir(path) {
                Ok(()) => {}
                Err(create_error) if create_error.kind() == std::io::ErrorKind::AlreadyExists => {}
                Err(create_error) => return Err(create_error.into()),
            }
            let metadata = fs::symlink_metadata(path)?;
            if metadata.file_type().is_symlink() || !metadata.is_dir() {
                anyhow::bail!("refusing non-directory or symlink at {}", path.display());
            }
        }
        Err(error) => return Err(error.into()),
    }
    Ok(())
}

fn restrict_directory(path: &Path) -> Result<()> {
    ensure_directory(path)?;
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        fs::set_permissions(path, fs::Permissions::from_mode(0o700))
            .with_context(|| format!("cannot restrict permissions on {}", path.display()))?;
    }
    Ok(())
}

fn prepare_task_directory(project_root: &Path) -> Result<(std::path::PathBuf, String)> {
    let root = project_root
        .canonicalize()
        .with_context(|| format!("cannot resolve project root: {}", project_root.display()))?;
    if !root.is_dir() {
        anyhow::bail!("project root is not a directory");
    }

    let rcoder_dir = root.join(".rcoder");
    let runtime_dir = rcoder_dir.join("runtime");
    let tasks_dir = runtime_dir.join("tasks");
    ensure_directory(&rcoder_dir)?;
    restrict_directory(&runtime_dir)?;
    restrict_directory(&tasks_dir)?;
    Ok((tasks_dir, root.display().to_string()))
}

fn existing_task_directory(project_root: &Path) -> Result<Option<(std::path::PathBuf, String)>> {
    let root = project_root
        .canonicalize()
        .with_context(|| format!("cannot resolve project root: {}", project_root.display()))?;
    if !root.is_dir() {
        anyhow::bail!("project root is not a directory");
    }

    let rcoder_dir = root.join(".rcoder");
    let runtime_dir = rcoder_dir.join("runtime");
    let tasks_dir = runtime_dir.join("tasks");
    for directory in [&rcoder_dir, &runtime_dir, &tasks_dir] {
        match fs::symlink_metadata(directory) {
            Ok(metadata) => {
                if metadata.file_type().is_symlink() || !metadata.is_dir() {
                    anyhow::bail!(
                        "refusing non-directory or symlink at {}",
                        directory.display()
                    );
                }
            }
            Err(error) if error.kind() == std::io::ErrorKind::NotFound => return Ok(None),
            Err(error) => return Err(error.into()),
        }
    }
    Ok(Some((tasks_dir, root.display().to_string())))
}

fn canonical_task_id(value: &str) -> Result<String> {
    Uuid::parse_str(value)
        .map(|id| id.to_string())
        .context("task ID must be a UUID")
}

fn task_path(directory: &Path, id: &str) -> std::path::PathBuf {
    directory.join(format!("{id}.json"))
}

fn lock_task(directory: &Path, id: &str) -> Result<File> {
    let path = directory.join(format!("{id}.lock"));
    if let Ok(metadata) = fs::symlink_metadata(&path) {
        if metadata.file_type().is_symlink() || !metadata.is_file() {
            anyhow::bail!("refusing non-file or symlink at {}", path.display());
        }
    }

    let file = OpenOptions::new()
        .read(true)
        .write(true)
        .create(true)
        .truncate(false)
        .open(&path)
        .with_context(|| format!("cannot open task lock {}", path.display()))?;
    FileExt::lock_exclusive(&file).with_context(|| format!("cannot lock task {}", id))?;
    Ok(file)
}

fn read_task_locked(directory: &Path, id: &str) -> Result<TaskContract> {
    let path = task_path(directory, id);
    let metadata =
        fs::symlink_metadata(&path).with_context(|| format!("task {id} does not exist"))?;
    if metadata.file_type().is_symlink() || !metadata.is_file() {
        anyhow::bail!("refusing non-file or symlink at {}", path.display());
    }
    let bytes = fs::read(&path)?;
    let task: TaskContract =
        serde_json::from_slice(&bytes).context("task contract JSON is invalid")?;
    if task.schema_version != 1 {
        anyhow::bail!(
            "unsupported task contract schema version: {}",
            task.schema_version
        );
    }
    if task.id != id {
        anyhow::bail!("task contract ID does not match its storage filename");
    }
    if task.completion_evidence_start_index > task.evidence.len() {
        anyhow::bail!("task completion evidence boundary exceeds its evidence history");
    }
    Ok(task)
}

fn write_task_locked(directory: &Path, task: &TaskContract) -> Result<()> {
    let destination = task_path(directory, &task.id);
    if let Ok(metadata) = fs::symlink_metadata(&destination) {
        if metadata.file_type().is_symlink() || !metadata.is_file() {
            anyhow::bail!(
                "refusing to replace non-file or symlink at {}",
                destination.display()
            );
        }
    }

    let temporary = directory.join(format!(".{}.{}.tmp", task.id, Uuid::new_v4()));
    let bytes = serde_json::to_vec_pretty(task)?;
    let mut file = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(&temporary)
        .with_context(|| format!("cannot create temporary task file {}", temporary.display()))?;
    file.write_all(&bytes)?;
    file.sync_all()?;
    drop(file);

    // Windows rename does not replace an existing file. All readers and writers
    // take the task lock, so the short remove/rename window is not observable
    // through the Runtime API.
    #[cfg(windows)]
    if destination.exists() {
        fs::remove_file(&destination)?;
    }

    if let Err(error) = fs::rename(&temporary, &destination) {
        let _ = fs::remove_file(&temporary);
        return Err(error).with_context(|| format!("cannot persist task {}", task.id));
    }
    Ok(())
}

fn latest_outcome(task: &TaskContract, criterion_id: &str) -> Option<EvidenceOutcome> {
    task.evidence
        .iter()
        .skip(task.completion_evidence_start_index)
        .rev()
        .find(|record| record.criterion_id == criterion_id)
        .map(|record| record.outcome)
}

pub fn create_task(
    project_root: &Path,
    objective: &str,
    acceptance_criteria: &[String],
    constraints: &[String],
    risk_level: RiskLevel,
) -> Result<TaskContract> {
    let objective = validate_text(objective, "objective", MAX_OBJECTIVE_CHARS)?;
    if acceptance_criteria.is_empty() || acceptance_criteria.len() > MAX_CRITERIA {
        anyhow::bail!("acceptance criteria must contain 1..={MAX_CRITERIA} items");
    }
    if constraints.len() > MAX_CONSTRAINTS {
        anyhow::bail!("constraints must contain at most {MAX_CONSTRAINTS} items");
    }

    let criteria = acceptance_criteria
        .iter()
        .enumerate()
        .map(|(index, description)| {
            Ok(AcceptanceCriterion {
                id: format!("AC-{:03}", index + 1),
                description: validate_text(
                    description,
                    "acceptance criterion",
                    MAX_CRITERION_CHARS,
                )?,
            })
        })
        .collect::<Result<Vec<_>>>()?;
    let constraints = constraints
        .iter()
        .map(|value| validate_text(value, "constraint", MAX_CONSTRAINT_CHARS))
        .collect::<Result<Vec<_>>>()?;

    let (directory, root) = prepare_task_directory(project_root)?;
    let id = Uuid::new_v4().to_string();
    let lock = lock_task(&directory, &id)?;
    let now = unix_now();
    let task = TaskContract {
        schema_version: 1,
        id,
        project_root: root,
        objective,
        acceptance_criteria: criteria,
        constraints,
        risk_level,
        status: TaskStatus::Draft,
        evidence: Vec::new(),
        completion_evidence_start_index: 0,
        history: Vec::new(),
        created_at_unix: now,
        updated_at_unix: now,
    };
    write_task_locked(&directory, &task)?;
    let _ = FileExt::unlock(&lock);
    Ok(task)
}

pub fn list_tasks(project_root: &Path) -> Result<Vec<TaskContract>> {
    let Some((directory, _)) = existing_task_directory(project_root)? else {
        return Ok(Vec::new());
    };
    let mut tasks = Vec::new();
    for entry in fs::read_dir(&directory)? {
        let entry = entry?;
        let path = entry.path();
        if path.extension().and_then(|value| value.to_str()) != Some("json") {
            continue;
        }
        let metadata = fs::symlink_metadata(&path)?;
        if metadata.file_type().is_symlink() || !metadata.is_file() {
            continue;
        }
        let Some(id) = path.file_stem().and_then(|value| value.to_str()) else {
            continue;
        };
        if let Ok(task_id) = canonical_task_id(id) {
            if task_id == id {
                tasks.push(get_task(project_root, &task_id)?);
            }
        }
    }
    tasks.sort_by(|left, right| right.updated_at_unix.cmp(&left.updated_at_unix));
    Ok(tasks)
}

pub fn get_task(project_root: &Path, task_id: &str) -> Result<TaskContract> {
    let Some((directory, _)) = existing_task_directory(project_root)? else {
        anyhow::bail!("Runtime task store does not exist for this project");
    };
    let id = canonical_task_id(task_id)?;
    let lock = lock_task(&directory, &id)?;
    let task = read_task_locked(&directory, &id)?;
    let _ = FileExt::unlock(&lock);
    Ok(task)
}

pub fn record_evidence(
    project_root: &Path,
    task_id: &str,
    criterion_id: &str,
    outcome: EvidenceOutcome,
    summary: &str,
    source: &str,
) -> Result<TaskContract> {
    let Some((directory, _)) = existing_task_directory(project_root)? else {
        anyhow::bail!("Runtime task store does not exist for this project");
    };
    let id = canonical_task_id(task_id)?;
    let lock = lock_task(&directory, &id)?;
    let mut task = read_task_locked(&directory, &id)?;

    if task.status != TaskStatus::Active {
        anyhow::bail!("evidence can be recorded only while a task is active");
    }
    if !task
        .acceptance_criteria
        .iter()
        .any(|criterion| criterion.id == criterion_id)
    {
        anyhow::bail!("unknown acceptance criterion: {criterion_id}");
    }
    if task.evidence.len() >= MAX_EVIDENCE_RECORDS {
        anyhow::bail!("task evidence history is full ({MAX_EVIDENCE_RECORDS} records maximum)");
    }

    let summary = validate_text(summary, "evidence summary", MAX_EVIDENCE_SUMMARY_CHARS)?;
    let source = validate_text(source, "evidence source", MAX_EVIDENCE_SOURCE_CHARS)?;
    let now = unix_now();
    task.evidence.push(EvidenceRecord {
        id: Uuid::new_v4().to_string(),
        criterion_id: criterion_id.to_string(),
        outcome,
        summary,
        source,
        recorded_at_unix: now,
    });
    task.updated_at_unix = now;
    write_task_locked(&directory, &task)?;
    let _ = FileExt::unlock(&lock);
    Ok(task)
}

pub fn transition_task(
    project_root: &Path,
    task_id: &str,
    to: TaskStatus,
    reason: Option<&str>,
) -> Result<TaskContract> {
    let Some((directory, _)) = existing_task_directory(project_root)? else {
        anyhow::bail!("Runtime task store does not exist for this project");
    };
    let id = canonical_task_id(task_id)?;
    let lock = lock_task(&directory, &id)?;
    let mut task = read_task_locked(&directory, &id)?;
    let from = task.status;

    let allowed = matches!(
        (from, to),
        (TaskStatus::Draft, TaskStatus::Active)
            | (TaskStatus::Draft, TaskStatus::Cancelled)
            | (TaskStatus::Active, TaskStatus::Blocked)
            | (TaskStatus::Active, TaskStatus::Completed)
            | (TaskStatus::Active, TaskStatus::Cancelled)
            | (TaskStatus::Blocked, TaskStatus::Active)
            | (TaskStatus::Blocked, TaskStatus::Cancelled)
            | (TaskStatus::Completed, TaskStatus::Active)
    );
    if !allowed {
        anyhow::bail!(
            "invalid task state transition: {} -> {}",
            from.as_str(),
            to.as_str()
        );
    }

    if to == TaskStatus::Completed {
        let missing: Vec<&str> = task
            .acceptance_criteria
            .iter()
            .filter(|criterion| latest_outcome(&task, &criterion.id) != Some(EvidenceOutcome::Pass))
            .map(|criterion| criterion.id.as_str())
            .collect();
        if !missing.is_empty() {
            anyhow::bail!(
                "cannot complete task; acceptance criteria without latest passing evidence: {}",
                missing.join(", ")
            );
        }
    }

    let reason = reason
        .map(|value| validate_text(value, "transition reason", MAX_TRANSITION_REASON_CHARS))
        .transpose()?;
    if matches!(to, TaskStatus::Blocked)
        || (from == TaskStatus::Completed && to == TaskStatus::Active)
    {
        if reason.is_none() {
            anyhow::bail!("a reason is required when blocking or reopening a task");
        }
    }
    if task.history.len() >= MAX_TRANSITIONS {
        anyhow::bail!("task transition history is full ({MAX_TRANSITIONS} records maximum)");
    }

    let now = unix_now();
    if from == TaskStatus::Completed && to == TaskStatus::Active {
        // Preserve historical evidence for audit, but require a fresh verification
        // cycle before the reopened task can be completed again.
        task.completion_evidence_start_index = task.evidence.len();
    }
    task.history.push(StatusTransition {
        from,
        to,
        reason,
        transitioned_at_unix: now,
    });
    task.status = to;
    task.updated_at_unix = now;
    write_task_locked(&directory, &task)?;
    let _ = FileExt::unlock(&lock);
    Ok(task)
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::path::PathBuf;
    use uuid::Uuid;

    fn fixture() -> PathBuf {
        let path = std::env::temp_dir().join(format!("rcoder-runtime-task-{}", Uuid::new_v4()));
        fs::create_dir_all(&path).expect("create fixture");
        path
    }

    #[test]
    fn task_cannot_complete_until_every_criterion_has_latest_passing_evidence() {
        let root = fixture();
        let acceptance = vec![
            "Unit tests pass".to_string(),
            "No credential is written to logs".to_string(),
        ];
        let task = create_task(
            &root,
            "Implement a bounded task controller",
            &acceptance,
            &[],
            RiskLevel::High,
        )
        .expect("create task");
        assert_eq!(task.status, TaskStatus::Draft);
        assert_eq!(task.acceptance_criteria[0].id, "AC-001");

        let active = transition_task(&root, &task.id, TaskStatus::Active, None).expect("activate");
        assert_eq!(active.status, TaskStatus::Active);
        assert!(transition_task(&root, &task.id, TaskStatus::Completed, None).is_err());

        record_evidence(
            &root,
            &task.id,
            "AC-001",
            EvidenceOutcome::Pass,
            "The focused unit suite passed",
            "cargo test -p rcoder-runtime-core",
        )
        .expect("record first pass");
        record_evidence(
            &root,
            &task.id,
            "AC-002",
            EvidenceOutcome::Pass,
            "No secret-like value appears in the evidence export",
            "runtime security regression",
        )
        .expect("record second pass");
        let completed = transition_task(&root, &task.id, TaskStatus::Completed, None)
            .expect("complete with evidence");
        assert_eq!(completed.status, TaskStatus::Completed);
        assert_eq!(completed.history.len(), 2);
        assert!(transition_task(&root, &task.id, TaskStatus::Active, None).is_err());

        fs::remove_dir_all(root).expect("remove fixture");
    }

    #[test]
    fn latest_failing_evidence_reopens_a_completion_blocker() {
        let root = fixture();
        let acceptance = vec!["Build passes".to_string()];
        let task = create_task(
            &root,
            "Build a component",
            &acceptance,
            &[],
            RiskLevel::Medium,
        )
        .expect("create task");
        transition_task(&root, &task.id, TaskStatus::Active, None).expect("activate");
        record_evidence(
            &root,
            &task.id,
            "AC-001",
            EvidenceOutcome::Pass,
            "Build succeeded",
            "cargo build",
        )
        .expect("record pass");
        record_evidence(
            &root,
            &task.id,
            "AC-001",
            EvidenceOutcome::Fail,
            "A subsequent build failed",
            "cargo build",
        )
        .expect("record failure");
        assert!(transition_task(&root, &task.id, TaskStatus::Completed, None).is_err());
        fs::remove_dir_all(root).expect("remove fixture");
    }

    #[test]
    fn blocked_transition_requires_reason_and_can_resume() {
        let root = fixture();
        let task = create_task(
            &root,
            "Resolve a dependency",
            &["Cargo resolves".to_string()],
            &[],
            RiskLevel::Low,
        )
        .expect("create task");
        transition_task(&root, &task.id, TaskStatus::Active, None).expect("activate");
        assert!(transition_task(&root, &task.id, TaskStatus::Blocked, None).is_err());
        let blocked = transition_task(
            &root,
            &task.id,
            TaskStatus::Blocked,
            Some("Registry unavailable"),
        )
        .expect("block with reason");
        assert_eq!(blocked.status, TaskStatus::Blocked);
        let resumed = transition_task(&root, &task.id, TaskStatus::Active, None).expect("resume");
        assert_eq!(resumed.status, TaskStatus::Active);
        fs::remove_dir_all(root).expect("remove fixture");
    }

    #[test]
    fn completed_task_can_be_reopened_and_a_new_failure_blocks_completion() {
        let root = fixture();
        let task = create_task(
            &root,
            "Recheck a completed deliverable",
            &["Regression suite passes".to_string()],
            &[],
            RiskLevel::High,
        )
        .expect("create task");
        transition_task(&root, &task.id, TaskStatus::Active, None).expect("activate");
        record_evidence(
            &root,
            &task.id,
            "AC-001",
            EvidenceOutcome::Pass,
            "Initial regression suite passed",
            "CI run 100",
        )
        .expect("record initial pass");
        transition_task(&root, &task.id, TaskStatus::Completed, None).expect("complete task");

        assert!(transition_task(&root, &task.id, TaskStatus::Active, None).is_err());
        let reopened = transition_task(
            &root,
            &task.id,
            TaskStatus::Active,
            Some("A post-release regression was reported"),
        )
        .expect("reopen with a reason");
        assert_eq!(reopened.status, TaskStatus::Active);
        assert_eq!(reopened.evidence.len(), 1, "historical evidence remains auditable");
        assert_eq!(reopened.completion_evidence_start_index, 1);
        assert_eq!(latest_outcome(&reopened, "AC-001"), None);
        assert!(
            transition_task(&root, &task.id, TaskStatus::Completed, None).is_err(),
            "a reopened task must not reuse its pre-reopen passing evidence"
        );

        record_evidence(
            &root,
            &task.id,
            "AC-001",
            EvidenceOutcome::Fail,
            "A later regression check failed",
            "CI run 101",
        )
        .expect("record later failure");
        assert_eq!(latest_outcome(&get_task(&root, &task.id).expect("read failed task"), "AC-001"),
            Some(EvidenceOutcome::Fail));
        assert!(transition_task(&root, &task.id, TaskStatus::Completed, None).is_err());

        let repaired = record_evidence(
            &root,
            &task.id,
            "AC-001",
            EvidenceOutcome::Pass,
            "Regression fixed and suite passed",
            "CI run 102",
        )
        .expect("record repaired pass");
        assert_eq!(
            latest_outcome(&repaired, "AC-001"),
            Some(EvidenceOutcome::Pass)
        );
        transition_task(&root, &task.id, TaskStatus::Completed, None)
            .expect("complete after re-verification");
        fs::remove_dir_all(root).expect("remove fixture");
    }

    #[test]
    fn listing_and_reading_tasks_do_not_create_runtime_state() {
        let root = fixture();
        assert!(
            list_tasks(&root)
                .expect("list absent task store")
                .is_empty()
        );
        assert!(get_task(&root, "00000000-0000-4000-8000-000000000001").is_err());
        assert!(!root.join(".rcoder").exists());
        fs::remove_dir_all(root).expect("remove fixture");
    }

    #[test]
    fn legacy_task_contracts_default_to_the_first_evidence_cycle() {
        let root = fixture();
        let task = create_task(
            &root,
            "Read an older task contract",
            &["Tests pass".to_string()],
            &[],
            RiskLevel::Low,
        )
        .expect("create task");
        let mut serialized = serde_json::to_value(&task).expect("serialize task");
        serialized
            .as_object_mut()
            .expect("task JSON object")
            .remove("completion_evidence_start_index");

        let restored: TaskContract =
            serde_json::from_value(serialized).expect("deserialize legacy contract");
        assert_eq!(restored.completion_evidence_start_index, 0);
        fs::remove_dir_all(root).expect("remove fixture");
    }

    #[test]
    fn task_ids_are_validated_before_path_construction() {
        let root = fixture();
        assert!(get_task(&root, "../../README.md").is_err());
        fs::remove_dir_all(root).expect("remove fixture");
    }

    #[cfg(unix)]
    #[test]
    fn task_storage_rejects_symlinked_runtime_state() {
        let root = fixture();
        let outside = fixture();
        fs::create_dir(root.join(".rcoder")).expect("create rcoder dir");
        std::os::unix::fs::symlink(&outside, root.join(".rcoder/runtime")).expect("create symlink");
        assert!(
            create_task(
                &root,
                "Reject symlink",
                &["A".to_string()],
                &[],
                RiskLevel::Low
            )
            .is_err()
        );
        fs::remove_dir_all(root).expect("remove root");
        fs::remove_dir_all(outside).expect("remove outside");
    }
}
