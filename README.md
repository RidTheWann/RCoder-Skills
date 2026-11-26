# RCoder

**A model-agnostic engineering toolkit for AI coding agents.** RCoder helps agentic AI systems understand unfamiliar repositories, select the right engineering expertise, manage context, and execute software work with verifiable evidence. It combines a progressive-disclosure Agent Skill, specialist engineering references, deterministic project-analysis tools, context-management utilities, and an optional Model Context Protocol (MCP) server.

[![Quality CI](https://github.com/RidTheWann/RCoder-Skills/actions/workflows/quality.yml/badge.svg)](https://github.com/RidTheWann/RCoder-Skills/actions/workflows/quality.yml)
[![Security: A — Skills Directory](https://www.skillsdirectory.com/api/skills/ridthewann-rcoder/badge)](https://www.skillsdirectory.com/skills/ridthewann-rcoder)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Hosts](https://img.shields.io/badge/Agent%20hosts-20-informational.svg)](#supported-agent-hosts)
[![Platforms](https://img.shields.io/badge/OS-Windows%20%7C%20Linux%20%7C%20macOS-informational.svg)](#installation)

RCoder is designed to work across **agentic AI applications, coding CLIs, IDE integrations, and other Agent Skills-compatible environments**. It is an orchestration and workflow layer—not a model, autonomous runtime, permission system, or replacement for the tools provided by the host.

> **The goal:** help an AI coding agent do the right engineering work, with the right specialist guidance, using the tools it actually has, and prove what it changed and verified.

---

## Why RCoder?

Modern coding agents can edit code, run commands, inspect repositories, and delegate work—but their effectiveness depends on how they understand a codebase, select expertise, manage limited context, and verify results.

RCoder provides a consistent engineering workflow across supported hosts:

- **Model-agnostic instructions** — reusable guidance that does not depend on one model vendor or prompting format.
- **Progressive disclosure** — a compact entry point with specialist references loaded only when the task requires them.
- **Deterministic repository reconnaissance** — RScan produces bounded, read-only project inventories and prioritized development options.
- **Context budgeting and recovery** — RSaver helps measure, reduce, redact, anchor, and reconstruct context with evidence.
- **MCP integration** — expose supported RCoder capabilities as native tools to compatible agent hosts.
- **Specialist engineering library** — focused guidance for programming languages, architecture, systems, security, reverse engineering, testing, and more.
- **Agent integration utilities** — host-aware installation, diagnostics, skill authoring, packaging, and opt-in lifecycle hooks.

## Capabilities at a glance

| Component | Purpose |
|---|---|
| **RCoder Skill** | Classifies engineering tasks and routes the agent to relevant specialist references |
| **RScan** | Performs bounded, read-only project reconnaissance and produces a prioritized development menu |
| **RSaver** | Supports token/context budgeting, redaction, compression, recovery, anchoring, and drift checks |
| **MCP server** | Exposes supported RCoder functions through the Model Context Protocol |
| **Launcher CLI** | Installs and updates RCoder, configures integrations, runs diagnostics, and manages skills/hooks |
| **Skill toolkit** | Scaffolds, lints, and packages modular Agent Skills |
| **Specialist references** | Provides domain-specific engineering workflows and verification guidance |

---

## Installation

Choose the installation route that matches your environment. You do not need Node.js for the native Windows PowerShell installer or the POSIX skill installer.

### Windows PowerShell

Install RCoder into the current project and register the global `rcoder` launcher:

```powershell
irm https://raw.githubusercontent.com/RidTheWann/RCoder-Skills/main/install.ps1 | iex
```

Compatible with Windows PowerShell 5.1 and PowerShell 7+.

Install for a specific host and user scope:

```powershell
& ([scriptblock]::Create((irm 'https://raw.githubusercontent.com/RidTheWann/RCoder-Skills/main/install.ps1'))) -Target qoder -Scope user
```

To inspect or configure MCP integration, append `-Mcp show` or `-Mcp install`.

### Linux, macOS, WSL, and Termux (POSIX shell)

From a local clone of RCoder-Skills, use the repository-root entrypoint:

```sh
git clone https://github.com/RidTheWann/RCoder-Skills.git
cd RCoder-Skills
sh ./install.sh --target codex --scope project
```

For Claude Code or Gemini CLI, the short aliases are also accepted:

```sh
sh ./install.sh --host claude --scope user
sh ./install.sh --host gemini --scope project
```

The root `install.sh` is a stable thin entrypoint that delegates to the canonical `scripts/install.sh`. The POSIX skill installation does not require Node.js. Use `--dry-run` to preview, `--uninstall` to restore the previous skill, `--yes` for automation-compatible invocation, or `--mcp show|install` to inspect/apply MCP configuration. `--host all` is intentionally rejected because the installer targets one host per invocation; use `--target agents` for the generic Agent Skills location.

Run `sh ./install.sh --doctor` to run the CLI doctor. This diagnostic path requires Node.js 18.18 or newer; standard skill installation does not.

### Node.js / npm — Windows, Linux, macOS

Requires Node.js 18.18+, npm, and Git:

```sh
npx -y github:RidTheWann/RCoder-Skills
```

Examples for non-interactive installation:

```sh
# Codex, project scope
npx -y github:RidTheWann/RCoder-Skills --target codex --scope project

# Factory, user scope
npx -y github:RidTheWann/RCoder-Skills --target factory --scope user
```

Launcher locations:

- **Linux / macOS:** `~/.local/bin/rcoder`
- **Windows:** `%USERPROFILE%\\.rcoder\\bin\\rcoder.cmd`

### Verify the installation

After installation, open a new terminal so the updated user `PATH` is loaded by the new shell. Then verify the launcher:

```sh
rcoder doctor --json
```

`rcoder doctor --fix` repairs only canonical drift: repository-root wrappers, MCP launcher paths, and the SessionStart hook. It leaves unrelated host configuration untouched and reports each repair as `FIXED` or `SKIP`. `rcoder sync` normalizes portable MCP configs, state paths, POSIX executable modes, and host manifests; `doctor --fix` runs it automatically.

For host-specific integration options and MCP configuration, see [docs/MCP.md](docs/MCP.md) and the relevant integration documentation.

---

## A universal agent instruction for RCoder

The following prompt is intended for a repository's agent instructions, a coding-agent session, or a host-specific project prompt. It helps an AI agent discover and use RCoder consistently without assuming a particular model, vendor, CLI, IDE, or tool API.

Copy the prompt into the appropriate instruction surface supported by your environment (for example `AGENTS.md`, `CLAUDE.md`, project rules, custom instructions, or the initial agent task prompt).

<details>
<summary><strong>RCoder — agent operating prompt (expand)</strong></summary>

```text
You are an AI coding agent. Use RCoder to route and execute engineering work in the active model, CLI, IDE, or agent host.

- **Follow project rules:** obey user instructions and repository guidance; inspect the project before editing.
- **Discover RCoder:** prefer connected MCP tools within the server's configured `--root`; otherwise use installed helpers via absolute `<skill-dir>/scripts/...` paths with an explicit project root. Never assume tools or paths exist.
- **Route narrowly:** choose one primary specialist and load only necessary supporting references.
- **Finish the work:** implement the requested outcome, run relevant checks, and review the final diff. Do not stop at a plan when execution is authorized.
- **Report evidence:** summarize changes, checks and results, and remaining risks. Label claims `VERIFIED`, `INFERRED`, or `NOT VERIFIED`.

Adapt to actual host capabilities. Never invent tool access or test results, or bypass repository, permission, or security boundaries.
```

</details>

**For maintainers:** the repository's [AGENTS.md](AGENTS.md) provides a concise bootstrap for agents that discover repository-level instructions. The full workflow and specialist routing live in [skills/rcoder/SKILL.md](skills/rcoder/SKILL.md).

---

## Tooling

### RScan — project reconnaissance

RScan performs bounded, read-only inspection of a project:

```sh
python3 skills/rcoder/scripts/rscan.py scan --root . --format json
```

It can identify project structure, frameworks, runtimes, package manifests, tests, and repository risks, then produce a ranked development menu linked to relevant RCoder specialists.

### RSaver — context management

RSaver helps coding agents manage limited context and reduce avoidable context loss:

- **Audit and budget:** estimate context impact and prioritize what should remain available.
- **Redaction:** deterministically mask secrets and credentials before content is shared.
- **Pack and unpack:** compress repetitive material with verifiable SHA-256 reconstruction.
- **Anchor and drift checks:** preserve objectives, constraints, decisions, and unresolved questions.
- **Crosscheck:** compare completion claims with available change and test evidence.

See [docs/TOKEN-ECONOMICS.md](docs/TOKEN-ECONOMICS.md) and [skills/rcoder/references/rsaver.md](skills/rcoder/references/rsaver.md).

### MCP server

RCoder includes a zero-dependency stdio MCP server:

```sh
# Print a host configuration example
python3 skills/rcoder/scripts/rcoder_mcp.py --print-config claude-code

# Run with a bounded workspace root and profile
python3 skills/rcoder/scripts/rcoder_mcp.py --root . --profile minimal
```

The server is designed around workspace-root confinement and avoids subprocess shells and network sockets in its stdio implementation. An optional loopback Streamable HTTP transport is documented in [docs/MCP.md](docs/MCP.md).

MCP is optional. Use it when the active host supports MCP and the server's read-only tools are useful; see [docs/MCP.md](docs/MCP.md) for setup and boundaries.
