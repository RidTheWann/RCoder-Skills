# RCoder

**A model-agnostic engineering toolkit for AI coding agents.**

RCoder helps agentic AI systems understand unfamiliar repositories, select the right engineering expertise, manage context, and execute software work with verifiable evidence. It combines a progressive-disclosure Agent Skill, specialist engineering references, deterministic project-analysis tools, context-management utilities, and an optional Model Context Protocol (MCP) server.

[![Quality CI](https://github.com/RidTheWann/RCoder-Skills/actions/workflows/quality.yml/badge.svg)](https://github.com/RidTheWann/RCoder-Skills/actions/workflows/quality.yml)
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

Choose the installation route that matches your environment. You do not need Node.js for the native Windows PowerShell installer.

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
- **Windows:** `%USERPROFILE%\.rcoder\bin\rcoder.cmd`

### Verify the installation

```sh
rcoder doctor --json
```

For host-specific integration options and MCP configuration, see [docs/MCP.md](docs/MCP.md) and the relevant integration documentation.

---

## A universal agent instruction for RCoder

The following prompt is intended for a repository's agent instructions, a coding-agent session, or a host-specific project prompt. It helps an AI agent discover and use RCoder consistently without assuming a particular model, vendor, CLI, IDE, or tool API.

Copy the prompt into the appropriate instruction surface supported by your environment (for example `AGENTS.md`, `CLAUDE.md`, project rules, custom instructions, or the initial agent task prompt).

<details>
<summary><strong>RCoder — agent operating prompt (expand)</strong></summary>

```text
You are an AI coding agent. Use RCoder as your engineering workflow and specialist-routing layer. Adapt it to the model, host (CLI, IDE, or agent app), and tools actually available.

1. **Respect the project.** Follow user instructions and repository policies first. Inspect the repository state and applicable `AGENTS.md`, `CLAUDE.md`, and project guidance.
2. **Discover RCoder.** Prefer connected `mcp__rcoder__*` tools, keeping targets inside the server's configured `--root`. Otherwise, use installed RCoder helpers by absolute `<skill-dir>/scripts/...` path with an explicit project root. Never assume a tool or path exists; mark unavailable capabilities `NOT VERIFIED`.
3. **Route selectively.** Choose exactly one primary RCoder specialist and only the supporting references the task needs. Load guidance progressively.
4. **Deliver the task.** Inspect relevant code and tests, implement the requested change, and continue through verification when authorized. Do not stop at a plan when the work can be completed.
5. **Prove the result.** Run relevant checks and review the final diff. Report what changed, checks and outcomes, and remaining risks. Label evidence `VERIFIED`, `INFERRED`, or `NOT VERIFIED`.

Never invent tool access or test results, and never bypass repository, permission, or security boundaries.
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

MCP is optional. Use it when the active host supports MCP and the server has been configured; otherwise use the installed skill and supported CLI/helper workflows.

### Launcher CLI

Run the interactive management interface:

```sh
rcoder
```

Common commands:

```sh
# Integrations
rcoder integration install opencode --scope project
rcoder integration install codex
rcoder integration verify opencode --scope project

# Diagnostics
rcoder doctor --json

# Agent Skill lifecycle
rcoder skill new custom-domain --description "Guidance for custom domain workflows."
rcoder skill lint ./custom-domain
rcoder skill package ./custom-domain --out ./dist/custom-domain.zip

# Optional lifecycle hooks
rcoder hooks install --scope project --dry-run
rcoder hooks install --scope user --profile strict
rcoder hooks uninstall --scope project
rcoder hooks print-config
```

Hooks are opt-in. Review the relevant documentation and generated configuration before applying them.

---

## Supported agent hosts

RCoder's installer maps supported hosts to their canonical project and user skill roots.

| Agent / environment | Project skill root | User skill root |
|---|---|---|
| Claude Code | `.claude/skills` | `~/.claude/skills` |
| OpenAI Codex CLI | `.agents/skills` | `~/.agents/skills` |
| Cursor | `.cursor/skills` | `~/.cursor/skills` |
| Gemini CLI | `.gemini/skills` | `~/.gemini/skills` |
| GitHub Copilot | `.github/skills` | `~/.copilot/skills` |
| Generic Agent Skills | `.agents/skills` | `~/.agents/skills` |
| Qoder CLI / IDE | `.qoder/skills` | `~/.qoder/skills` |
| OpenCode | `.opencode/skills` | `~/.config/opencode/skills` |
| Google Antigravity | `.agents/skills` | `~/.gemini/config/skills` |
| Amp CLI | `.agents/skills` | `~/.config/agents/skills` |
| Zed Agent | `.agents/skills` | `~/.agents/skills` |
| Pi Coding Agent | `.pi/skills` | `~/.pi/agent/skills` |
| OpenClaw | `.agents/skills` | `~/.agents/skills` |
| Autohand Code CLI | `.autohand/skills` | `~/.autohand/skills` |
| Warp Agent | `.warp/skills` | `~/.warp/skills` |
| Kilo Code | `.kilo/skills` | `~/.kilo/skills` |
| Cline | `.cline/skills` | `~/.cline/skills` |
| Roo Code | `.roo/skills` | `~/.roo/skills` |
| TRAE | `.trae/skills` | `~/.trae/skills` |
| Factory Droid | `.factory/skills` | `~/.factory/skills` |

The table describes installation targets, not a guarantee that every host exposes identical MCP, hook, subagent, or CLI capabilities. Those features depend on the active host and its configuration.

---

## Specialist engineering library

RCoder uses focused references under `skills/rcoder/references/`. Select only the modules relevant to the current deliverable.

| Domain | Coverage |
|---|---|
| **Core engineering** | Coding, architecture, debugging, testing, QA, review, documentation, performance, DevOps, observability, API and database engineering |
| **Languages and runtimes** | C/C++, Rust, Python, JavaScript/TypeScript, Node.js, C#/.NET, Java, Go, Swift, Kotlin, PHP, Ruby, Dart/Flutter, Scala, Elixir, Haskell, R, Julia |
| **Platforms and systems** | Windows, Linux, Android/AOSP, mobile, embedded systems, firmware, graphics, GPU, game engines, distributed systems |
| **Security** | Threat modeling, secure code review, application security, authorized penetration testing, cloud/container, network, identity, cryptography, supply-chain, incident response, forensics, malware analysis, LLM/agent security |
| **Reverse engineering** | Binary analysis, disassembly/decompilation, file formats, protocol analysis, firmware research, ABI and semantic reconstruction |

Security and reverse-engineering workflows emphasize authorization, preservation of evidence, and clear separation of observed facts from hypotheses.

---

## Developer guide and verification

Run the relevant focused checks during development. The repository's full validation entry point is:

```sh
python3 scripts/validate-all
```

Additional test suites include:

```sh
# Python test suites
python3 scripts/test-context-snapshot.py
python3 scripts/test-score-eval.py
python3 scripts/test-objective.py
python3 scripts/test-route-predict.py
python3 scripts/test-repo-map.py
python3 scripts/test-rsaver.py
python3 scripts/test-rscan.py
python3 scripts/test-mcp.py
python3 scripts/test-mcp-contract.py
python3 scripts/test-mcp-http.py
python3 scripts/test-mcp-modern.py
python3 scripts/test-mcp-setup.py

# CLI and host integration suites
node scripts/test-cli-doctor.mjs
node scripts/test-cli-skill.mjs
node scripts/test-integrations.mjs
node scripts/test-node-installer.mjs

# Distribution checks
python3 scripts/package
python3 scripts/check-dist.py
```

For evaluation methodology and reproducibility, see [evals/ABLATION-PROTOCOL.md](evals/ABLATION-PROTOCOL.md), [evals/results.md](evals/results.md), and [docs/LIVE-BENCHMARK.md](docs/LIVE-BENCHMARK.md).

---

## Documentation

- [Agent Skill entry point](skills/rcoder/SKILL.md)
- [MCP setup and transports](docs/MCP.md)
- [Compatibility matrix](docs/COMPATIBILITY.md)
- [Environment discovery](docs/ENVIRONMENT.md)
- [RScan hooks](docs/RSCAN-HOOKS.md)
- [Token economics](docs/TOKEN-ECONOMICS.md)
- [Changelog](CHANGELOG.md)
- [Contributing](CONTRIBUTING.md)
- [Security policy](SECURITY.md)

## License

RCoder is released under the [MIT License](LICENSE).
