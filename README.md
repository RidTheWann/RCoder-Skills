# RCoder

[![RCoder Quality CI](https://github.com/RidTheWann/RCoder-Skills/actions/workflows/quality.yml/badge.svg)](https://github.com/RidTheWann/RCoder-Skills/actions/workflows/quality.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform Support](https://img.shields.io/badge/Platforms-Windows%20%7C%20Linux%20%7C%20macOS-informational)](#supported-hosts--environments)

**RCoder** is a lightweight, portable, model-agnostic software engineering skill and orchestration toolkit for agentic AI and coding CLIs. Built on the progressive disclosure architecture, RCoder exposes concise routing metadata upfront and loads detailed specialist protocols only when required by the active task.

---

## Table of Contents

- [Key Features](#key-features)
- [Quick Start & Installation](#quick-start--installation)
  - [Windows PowerShell (One-Liner)](#1-windows-powershell-one-liner)
  - [Node.js / npm (Cross-Platform)](#2-nodejs--npm-cross-platform)
- [Terminal Launcher CLI](#terminal-launcher-cli)
- [Tooling Suite](#tooling-suite)
  - [RScan: Automated Project Reconnaissance](#rscan-automated-project-reconnaissance)
  - [RSaver: Context Management & Compression](#rsaver-context-management--compression)
  - [MCP Server Infrastructure](#mcp-server-infrastructure)
  - [Agent Skill Authoring Toolkit](#agent-skill-authoring-toolkit)
  - [Opt-in Hook Management](#opt-in-hook-management)
- [Supported Hosts & Environments](#supported-hosts--environments)
- [Specialist Domains](#specialist-domains)
- [Developer Guide & Verification](#developer-guide--verification)
- [Evaluation & Benchmarks](#evaluation--benchmarks)
- [License](#license)

---

## Key Features

- **Progressive Disclosure Architecture:** Minimal token footprint at session start; detailed domain instructions load on demand.
- **Model & Host Agnostic:** Integrates seamlessly across 20+ agentic AI hosts including Claude Code, Cursor, Codex, OpenCode, and Copilot.
- **Comprehensive Specialist Router:** 13-section domain guidelines covering software engineering, systems programming, reverse engineering, and defensive cybersecurity.
- **Deterministic Context Optimization (RSaver):** Transparent token budgeting, duplicate compaction, and exact range reconstruction.
- **Safe Automated Reconnaissance (RScan):** Read-only, bounded inspection yielding ranked development roadmaps.
- **Zero-Dependency Stdio MCP Server:** Conforms strictly to Model Context Protocol standards without third-party dependencies.

---

## Quick Start & Installation

RCoder provides two native installation paths. Both configure target discovery roots and provision the global `rcoder` command.

### 1. Windows PowerShell (One-Liner)

Install into the current project (`.agents/skills/rcoder`) and register the `%USERPROFILE%\.rcoder\bin\rcoder.cmd` terminal launcher:

```powershell
irm https://raw.githubusercontent.com/RidTheWann/RCoder-Skills/main/install.ps1 | iex
```

> **Note:** Compatible with Windows PowerShell 5.1 and PowerShell 7+. Node.js is **not** required for this route.

To target a specific host or user-level scope:

```powershell
& ([scriptblock]::Create((irm 'https://raw.githubusercontent.com/RidTheWann/RCoder-Skills/main/install.ps1'))) -Target qoder -Scope user
```

Append `-Mcp show` to view the host MCP configuration, or `-Mcp install` to configure it automatically.

### 2. Node.js / npm (Cross-Platform)

Requires Node.js 18.18+, npm, and Git:

```sh
npx -y github:RidTheWann/RCoder-Skills
```

- **Linux / macOS:** Installs launcher to `~/.local/bin/rcoder`.
- **Windows:** Installs launcher to `%USERPROFILE%\.rcoder\bin\rcoder.cmd`.

Target specific hosts and scopes non-interactively:

```sh
npx -y github:RidTheWann/RCoder-Skills --target codex --scope project
npx -y github:RidTheWann/RCoder-Skills --target factory --scope user
```

---

## Terminal Launcher CLI

Launch the interactive management dashboard from any terminal:

```sh
rcoder
```

```text
============================================================
                     RCoder Management
============================================================
1. Install / Update RCoder
2. Uninstall RCoder
3. Show supported agents
4. Set up MCP server
0. Exit
```

### CLI Subcommands

The global `rcoder` command routes subcommands directly:

```sh
# Host integrations
rcoder integration install opencode --scope project
rcoder integration install gemini-cli
rcoder integration install codex
rcoder integration install claude-code
rcoder integration verify opencode --scope project

# Environment diagnostics
rcoder doctor --json

# Agent Skill management
rcoder skill new custom-domain --description "Guidance for custom domain workflows."
rcoder skill lint ./custom-domain
rcoder skill package ./custom-domain --out ./dist/custom-domain.zip

# Lifecycle hooks
rcoder hooks install --scope project --dry-run
rcoder hooks install --scope user --profile strict
rcoder hooks uninstall --scope project
rcoder hooks print-config
```

---

## Tooling Suite

### RScan: Automated Project Reconnaissance

RScan (`skills/rcoder/scripts/rscan.py`) conducts bounded, read-only inspections of project workspaces:

```sh
python3 skills/rcoder/scripts/rscan.py scan --root .
```

- Discovers frameworks, runtimes, package configurations, and test suites.
- Flags security exposures and repository risks.
- Generates a prioritized development menu linked to relevant RCoder specialists.

### RSaver: Context Management & Compression

RSaver (`skills/rcoder/scripts/rsaver.py`) guards against context window overflow and semantic drift:

- **Audit & Budgeting:** `rsaver audit` ranks project files by estimated token impact.
- **Redaction:** `rsaver redact` masks secrets and credentials deterministically before submission.
- **Exact-Recovery Compression:** `rsaver pack` and `rsaver unpack` compress repetitive content with verifiable SHA-256 reconstruction.
- **Drift Detection:** `rsaver drift` and `rsaver anchor` isolate objectives and ground ongoing dialogue.

### MCP Server Infrastructure

RCoder includes a zero-dependency, root-confined stdio [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server (`skills/rcoder/scripts/rcoder_mcp.py`):

```sh
# Generate host configuration snippets
python3 skills/rcoder/scripts/rcoder_mcp.py --print-config claude-code
python3 skills/rcoder/scripts/rcoder_mcp.py --root . --profile minimal
```

- Confined strictly to the workspace root; refuses symlinks and sensitive files.
- Operates without subprocess shells or network sockets.
- Optional loopback Streamable HTTP transport available for specialized clients (`docs/MCP.md`).

### Agent Skill Authoring Toolkit

Standardized scaffolding and packaging for agent skills:

```sh
rcoder skill new mcp-observability --description "Specialist for MCP telemetry workflows."
rcoder skill lint ./mcp-observability
rcoder skill package ./mcp-observability --out ./dist/mcp-observability.zip
```

Enforces 13-section modular architecture, strictly bounds references, verifies links, blocks private keys/secrets, and creates deterministic ZIP packages with SHA-256 sidecars.

### Opt-in Hook Management

Safely manage lifecycle integration points (such as Claude Code `PreToolUse` and `Stop` hooks):

```sh
rcoder hooks install --scope project --dry-run
rcoder hooks install --scope user --profile strict
```

Hooks execute with zero dependencies, refuse symlinks, validate strict JSON formats, and fail open to protect developer workflow continuity.

---

## Supported Hosts & Environments

`targets.json` defines canonical installation roots across all supported agents:

| Host Platform | Project Skill Root | User Skill Root |
|---|---|---|
| **Claude Code** | `.claude/skills` | `~/.claude/skills` |
| **OpenAI Codex CLI** | `.agents/skills` | `~/.agents/skills` |
| **Cursor** | `.cursor/skills` | `~/.cursor/skills` |
| **Gemini CLI** | `.gemini/skills` | `~/.gemini/skills` |
| **GitHub Copilot** | `.github/skills` | `~/.copilot/skills` |
| **Generic Agent Skills** | `.agents/skills` | `~/.agents/skills` |
| **Qoder CLI / IDE** | `.qoder/skills` | `~/.qoder/skills` |
| **OpenCode** | `.opencode/skills` | `~/.config/opencode/skills` |
| **Google Antigravity** | `.agents/skills` | `~/.gemini/config/skills` |
| **Amp CLI** | `.agents/skills` | `~/.config/agents/skills` |
| **Zed Agent** | `.agents/skills` | `~/.agents/skills` |
| **Pi Coding Agent** | `.pi/skills` | `~/.pi/agent/skills` |
| **OpenClaw** | `.agents/skills` | `~/.agents/skills` |
| **Autohand Code CLI** | `.autohand/skills` | `~/.autohand/skills` |
| **Warp Agent** | `.warp/skills` | `~/.warp/skills` |
| **Kilo Code** | `.kilo/skills` | `~/.kilo/skills` |
| **Cline** | `.cline/skills` | `~/.cline/skills` |
| **Roo Code** | `.roo/skills` | `~/.roo/skills` |
| **TRAE** | `.trae/skills` | `~/.trae/skills` |
| **Factory Droid** | `.factory/skills` | `~/.factory/skills` |

---

## Specialist Domains

The router matches incoming engineering tasks to specialized modules under `skills/rcoder/references/`:

- **Languages & Runtimes:** C, C++, Rust, Python, JavaScript/TypeScript, Node.js, C#/.NET, Java/JVM, Go, Swift, Kotlin, PHP, Ruby, Dart/Flutter, Scala, Elixir, Haskell, Lua, R/Julia.
- **Product & Architecture:** Fullstack frontend/SSR, backend APIs, distributed architectures, database engines, mobile ecosystems, embedded firmware, ML/AI systems.
- **Infrastructure & Platform:** Win32/Windows systems, Android/AOSP, Linux systems administration, Kubernetes, Cloud IaC, GPU computing.
- **Quality & Security:** Defensive threat modeling, secure code reviews, automated test planning, performance profiling, supply-chain verification.
- **Reverse Engineering:** Authorized binary analysis, protocol reverse engineering, firmware disassembly, ABI reconstruction, emulator design.

---

## Developer Guide & Verification

Run the comprehensive test and validation suite locally:

```sh
# Core static validation and regressions
python3 scripts/validate-all
python3 scripts/test-context-snapshot.py
python3 scripts/test-score-eval.py
python3 scripts/test-objective.py
python3 scripts/test-route-predict.py
python3 scripts/test-repo-map.py
python3 scripts/test-rsaver.py
python3 scripts/test-rscan.py

# Protocol and MCP integration tests
python3 scripts/test-mcp.py
python3 scripts/test-mcp-contract.py
python3 scripts/test-mcp-http.py
python3 scripts/test-mcp-modern.py
python3 scripts/test-mcp-setup.py

# CLI and host installation suites
node scripts/test-cli-doctor.mjs
node scripts/test-cli-skill.mjs
node scripts/test-integrations.mjs
node scripts/test-node-installer.mjs

# Packaging and artifact checks
python3 scripts/package
python3 scripts/check-dist.py
```

---

## Evaluation & Benchmarks

Evaluation methodology adheres to strict ablation standards ([evals/ABLATION-PROTOCOL.md](evals/ABLATION-PROTOCOL.md)). Controlled runs evaluate task completion, specialist routing precision, and trigger detection accuracy while isolating model temperature, seed, and environment fixtures. Refer to [evals/results.md](evals/results.md) and [docs/LIVE-BENCHMARK.md](docs/LIVE-BENCHMARK.md) for published findings and reproduction logs.

---

## License

This project is licensed under the [MIT License](LICENSE).

