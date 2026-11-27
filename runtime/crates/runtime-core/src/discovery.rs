use std::fs;
use std::path::{Path, PathBuf};

use anyhow::{Context, Result};
use serde::Serialize;
use serde_json::Value;

const CONFIG_CANDIDATES: &[&str] = &[
    ".mcp.json",
    "mcp.json",
    ".vscode/mcp.json",
    ".cursor/mcp.json",
    ".windsurf/mcp_config.json",
    "opencode.json",
    ".opencode/opencode.json",
];

#[derive(Debug, Clone, Serialize)]
pub struct DetectedServer {
    pub name: String,
    pub config_file: String,
    pub transport: String,
}

#[derive(Debug, Clone, Serialize)]
pub struct ConfigIssue {
    pub config_file: String,
    pub message: String,
}

#[derive(Debug, Clone, Serialize)]
pub struct DetectionReport {
    pub project_root: String,
    pub inspected_files: Vec<String>,
    pub servers: Vec<DetectedServer>,
    pub issues: Vec<ConfigIssue>,
}

pub fn detect_project(project_root: &Path) -> Result<DetectionReport> {
    let root = project_root
        .canonicalize()
        .with_context(|| format!("cannot resolve project root: {}", project_root.display()))?;
    if !root.is_dir() {
        anyhow::bail!("project root is not a directory: {}", root.display());
    }

    let mut report = DetectionReport {
        project_root: root.display().to_string(),
        inspected_files: Vec::new(),
        servers: Vec::new(),
        issues: Vec::new(),
    };

    for relative in CONFIG_CANDIDATES {
        let path = root.join(relative);
        if !path.is_file() {
            continue;
        }

        report.inspected_files.push((*relative).to_string());
        let text = match fs::read_to_string(&path) {
            Ok(text) => text,
            Err(error) => {
                report.issues.push(ConfigIssue {
                    config_file: (*relative).to_string(),
                    message: format!("cannot read configuration: {error}"),
                });
                continue;
            }
        };

        let document: Value = match serde_json::from_str(&text) {
            Ok(value) => value,
            Err(error) => {
                report.issues.push(ConfigIssue {
                    config_file: (*relative).to_string(),
                    message: format!("invalid JSON: {error}"),
                });
                continue;
            }
        };

        for key in ["mcpServers", "servers", "mcp"] {
            let Some(servers) = document.get(key).and_then(Value::as_object) else {
                continue;
            };

            for (name, definition) in servers {
                if !is_rcoder_server(name, definition) {
                    continue;
                }

                let transport = if definition.get("url").and_then(Value::as_str).is_some() {
                    "remote"
                } else {
                    "stdio"
                };

                let item = DetectedServer {
                    name: name.clone(),
                    config_file: (*relative).to_string(),
                    transport: transport.to_string(),
                };
                if !report.servers.iter().any(|existing| {
                    existing.name == item.name && existing.config_file == item.config_file
                }) {
                    report.servers.push(item);
                }
            }
        }
    }

    report.servers.sort_by(|left, right| {
        left.config_file
            .cmp(&right.config_file)
            .then_with(|| left.name.cmp(&right.name))
    });
    report.inspected_files.sort();
    Ok(report)
}

fn is_rcoder_server(_name: &str, definition: &Value) -> bool {
    let Some(object) = definition.as_object() else {
        return false;
    };

    for field in ["command", "args", "executable", "module"] {
        if let Some(value) = object.get(field) {
            if contains_rcoder_entrypoint(value, 0) {
                return true;
            }
        }
    }
    false
}

fn contains_rcoder_entrypoint(value: &Value, depth: usize) -> bool {
    if depth > 8 {
        return false;
    }

    match value {
        Value::String(text) => {
            let normalized = text.to_ascii_lowercase().replace('\\', "/");
            normalized.split_whitespace().any(|raw_token| {
                let token = raw_token.trim_matches(|character| character == '"' || character == '\\'' || character == ',');
                let basename = token.rsplit('/').next().unwrap_or(token);
                matches!(
                    basename,
                    "rcoder_mcp.py"
                        | "rcoder_mcp_modern.py"
                        | "rcoder_mcp"
                        | "rcoder-mcp"
                        | "rcoder-mcp.mjs"
                        | "rcoder-mcp.exe"
                        | "rcoder-mcp.cmd"
                        | "rcoder-mcp.bat"
                )
            })
        }
        Value::Array(items) => items
            .iter()
            .any(|item| contains_rcoder_entrypoint(item, depth + 1)),
        _ => false,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;
    use uuid::Uuid;

    fn fixture() -> PathBuf {
        let path = std::env::temp_dir().join(format!("rcoder-runtime-detect-{}", Uuid::new_v4()));
        fs::create_dir_all(&path).expect("create fixture");
        path
    }

    #[test]
    fn detects_rcoder_in_claude_and_opencode_manifests() {
        let root = fixture();
        fs::write(
            root.join(".mcp.json"),
            r#"{"mcpServers":{"serena":{"command":"uvx","args":["serena"]},"rcoder":{"command":"python","args":["skills/rcoder/scripts/rcoder_mcp.py"]}}}"#,
        )
        .expect("write Claude config");
        fs::write(
            root.join("opencode.json"),
            r#"{"mcp":{"rcoder-tools":{"type":"local","command":["python","rcoder_mcp.py"]}}}"#,
        )
        .expect("write OpenCode config");

        let report = detect_project(&root).expect("detect project");
        assert_eq!(report.servers.len(), 2);
        assert!(report.servers.iter().any(|server| server.name == "rcoder"));
        assert!(
            report
                .servers
                .iter()
                .any(|server| server.name == "rcoder-tools")
        );
        assert!(!report.servers.iter().any(|server| server.name == "serena"));

        fs::remove_dir_all(root).expect("remove fixture");
    }

    #[test]
    fn detects_entrypoint_even_when_server_name_is_custom() {
        let root = fixture();
        fs::create_dir_all(root.join(".vscode")).expect("create vscode config dir");
        fs::write(
            root.join(".vscode/mcp.json"),
            r#"{"servers":{"engineering-tools":{"type":"stdio","command":"python","args":["-m","rcoder_mcp"]}}}"#,
        )
        .expect("write VS Code config");

        let report = detect_project(&root).expect("detect project");
        assert_eq!(report.servers.len(), 1);
        assert_eq!(report.servers[0].name, "engineering-tools");

        fs::remove_dir_all(root).expect("remove fixture");
    }

    #[test]
    fn malformed_manifest_is_reported_without_stopping_other_detection() {
        let root = fixture();
        fs::write(root.join(".mcp.json"), "{broken").expect("write malformed config");
        fs::write(
            root.join("opencode.json"),
            r#"{"mcp":{"rcoder":{"type":"local","command":["python","rcoder_mcp.py"]}}}"#,
        )
        .expect("write valid config");

        let report = detect_project(&root).expect("detect project");
        assert_eq!(report.issues.len(), 1);
        assert_eq!(report.servers.len(), 1);

        fs::remove_dir_all(root).expect("remove fixture");
    }

    #[test]
    fn a_server_named_rcoder_without_the_rcoder_entrypoint_is_not_a_match() {
        let root = fixture();
        fs::write(
            root.join(".mcp.json"),
            r#"{"mcpServers":{"rcoder":{"command":"python","args":["some-other-server.py"]}}}"#,
        )
        .expect("write config");

        let report = detect_project(&root).expect("detect project");
        assert!(report.servers.is_empty());

        fs::remove_dir_all(root).expect("remove fixture");
    }

    #[test]
    fn unrelated_mcp_servers_do_not_trigger_detection() {
        let root = fixture();
        fs::write(
            root.join(".mcp.json"),
            r#"{"mcpServers":{"serena":{"command":"uvx","args":["serena"]},"filesystem":{"command":"npx","args":["mcp-filesystem"]}}}"#,
        )
        .expect("write config");

        let report = detect_project(&root).expect("detect project");
        assert!(report.servers.is_empty());

        fs::remove_dir_all(root).expect("remove fixture");
    }
}
