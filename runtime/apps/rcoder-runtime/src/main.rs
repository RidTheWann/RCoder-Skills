use std::path::PathBuf;

use anyhow::Result;
use clap::{Parser, Subcommand};
use rcoder_runtime_core::{attach_until_parent_exits, detect_project, list_sessions};

#[derive(Debug, Parser)]
#[command(
    name = "rcoder-runtime",
    version,
    about = "Local lifecycle control plane for RCoder MCP sessions"
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
    /// Internal companion mode. The process exits when its MCP parent exits.
    #[command(hide = true)]
    Attach {
        #[arg(long, default_value = ".")]
        project: PathBuf,
        #[arg(long)]
        parent_pid: u32,
    },
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
                        "{}  session={}  parent_pid={}  runtime_pid={}  started_at={}",
                        session.state,
                        session.session_id,
                        session.parent_pid,
                        session.runtime_pid,
                        session.started_at_unix
                    );
                }
            }
        }
        Command::Attach {
            project,
            parent_pid,
        } => {
            attach_until_parent_exits(&project, parent_pid).await?;
        }
    }
    Ok(())
}
