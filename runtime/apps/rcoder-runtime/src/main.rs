use std::path::PathBuf;

use anyhow::Result;
use clap::{Parser, Subcommand, ValueEnum};
use rcoder_runtime_core::{
    ArtifactReference, EvidenceOutcome, RiskLevel, TaskStatus, attach_until_parent_exits,
    compile_task, create_task, detect_project, get_task, list_sessions, list_tasks,
    record_evidence, require_artifact_verification, transition_task, verify_artifact_references,
    verify_task_evidence,
};

#[derive(Debug, Parser)]
#[command(
    name = "rcoder-runtime",
    version,
    about = "Local control plane for RCoder MCP sessions and execution contracts"
)]
struct Cli {
    #[command(subcommand)]
    command: Command,
}

#[derive(Debug, Subcommand)]
enum Command {
    /// Detect project-local MCP configurations that point to RCoder.
    Detect {
        #[arg(long, default_value = ".")]
        project: PathBuf,
        #[arg(long)]
        json: bool,
    },
    /// Show Runtime sessions recorded for a project.
    Status {
        #[arg(long, default_value = ".")]
        project: PathBuf,
        #[arg(long)]
        json: bool,
    },
    /// Create, inspect, and update a typed execution contract.
    Task {
        #[command(subcommand)]
        command: TaskCommand,
    },
    /// Internal companion mode. The process exits when its MCP parent exits.
    #[command(hide = true)]
    Attach {
        #[arg(long, default_value = ".")]
        project: PathBuf,
        #[arg(long)]
        parent_pid: u32,
    },
}

#[derive(Debug, Subcommand)]
enum TaskCommand {
    /// Create a draft execution contract with explicit acceptance criteria.
    Create {
        #[arg(long, default_value = ".")]
        project: PathBuf,
        #[arg(long)]
        objective: String,
        #[arg(long = "acceptance", required = true)]
        acceptance_criteria: Vec<String>,
        #[arg(long = "constraint")]
        constraints: Vec<String>,
        #[arg(long, value_enum, default_value = "medium")]
        risk: RiskArg,
        #[arg(long)]
        json: bool,
    },
    /// List execution contracts for a project.
    List {
        #[arg(long, default_value = ".")]
        project: PathBuf,
        #[arg(long)]
        json: bool,
    },
    /// Show one execution contract, its evidence, and transition history.
    Show {
        #[arg(long, default_value = ".")]
        project: PathBuf,
        #[arg(long)]
        id: String,
        #[arg(long)]
        json: bool,
    },
    /// Compile an active task into a bounded, deterministic host-context packet.
    Compile {
        #[arg(long, default_value = ".")]
        project: PathBuf,
        #[arg(long, required_unless_present = "active", conflicts_with = "active")]
        id: Option<String>,
        #[arg(long, conflicts_with = "id")]
        active: bool,
        #[arg(long)]
        json: bool,
    },
    /// Record evidence against one acceptance criterion.
    Evidence {
        #[arg(long, default_value = ".")]
        project: PathBuf,
        #[arg(long)]
        id: String,
        #[arg(long)]
        criterion: String,
        #[arg(long, value_enum)]
        outcome: EvidenceArg,
        #[arg(long)]
        summary: String,
        #[arg(long)]
        source: String,
        #[arg(long)]
        json: bool,
    },
    /// Inspect a bounded artifact against a current-cycle evidence record.
    Verify {
        #[arg(long, default_value = ".")]
        project: PathBuf,
        #[arg(long)]
        id: String,
        #[arg(long)]
        evidence: String,
        #[arg(long)]
        artifact: String,
        #[arg(long = "expect-sha256")]
        expect_sha256: Option<String>,
        /// Allowlisted parser identifier for deterministic outcome extraction.
        #[arg(long)]
        parser: Option<String>,
        #[arg(long)]
        criterion: Option<String>,
        #[arg(long)]
        provenance: Option<String>,
        #[arg(long = "require-digest")]
        require_digest: bool,
        /// Opt the criterion into artifact-backed completion verification.
        #[arg(long)]
        enforce: bool,
        #[arg(long)]
        json: bool,
    },
    /// Move a task through the guarded state machine.
    Transition {
        #[arg(long, default_value = ".")]
        project: PathBuf,
        #[arg(long)]
        id: String,
        #[arg(long, value_enum)]
        to: TaskStatusArg,
        #[arg(long)]
        reason: Option<String>,
        #[arg(long)]
        json: bool,
    },
}

#[derive(Debug, Clone, Copy, ValueEnum)]
enum RiskArg {
    Low,
    Medium,
    High,
}

impl From<RiskArg> for RiskLevel {
    fn from(value: RiskArg) -> Self {
        match value {
            RiskArg::Low => Self::Low,
            RiskArg::Medium => Self::Medium,
            RiskArg::High => Self::High,
        }
    }
}

#[derive(Debug, Clone, Copy, ValueEnum)]
enum EvidenceArg {
    Pass,
    Fail,
    NotRun,
}

impl From<EvidenceArg> for EvidenceOutcome {
    fn from(value: EvidenceArg) -> Self {
        match value {
            EvidenceArg::Pass => Self::Pass,
            EvidenceArg::Fail => Self::Fail,
            EvidenceArg::NotRun => Self::NotRun,
        }
    }
}

#[derive(Debug, Clone, Copy, ValueEnum)]
enum TaskStatusArg {
    Draft,
    Active,
    Blocked,
    Completed,
    Cancelled,
}

impl From<TaskStatusArg> for TaskStatus {
    fn from(value: TaskStatusArg) -> Self {
        match value {
            TaskStatusArg::Draft => Self::Draft,
            TaskStatusArg::Active => Self::Active,
            TaskStatusArg::Blocked => Self::Blocked,
            TaskStatusArg::Completed => Self::Completed,
            TaskStatusArg::Cancelled => Self::Cancelled,
        }
    }
}

fn print_instruction_packet(
    packet: &rcoder_runtime_core::InstructionPacket,
    json: bool,
) -> Result<()> {
    if json {
        println!("{}", serde_json::to_string_pretty(packet)?);
    } else {
        println!("RCoder Runtime instruction packet");
        println!("Schema: {}", packet.schema_version);
        println!("Compiler: {}", packet.compiler_version);
        println!("SHA-256: {}", packet.digest_sha256);
        println!("Trust boundary: {}", packet.trust_boundary);
        println!("Execution rule: {}", packet.policy.execution_rule);
        println!("Completion rule: {}", packet.policy.completion_rule);
        println!("Evidence rule: {}", packet.policy.evidence_rule);
        println!("Task data:");
        println!("{}", serde_json::to_string_pretty(&packet.task)?);
    }
    Ok(())
}

fn print_task(task: &rcoder_runtime_core::TaskContract, json: bool) -> Result<()> {
    if json {
        println!("{}", serde_json::to_string_pretty(task)?);
    } else {
        println!("Task: {}", task.id);
        println!("Status: {}", task.status.as_str());
        println!(
            "Risk: {}",
            format!("{:?}", task.risk_level).to_ascii_lowercase()
        );
        println!("Objective: {}", task.objective);
        println!("Acceptance criteria:");
        for criterion in &task.acceptance_criteria {
            let outcome = task
                .evidence
                .iter()
                .skip(task.completion_evidence_start_index)
                .rev()
                .find(|evidence| evidence.criterion_id == criterion.id)
                .map(|evidence| format!("{:?}", evidence.outcome).to_ascii_lowercase())
                .unwrap_or_else(|| "not_recorded".to_string());
            println!(
                "  [{}] {} — {}",
                criterion.id, outcome, criterion.description
            );
        }
        if !task.constraints.is_empty() {
            println!("Constraints:");
            for constraint in &task.constraints {
                println!("  - {constraint}");
            }
        }
        println!("Evidence records: {}", task.evidence.len());
        if !task.evidence.is_empty() {
            println!("Evidence history:");
            for evidence in &task.evidence {
                println!(
                    "  {} {} @ {} — {} ({})",
                    evidence.criterion_id,
                    format!("{:?}", evidence.outcome).to_ascii_lowercase(),
                    evidence.recorded_at_unix,
                    evidence.summary,
                    evidence.source
                );
            }
        }
        if !task.history.is_empty() {
            println!("State history:");
            for transition in &task.history {
                println!(
                    "  {} -> {} @ {}{}",
                    transition.from.as_str(),
                    transition.to.as_str(),
                    transition.transitioned_at_unix,
                    transition
                        .reason
                        .as_deref()
                        .map(|reason| format!(" — {reason}"))
                        .unwrap_or_default()
                );
            }
        }
    }
    Ok(())
}

#[tokio::main]
async fn main() -> Result<()> {
    let cli = Cli::parse();
    match cli.command {
        Command::Detect { project, json } => {
            let report = detect_project(&project)?;
            if json {
                println!("{}", serde_json::to_string_pretty(&report)?);
            } else if report.servers.is_empty() {
                println!("No project-local RCoder MCP server was detected.");
                println!(
                    "Inspected {} configuration file(s).",
                    report.inspected_files.len()
                );
            } else {
                println!("Project: {}", report.project_root);
                for server in &report.servers {
                    println!(
                        "RCoder MCP: {} [{} / {}]",
                        server.name, server.config_file, server.transport
                    );
                }
            }
            for issue in report.issues {
                eprintln!("{}: {}", issue.config_file, issue.message);
            }
        }
        Command::Status { project, json } => {
            let sessions = list_sessions(&project)?;
            if json {
                println!("{}", serde_json::to_string_pretty(&sessions)?);
            } else if sessions.is_empty() {
                println!("No RCoder Runtime sessions are recorded for this project.");
            } else {
                for session in sessions {
                    println!(
                        "{}  session={}  parent_pid={}  parent_start={}  runtime_pid={}  started_at={}",
                        session.state,
                        session.session_id,
                        session.parent_pid,
                        session.parent_start_time,
                        session.runtime_pid,
                        session.started_at_unix
                    );
                }
            }
        }
        Command::Task { command } => match command {
            TaskCommand::Create {
                project,
                objective,
                acceptance_criteria,
                constraints,
                risk,
                json,
            } => {
                let task = create_task(
                    &project,
                    &objective,
                    &acceptance_criteria,
                    &constraints,
                    risk.into(),
                )?;
                print_task(&task, json)?;
            }
            TaskCommand::List { project, json } => {
                let tasks = list_tasks(&project)?;
                if json {
                    println!("{}", serde_json::to_string_pretty(&tasks)?);
                } else if tasks.is_empty() {
                    println!("No execution contracts are recorded for this project.");
                } else {
                    for task in tasks {
                        println!("{}  {}  {}", task.status.as_str(), task.id, task.objective);
                    }
                }
            }
            TaskCommand::Show { project, id, json } => {
                let task = get_task(&project, &id)?;
                print_task(&task, json)?;
            }
            TaskCommand::Compile {
                project,
                id,
                active,
                json,
            } => {
                let task = if active {
                    let mut active_tasks = list_tasks(&project)?
                        .into_iter()
                        .filter(|task| task.status == TaskStatus::Active)
                        .collect::<Vec<_>>();
                    match active_tasks.len() {
                        0 => anyhow::bail!("no active Runtime task is available to compile"),
                        1 => active_tasks.remove(0),
                        count => anyhow::bail!(
                            "{count} active Runtime tasks found; compile a specific --id or leave one active"
                        ),
                    }
                } else {
                    let task_id = id
                        .as_deref()
                        .ok_or_else(|| anyhow::anyhow!("--id or --active is required"))?;
                    get_task(&project, task_id)?
                };
                let packet = compile_task(&task)?;
                print_instruction_packet(&packet, json)?;
            }
            TaskCommand::Evidence {
                project,
                id,
                criterion,
                outcome,
                summary,
                source,
                json,
            } => {
                let task =
                    record_evidence(&project, &id, &criterion, outcome.into(), &summary, &source)?;
                print_task(&task, json)?;
            }
            TaskCommand::Verify {
                project,
                id,
                evidence,
                artifact,
                expect_sha256,
                parser,
                criterion,
                provenance,
                require_digest,
                enforce,
                json,
            } => {
                let report = if let Some(parser) = &parser {
                    if enforce {
                        let criterion_id = criterion.as_deref().ok_or_else(|| {
                            anyhow::anyhow!("--criterion is required when --enforce is used")
                        })?;
                        require_artifact_verification(
                            &project,
                            &id,
                            criterion_id,
                            parser,
                            require_digest,
                        )?;
                    }
                    let reference = ArtifactReference {
                        schema_version: 1,
                        artifact: artifact.clone(),
                        parser: Some(parser.clone()),
                        expected_sha256: expect_sha256.clone(),
                        criterion_id: criterion.clone(),
                        evidence_id: evidence.clone(),
                        declared_outcome: None,
                        provenance: provenance.unwrap_or_else(|| "cli:local".to_string()),
                    };
                    let (_, mut reports) = verify_artifact_references(&project, &id, &[reference])?;
                    reports.remove(0)
                } else {
                    if enforce || require_digest {
                        anyhow::bail!("--parser is required with --enforce or --require-digest");
                    }
                    let (_, report) = verify_task_evidence(
                        &project,
                        &id,
                        &evidence,
                        &artifact,
                        expect_sha256.as_deref(),
                    )?;
                    report
                };
                if json {
                    println!("{}", serde_json::to_string_pretty(&report)?);
                } else {
                    println!("Artifact: {}", report.artifact);
                    println!("Verdict: {}", report.verdict.as_str());
                    println!(
                        "Verification state: {}",
                        report.verification_state().as_str()
                    );
                    println!("Detail: {}", report.detail);
                    println!("Size: {} bytes", report.size_bytes);
                    println!("SHA-256: {}", report.sha256);
                    println!("Evidence: {}", report.evidence_id);
                    println!("Criterion: {}", report.criterion_id);
                    println!("Provenance: {}", report.provenance);
                    println!("Observed at: {}", report.inspected_at_unix);
                    if let Some(outcome) = &report.outcome {
                        println!(
                            "Extracted: {} passed, {} failed, {} skipped, {} errors",
                            outcome.passed, outcome.failed, outcome.skipped, outcome.errors
                        );
                    }
                    println!("Declared claim: {:?}", report.declared_outcome);
                    println!("Digest match alone is never proof that tests passed");
                }
            }
            TaskCommand::Transition {
                project,
                id,
                to,
                reason,
                json,
            } => {
                let task = transition_task(&project, &id, to.into(), reason.as_deref())?;
                print_task(&task, json)?;
            }
        },
        Command::Attach {
            project,
            parent_pid,
        } => {
            attach_until_parent_exits(&project, parent_pid).await?;
        }
    }
    Ok(())
}

#[cfg(test)]
mod cli_tests {
    use super::*;

    #[test]
    fn task_create_accepts_multiple_acceptance_criteria() {
        let cli = Cli::try_parse_from([
            "rcoder-runtime",
            "task",
            "create",
            "--project",
            ".",
            "--objective",
            "Implement a feature",
            "--acceptance",
            "Tests pass",
            "--acceptance",
            "Diff is scoped",
            "--risk",
            "high",
            "--json",
        ])
        .expect("parse task create command");

        match cli.command {
            Command::Task {
                command:
                    TaskCommand::Create {
                        acceptance_criteria,
                        risk,
                        json,
                        ..
                    },
            } => {
                assert_eq!(acceptance_criteria.len(), 2);
                assert!(matches!(risk, RiskArg::High));
                assert!(json);
            }
            other => panic!("unexpected command: {other:?}"),
        }
    }

    #[test]
    fn task_compile_command_parses_json_mode() {
        let cli = Cli::try_parse_from([
            "rcoder-runtime",
            "task",
            "compile",
            "--id",
            "00000000-0000-4000-8000-000000000001",
            "--json",
        ])
        .expect("parse task compile command");

        match cli.command {
            Command::Task {
                command:
                    TaskCommand::Compile {
                        id, active, json, ..
                    },
            } => {
                assert_eq!(id.as_deref(), Some("00000000-0000-4000-8000-000000000001"));
                assert!(!active);
                assert!(json);
            }
            other => panic!("unexpected command: {other:?}"),
        }
    }

    #[test]
    fn task_compile_command_parses_unique_active_selector() {
        let cli = Cli::try_parse_from(["rcoder-runtime", "task", "compile", "--active", "--json"])
            .expect("parse active task compile command");

        match cli.command {
            Command::Task {
                command:
                    TaskCommand::Compile {
                        id, active, json, ..
                    },
            } => {
                assert!(id.is_none());
                assert!(active);
                assert!(json);
            }
            other => panic!("unexpected command: {other:?}"),
        }
    }

    #[test]
    fn task_transition_command_parses_reopen_reason() {
        let cli = Cli::try_parse_from([
            "rcoder-runtime",
            "task",
            "transition",
            "--id",
            "00000000-0000-4000-8000-000000000001",
            "--to",
            "active",
            "--reason",
            "A regression needs re-verification",
        ])
        .expect("parse task reopen command");

        match cli.command {
            Command::Task {
                command:
                    TaskCommand::Transition {
                        to: TaskStatusArg::Active,
                        reason,
                        ..
                    },
            } => {
                assert_eq!(
                    reason.as_deref(),
                    Some("A regression needs re-verification")
                );
            }
            other => panic!("unexpected command: {other:?}"),
        }
    }

    #[test]
    fn task_evidence_command_parses_attestation_fields() {
        let cli = Cli::try_parse_from([
            "rcoder-runtime",
            "task",
            "evidence",
            "--id",
            "00000000-0000-4000-8000-000000000001",
            "--criterion",
            "AC-001",
            "--outcome",
            "not-run",
            "--summary",
            "Build not run",
            "--source",
            "CI log reference",
        ])
        .expect("parse task evidence command");

        match cli.command {
            Command::Task {
                command:
                    TaskCommand::Evidence {
                        outcome, criterion, ..
                    },
            } => {
                assert!(matches!(outcome, EvidenceArg::NotRun));
                assert_eq!(criterion, "AC-001");
            }
            other => panic!("unexpected command: {other:?}"),
        }
    }

    #[test]
    fn task_verify_command_parses_artifact_inspection_fields() {
        let digest = "a".repeat(64);
        let cli = Cli::try_parse_from([
            "rcoder-runtime",
            "task",
            "verify",
            "--id",
            "00000000-0000-4000-8000-000000000001",
            "--evidence",
            "00000000-0000-4000-8000-000000000002",
            "--artifact",
            "artifacts/test.log",
            "--expect-sha256",
            &digest,
            "--json",
        ])
        .expect("parse task verify command");

        match cli.command {
            Command::Task {
                command:
                    TaskCommand::Verify {
                        artifact,
                        expect_sha256,
                        json,
                        ..
                    },
            } => {
                assert_eq!(artifact, "artifacts/test.log");
                assert_eq!(expect_sha256.as_deref(), Some(digest.as_str()));
                assert!(json);
            }
            other => panic!("unexpected command: {other:?}"),
        }
    }

    #[test]
    fn task_verify_command_parses_artifact_backed_fields() {
        let cli = Cli::try_parse_from([
            "rcoder-runtime",
            "task",
            "verify",
            "--id",
            "00000000-0000-4000-8000-000000000001",
            "--evidence",
            "00000000-0000-4000-8000-000000000002",
            "--artifact",
            "artifacts/report.json",
            "--parser",
            "rcoder_test_report_v1",
            "--criterion",
            "AC-001",
            "--provenance",
            "cli:unit",
            "--require-digest",
            "--enforce",
        ])
        .expect("parse artifact-backed verify command");

        match cli.command {
            Command::Task {
                command:
                    TaskCommand::Verify {
                        parser,
                        criterion,
                        provenance,
                        require_digest,
                        enforce,
                        ..
                    },
            } => {
                assert_eq!(parser.as_deref(), Some("rcoder_test_report_v1"));
                assert_eq!(criterion.as_deref(), Some("AC-001"));
                assert_eq!(provenance.as_deref(), Some("cli:unit"));
                assert!(require_digest);
                assert!(enforce);
            }
            other => panic!("unexpected command: {other:?}"),
        }
    }
}
