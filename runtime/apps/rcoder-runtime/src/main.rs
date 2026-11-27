use std::path::PathBuf;

use anyhow::Result;
use clap::{Parser, Subcommand, ValueEnum};
use rcoder_runtime_core::{
    EvidenceOutcome, RiskLevel, TaskStatus, attach_until_parent_exits, create_task, detect_project,
    get_task, list_sessions, list_tasks, record_evidence, transition_task,
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
}
