# RCoder

**A model-agnostic engineering workflow for AI coding agents.**

RCoder helps an AI coding agent move from an unfamiliar codebase to a scoped implementation, relevant specialist guidance, verification, and an evidence-backed handoff. It brings repository reconnaissance, 60+ specialist references, context-management tools, MCP integration, and cross-host Agent Skills packaging into one workflow.

[![Quality CI](https://github.com/RidTheWann/RCoder-Skills/actions/workflows/quality.yml/badge.svg)](https://github.com/RidTheWann/RCoder-Skills/actions/workflows/quality.yml)
[![Security: A — Skills Directory](https://www.skillsdirectory.com/api/skills/ridthewann-rcoder/badge)](https://www.skillsdirectory.com/skills/ridthewann-rcoder)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Agent hosts](https://img.shields.io/badge/Agent%20hosts-20-informational.svg)](#supported-agent-hosts)
[![Platforms](https://img.shields.io/badge/OS-Windows%20%7C%20Linux%20%7C%20macOS-informational.svg)](#installation)

RCoder Skills is an **instruction and tooling layer**, not an AI model or a standalone autonomous agent. The optional **RCoder Runtime** is a separate local control-plane companion that follows the lifetime of a local RCoder MCP process. The connected agent still performs the work using the tools and permissions provided by its host.

---

## Start here

- **Want to install it?** Go to [Installation](#installation).
- **Want to understand the workflow?** Read [How RCoder works](#how-rcoder-works).
- **Want proof of the difference?** See the [Before-and-after evaluation](#before-and-after-evidence).
- **Want to see a complex task?** Jump to the [API migration walkthrough](#recorded-complex-task-api-migration).

### Contents

- [Why RCoder](#why-rcoder)
- [How RCoder works](#how-rcoder-works)
- [Before-and-after evidence](#before-and-after-evidence)
- [Recorded complex task: API migration](#recorded-complex-task-api-migration)
- [Installation](#installation)
- [Use RCoder with your agent](#use-rcoder-with-your-agent)
- [Core components](#core-components)
- [RCoder Runtime](#rcoder-runtime-optional-local-control-plane)
- [Supported agent hosts](#supported-agent-hosts)
- [Specialist library](#specialist-library)
- [Security and execution boundaries](#security-and-execution-boundaries)
- [Development and verification](#development-and-verification)
- [Documentation](#documentation)

---

## Why RCoder?

A coding agent can produce code quickly and still make the wrong change: it may misunderstand the repository, load irrelevant files, choose the wrong specialist, miss a compatibility constraint, or declare success without running a check.

RCoder addresses those failure points with a repeatable engineering loop:

| Common problem | How RCoder helps |
|---|---|
| The repository is unfamiliar or large | **RScan** builds a bounded, read-only map of project structure, detected stacks, risks, and likely next steps. |
| The task crosses multiple engineering domains | The **specialist router** selects one primary reference and only the supporting expertise the task needs. |
| The task is too broad to execute safely | The workflow requires acceptance criteria, a scoped plan, reversible changes, and a verification map. |
| Context is becoming expensive or unreliable | **RSaver** measures, budgets, redacts, compresses, anchors, and recovers context with integrity checks. |
| A completion claim needs evidence | Verification tools compare claims with diffs, test artifacts, and observed results. |
| Different hosts expose different capabilities | The Agent Skill, CLI, MCP server, plugins, and installers provide host-aware integration paths. |

The objective is not simply to generate more code. It is to make engineering work more **focused, reviewable, reproducible, and honest about what has and has not been verified**.

## How RCoder works

RCoder's execution kernel defines seven stages. The active AI agent carries them out using the capabilities available in its host.

```text
User request
    |
    v
1. INTAKE       Deliverable, acceptance criteria, constraints, authorization
    |
    v
2. RECON        Repository map, stack, tests, Git state, risk signals
    |
    v
3. ROUTE        One primary specialist + only distinct supporting references
    |
    v
4. PLAN         Ordered steps, acceptance criteria, risks, verification map
    |
    v
5. EXECUTE      Small, reversible changes using authorized host tools
    |
    v
6. VERIFY       Focused tests, lint/build checks, diff and claim cross-check
    |
    v
7. CHECKPOINT   Changes, evidence, unknowns, risks, and next action
```

### What this means in practice

1. **Understand the request first.** The agent identifies what must change, what must not change, the acceptance criteria, repository rules, and any authorization boundary.
2. **Inspect before editing.** RScan and bounded file reads reveal the project structure and the smallest relevant surface. RScan itself is read-only.
3. **Load expertise on demand.** The agent chooses one primary specialist and loads only the necessary supporting references, rather than flooding context with the entire library.
4. **Plan risky work.** Multi-file, architectural, security-sensitive, and deployment changes get explicit steps, acceptance criteria, risks, and checks.
5. **Do the implementation.** When execution is authorized, the agent continues beyond the plan and uses the host's real editing and terminal tools. RCoder does not invent unavailable tools.
6. **Verify the result.** The agent runs proportionate checks, inspects the actual diff, and labels evidence as `VERIFIED`, `INFERRED`, or `NOT VERIFIED`.
7. **Leave a usable handoff.** A context capsule records the current objective, constraints, changed files, verification, unresolved risks, and next action.

**Autonomy has a boundary:** RCoder encourages the agent to carry an authorized task through implementation and verification, but it does not grant permissions, bypass host approvals, or turn an unavailable tool into an available one. The `/plan` command is intentionally plan-only; a normal implementation request should ask the agent to carry out the work.

---

## Before-and-after evidence

RCoder maintains a reproducible evaluation protocol that runs the same prompts and fixtures **with and without the skill**. The comparison below comes from the completed live run on **2026-11-19**.

<details open>
<summary><strong>Live ablation: WITHOUT RCoder vs WITH RCoder</strong></summary>

| Metric | WITHOUT RCoder | WITH RCoder | Difference |
|---|---:|---:|---:|
| Trigger precision | 0.000 | 0.952 | +0.952 |
| Trigger recall | 0.000 | 0.833 | +0.833 |
| Trigger F1 | 0.000 | 0.889 | +0.889 |
| Trigger accuracy | 0.429 | 0.881 | +0.452 |
| Behavioral scenarios passed | 4 / 19 | 6 / 19 | +2 scenarios |
| Scenario rubric pass rate | 0.500 | 0.592 | +0.092 |

**Test scope:** 42 trigger prompts and 19 behavioral scenarios, each run in both arms with the model, host, prompts, tools, permissions, fixture, and rubric held constant. The completed run used OpenCode CLI 1.19.6 and `openrouter/tencent/hy4-flash`; the WITH arm used RCoder v1.11.0.

**Important limitations:**

- These figures describe one pinned model, host, skill version, and dataset. They are not a guarantee for every model or supported host, and they are not a measurement of the current v1.16.0 release.
- The scenario rubric was scored by the same pinned model over bounded transcript summaries. Same-model judging bias is disclosed in the retained report.
- Specialist selection remained a weakness: exact-match was **4 of 24 scored prompts (16.7%)** in this run. Activating RCoder does not guarantee that every specialist choice is correct.
- The results show a measured change in this experiment, not universal model improvement or statistical significance.

</details>

**Inspect the source evidence:** [Run summary](evals/runs/hy4-flash-openrouter-2026-11-19/SUMMARY.md) · [Scorer output](evals/runs/hy4-flash-openrouter-2026-11-19/score-final.json) · [Per-case evidence](evals/runs/hy4-flash-openrouter-2026-11-19/evidence.json) · [Evaluation protocol](docs/LIVE-BENCHMARK.md).

## Recorded complex task: API migration

This example is based on the retained live-evaluation case **`s10-api-migration`**. The task was:

> Add a required API field backed by a database column while older app versions remain deployed.

This is a compatibility problem, not just a schema edit. Old and new clients may coexist during deployment, so the change must consider producers, consumers, database state, migration order, partial failure, and rollback.

### What RCoder recorded

| Evidence | Recorded result |
|---|---|
| RCoder skill invoked and `SKILL.md` read | Yes |
| Specialist references selected | `api-protocol-engineering`, `data-api`, `database-engineering`, `test-engineering`, `testing-qa` |
| Tool calls | 19 |
| Tool errors | 3 |
| Scenario rubric | **4 / 4 criteria passed** |
| Scenario verdict | **PASS** |

### How the workflow addresses the task

| Stage | Engineering work required by the scenario |
|---|---|
| **Intake** | Define the new field, its validation and default behavior, the database invariant, and the old application versions that must keep working. |
| **Recon and route** | Inspect API contracts, database migrations, producers, consumers, and existing compatibility tests. The recorded run selected the five specialist references listed above. |
| **Plan** | Map old/new producer-consumer combinations. Use a staged expand → migrate/backfill → contract approach (or an equivalent safe sequence), with explicit idempotency, partial-failure, and rollback behavior. |
| **Execute** | The host agent applies the smallest compatible API and database changes, plus the required migration and regression tests, using its authorized tools. |
| **Verify** | Check compatibility for old and new versions, invalid values, migration behavior, and rollback assumptions. The retained scenario scorer marked all four rubric criteria as met. |

<details>
<summary><strong>What the 4/4 score means</strong></summary>

The scenario's four rubric criteria were:

1. Identify consumers, invariants, and old/new versions.
2. Describe a staged expand/migrate/contract strategy.
3. Bound backfill, idempotency, partial failure, and rollback.
4. Cover compatibility and invalid values with contract and migration tests.

All four were marked as passed in the retained `score-final.json`.

**Evidence boundary:** the retained run stores structured per-case evidence and the rubric result, not a complete verbatim tool transcript for this scenario. The workflow table above explains how the RCoder execution contract maps to the evaluated task; it is not presented as a line-by-line transcript. Three tool errors were recorded, so the run should not be described as an error-free session.

</details>

This is one recorded task, not a claim that RCoder can solve every migration without human review. See [the original scenario definition](evals/scenarios.json) and [the case evidence](evals/runs/hy4-flash-openrouter-2026-11-19/evidence.json).

---

## Installation

Choose the method for your environment. The native Windows PowerShell and POSIX installers do not require Node.js for a standard Agent Skill installation.

### Windows PowerShell

Install into the current project and register the `rcoder` launcher:

```powershell
irm https://raw.githubusercontent.com/RidTheWann/RCoder-Skills/main/install.ps1 | iex
```

Compatible with Windows PowerShell 5.1 and PowerShell 7+.

To install for a specific host and user scope:

```powershell
& ([scriptblock]::Create((irm 'https://raw.githubusercontent.com/RidTheWann/RCoder-Skills/main/install.ps1'))) -Target qoder -Scope user
```

Add `-Mcp show` to inspect MCP setup or `-Mcp install` to apply it.

### Linux, macOS, WSL, and Termux

Clone the repository and run the POSIX installer:

```sh
git clone https://github.com/RidTheWann/RCoder-Skills.git
cd RCoder-Skills
sh ./install.sh --target codex --scope project
```

Other examples:

```sh
sh ./install.sh --host claude --scope user
sh ./install.sh --host gemini --scope project
```

Use `--dry-run` to preview, `--yes` for non-interactive installation, `--uninstall` to restore the previous skill, or `--mcp show|install` to inspect or apply MCP configuration. Use `--target agents` for the generic Agent Skills location. The installer targets one host per invocation; `--host all` is intentionally rejected.

The root `install.sh` delegates to `scripts/install.sh`. Standard POSIX skill installation does not require Node.js. The optional `--doctor` path requires Node.js 18.18 or newer.

### Node.js / npm

Requires Node.js 18.18+, npm, and Git:

```sh
npx -y github:RidTheWann/RCoder-Skills
```

Non-interactive examples:

```sh
# Codex, project scope
npx -y github:RidTheWann/RCoder-Skills --target codex --scope project

# Factory Droid, user scope
npx -y github:RidTheWann/RCoder-Skills --target factory --scope user
```

Launcher locations:

- Linux / macOS: `~/.local/bin/rcoder`
- Windows: `%USERPROFILE%\\.rcoder\\bin\\rcoder.cmd`

### Verify the installation

Open a new terminal so the updated user `PATH` is loaded, then run:

```sh
rcoder doctor --json
```

For a safe repair of canonical launcher and integration drift, use `rcoder doctor --fix`. It reports each repair as `FIXED` or `SKIP` and leaves unrelated host configuration untouched.

For host-specific setup and MCP configuration, see [docs/MCP.md](docs/MCP.md).

---

## Use RCoder with your agent

After installing RCoder in a host that supports Agent Skills, start a task in the agent's normal chat or coding interface. The host discovers and loads the skill according to its own configuration.

For example, give the agent a concrete task:

```text
The API migration is breaking older clients. Investigate the repository,
identify the compatibility constraint, implement a safe migration, add
regression tests, run the relevant checks, review the diff, and report
what is VERIFIED, INFERRED, and NOT VERIFIED.

Use RCoder. Do not stop after planning if implementation is authorized.
```

You can also copy the following host-neutral instruction into a repository instruction file or project prompt (for example `AGENTS.md`, `CLAUDE.md`, or equivalent):

<details>
<summary><strong>RCoder agent operating prompt</strong></summary>

```text
You are an AI coding agent. Use RCoder to route and execute engineering work
in the active model, CLI, IDE, or agent host.

- Follow user instructions and repository rules. Inspect before editing.
- Discover actual tools and capabilities; do not assume they exist.
- Route narrowly: select one primary specialist and only distinct supporting
  references relevant to the deliverable.
- Define acceptance criteria and a bounded plan for multi-file or risky work.
- When implementation is authorized, execute the task instead of stopping
  after a plan.
- Run proportionate checks and inspect the actual final diff.
- Report changes, exact checks and results, residual risks, and unknowns.
- Label material claims VERIFIED, INFERRED, or NOT VERIFIED.
- Never invent tool access or test results, bypass authorization, or weaken
  repository security boundaries.
```

</details>

**Note:** the `/plan` command intentionally produces a plan and stops. Use a normal implementation request when you want the agent to proceed with the change.

---

## Core components

| Component | What it does |
|---|---|
| **RCoder Skill** | The routing and execution kernel: intake, reconnaissance, specialist selection, planning, execution, verification, and checkpointing. |
| **RScan** | Bounded, read-only repository scanning. Detects stacks, manifests, project risks, and likely development entry points. |
| **RSaver** | Context measurement and management: budget, redaction, safe prose optimization, compaction, deduplication, packing, anchoring, drift detection, recovery, and cross-checking. |
| **RFC Context Fabric** | Opt-in, provenance-aware local context persistence with explicit per-request hydration, canary delivery checks, token-free transcript export, and deterministic retention. |
| **Specialist library** | More than 60 focused engineering references, loaded progressively instead of all at once. |
| **MCP server** | Exposes supported RCoder and RSaver operations as native tools, resources, and prompts to compatible hosts. |
| **RCoder Runtime** | Optional Rust control-plane companion, automatically attached to the lifetime of a local RCoder MCP process when installed. Tracks project sessions without taking over host permissions. |
| **Launcher CLI** | Installs and updates RCoder, configures integrations, runs diagnostics, and manages skills and optional hooks. |
| **Skill toolkit** | Creates, lints, and packages portable Agent Skills. |
| **Subagents and commands** | Optional host-specific planner, explorer, reviewer, verifier, and workflow commands. |

### RScan — inspect before you edit

RScan is read-only. It scans project metadata and selected file names to detect stacks, manifests, tests, risk signals, and likely entry points. It skips common generated and dependency directories and can produce JSON for agent tooling.

Run the bundled scanner from a repository checkout:

```sh
python3 skills/rcoder/scripts/rscan.py scan --root . --format json
```

### RSaver — preserve useful context

RSaver helps an agent use context efficiently without treating a token estimate as an exact provider count.

- **Measure and budget:** estimate the relative context cost and reserve room for output and reasoning.
- **Optimize prose:** tighten a small allowlist of phrases while preserving code, structures, constraints, and evidence.
- **Redact:** mask credential-shaped values before sharing text.
- **Compact and deduplicate:** reduce repetitive output while preserving critical evidence.
- **Pack and unpack:** use lossless representations with SHA-256 verification.
- **Anchor and recover:** preserve objective, constraints, decisions, and omitted evidence across long tasks.
- **Cross-check:** compare completion claims with available diff, test, and usage artifacts.

See [the RSaver reference](skills/rcoder/references/rsaver.md) and [token economics](docs/TOKEN-ECONOMICS.md).

### RFC Context Fabric — explicit context across requests

RFC is the Context Fabric development track. It stores typed, source-aware context locally and assembles a bounded payload for each distinct model request. A coding agent must explicitly inject that payload into the request; a database or content hash alone does not create model memory.

The first slice includes SHA-256-addressed artifact storage, provenance and confidence fields, whole-item budget selection, session-plus-prompt canary validation, token-free transcript export, secret-pattern redaction, pinned context, and deterministic expiry collection. Its budget is measured in UTF-8 bytes, not provider tokens; use RSaver for token estimates and safe reduction.

The local Python API/CLI now has a native **Claude Code host adapter**: UserPromptSubmit builds and injects a fresh payload through the host's additionalContext channel, and Stop captures the final assistant response for canary verification and token-free RFC transcript storage. The adapter is opt-in: it remains inactive until .rcoder/context-fabric.sqlite3 exists, and it never blocks the host. Other host adapters, MCP write tools, encrypted storage, distributed synchronization, and vector retrieval are not implemented. See [RFC Context Fabric design and usage](docs/CONTEXT-FABRIC.md) and its [agent reference](skills/rcoder/references/context-fabric.md).

### RCoder Runtime — optional local control plane

RCoder Runtime is a separate Rust 2024 executable. When it is installed and a host starts the local Python RCoder MCP stdio server or loopback HTTP service, the MCP process automatically launches a detached Runtime companion. The companion tracks that exact server process and exits when it ends. The HTTP service uses one companion rather than spawning one per request. A project using only unrelated MCP servers (for example, Serena) does not activate RCoder Runtime.

Install and inspect it from the repository root:

```sh
cargo install --path runtime/apps/rcoder-runtime
rcoder-runtime detect --project .
rcoder-runtime status --project .

# Create a task contract with explicit acceptance criteria
rcoder-runtime task create --project . --objective "Implement a feature" \
  --acceptance "Focused tests pass" --acceptance "No unrelated files changed" --risk high --json
rcoder-runtime task transition --project . --id TASK_UUID --to active

# Compile the active task into a bounded context packet
rcoder-runtime task compile --project . --id TASK_UUID --json
```

Runtime is fail-open: if the executable is unavailable or startup fails, RCoder MCP continues normally. Set `RCODER_RUNTIME_DISABLE=1` to disable attachment, or `RCODER_RUNTIME_PATH` to use a non-PATH executable. The headless Runtime also provides typed execution contracts, reasoned reopening, acceptance-evidence gates, and a deterministic SHA-256-digested instruction packet for active tasks. The packaged Claude Code hook injects the unique active task packet on each eligible UserPromptSubmit; other hosts need a dedicated adapter. Host tool permission enforcement, instruction injection, RFC/RSaver integration, independent evidence verification, and the desktop console remain future stages. See [Runtime architecture and boundaries](docs/RUNTIME.md).

### MCP server — optional native tools

RCoder includes a standard-library stdio MCP server:

```sh
# Print a host configuration example without changing settings
python3 skills/rcoder/scripts/rcoder_mcp.py --print-config claude-code

# Start the server with a bounded workspace root
python3 skills/rcoder/scripts/rcoder_mcp.py --root . --profile minimal
```

Use MCP only when the active host supports it and the server has been configured. The process-level `--root` is the security boundary; a tool argument cannot widen it. An optional loopback Streamable HTTP transport is documented in [docs/MCP.md](docs/MCP.md).

### Launcher CLI and optional hooks

Run the interactive manager:

```sh
rcoder
```

Common commands:

```sh
# Integrations
rcoder integration install opencode --scope project
rcoder integration install codex
rcoder integration verify opencode --scope project

# Diagnostics and parity
rcoder doctor --json
rcoder doctor --fix
rcoder sync
python3 scripts/verify_parity.py
python3 scripts/check-dist.py

# Agent Skill lifecycle
rcoder skill new custom-domain --description "Guidance for custom domain workflows."
rcoder skill lint ./custom-domain
rcoder skill package ./custom-domain --out ./dist/custom-domain.zip

# Optional hooks
rcoder hooks install --scope project --dry-run
rcoder hooks install --scope user --profile strict
rcoder hooks uninstall --scope project
rcoder hooks print-config
```

Claude Code and Gemini CLI use different hook settings and event schemas. Hook installation is an explicit action; hooks run with the host user's privileges. Review [docs/HOOKS.md](docs/HOOKS.md) before enabling them.

---

## Supported agent hosts

RCoder's installer maps one canonical skill folder to the project and user locations below.

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

**Compatibility is evidence-based.** An installer writing to a documented directory does not prove that every host discovers, invokes, or behaves identically with RCoder. See [docs/COMPATIBILITY.md](docs/COMPATIBILITY.md) for the discovery, invocation, and behavioral evidence tiers. OpenCode 1.19.6 has specific historical native-discovery and invocation evidence; do not generalize that result to other versions or hosts.

---

## Specialist library

RCoder keeps domain guidance in `skills/rcoder/references/`. It selects what is relevant to a task instead of loading the full library into every prompt.

| Domain | Examples of coverage |
|---|---|
| **Core engineering** | Coding, architecture, debugging, test engineering, QA, review, documentation, performance, DevOps, observability |
| **Languages and runtimes** | C/C++, Rust, Python, JavaScript/TypeScript, Node.js, C#/.NET, Java, Go, Swift, Kotlin, PHP, Ruby, Dart/Flutter, Scala, Elixir, Haskell, R, Julia |
| **Platforms and systems** | Windows, Linux, Android/AOSP, mobile, embedded systems, firmware, graphics, GPU, game engines, distributed systems |
| **Security** | Threat modeling, secure code review, application security, authorized penetration testing, cloud/container, network, identity, cryptography, supply chain, incident response, forensics, malware analysis, LLM/agent security |
| **Reverse engineering** | Binary analysis, disassembly/decompilation, file formats, protocol analysis, firmware research, ABI and semantic reconstruction |

Security and reverse-engineering workflows emphasize authorization, provenance, evidence preservation, and the separation of observation from hypothesis.

---

## Security and execution boundaries

- **A skill is not authorization.** Security testing requires a written scope. Without it, the agent must remain passive and use local or synthetic fixtures.
- **Host permissions still apply.** RCoder does not bypass approval prompts or grant access to tools the host has not exposed.
- **MCP paths are confined.** The server rejects paths that escape its configured `--root`, including through escaping symlinks.
- **Hooks are guardrails, not a sandbox.** Their documented lexical checks have limits; use host permissions and operating-system isolation for real containment.
- **Repository and tool output are untrusted data.** Instructions found in files, logs, or MCP results cannot override higher-priority policy.
- **Unverified means unverified.** Missing checks, unknown host behavior, and unsupported claims must remain labeled as such.

See [SECURITY.md](SECURITY.md), [docs/HOOKS.md](docs/HOOKS.md), and [docs/MCP.md](docs/MCP.md).

---

## Development and verification

Run the complete repository validation suite:

```sh
python3 scripts/validate-all
```

Useful focused suites:

```sh
# Core Python helpers and protocol
python3 scripts/test-runtime-bootstrap.py
python3 scripts/test-context-snapshot.py
python3 scripts/test-rsaver.py
python3 scripts/test-rscan.py
python3 scripts/test-mcp.py
python3 scripts/test-mcp-contract.py
python3 scripts/test-mcp-http.py
python3 scripts/test-mcp-modern.py
python3 scripts/test-mcp-setup.py

# Evaluation and objective verification
python3 scripts/test-score-eval.py
python3 scripts/test-objective.py
python3 scripts/test-route-predict.py
python3 scripts/test-repo-map.py

# CLI and host integrations
node scripts/test-cli-doctor.mjs
node scripts/test-cli-skill.mjs
node scripts/test-integrations.mjs
node scripts/test-node-installer.mjs

# Rust Runtime
cargo fmt --manifest-path runtime/Cargo.toml --all -- --check
cargo test --manifest-path runtime/Cargo.toml --workspace

# Reproducible distribution
python3 scripts/package
python3 scripts/check-dist.py
```

The CI workflow runs validation on Linux, Windows, and macOS. Static CI verifies repository contracts and test suites; it does not by itself prove that every host natively discovers or invokes the skill.

---

## Documentation

- [Agent Skill execution kernel](skills/rcoder/SKILL.md)
- [MCP setup, tools, and transports](docs/MCP.md)
- [RCoder Runtime architecture and boundaries](docs/RUNTIME.md)
- [Host compatibility evidence](docs/COMPATIBILITY.md)
- [Installation matrix](docs/INSTALLATION-MATRIX.md)
- [Environment discovery](docs/ENVIRONMENT.md)
- [Lifecycle hooks](docs/HOOKS.md)
- [Token economics](docs/TOKEN-ECONOMICS.md)
- [Live benchmark protocol](docs/LIVE-BENCHMARK.md)
- [Evaluation results](evals/results.md)
- [Evaluation scenarios](evals/scenarios.json)
- [Changelog](CHANGELOG.md)
- [Contributing](CONTRIBUTING.md)
- [Security policy](SECURITY.md)

## License

RCoder is released under the [MIT License](LICENSE).
