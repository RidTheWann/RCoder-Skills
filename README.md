# RCoder

**A calmer way to use AI coding agents: less guessing, more evidence.**

RCoder is a small instruction and tooling layer you add to the agent you already use. It helps the agent look around the repository, pick the right guidance, do the work, and show what was actually checked. It does not replace your model, your editor, or your host's permission system.

You do not need a new model, a separate app, or a background service to start.

[![Quality CI](https://github.com/RidTheWann/RCoder-Skills/actions/workflows/quality.yml/badge.svg)](https://github.com/RidTheWann/RCoder-Skills/actions/workflows/quality.yml)
[![Security: A — Skills Directory](https://www.skillsdirectory.com/api/skills/ridthewann-rcoder/badge)](https://www.skillsdirectory.com/skills/ridthewann-rcoder)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Agent hosts](https://img.shields.io/badge/Agent%20hosts-20-informational.svg)](#supported-agent-hosts)
[![Platforms](https://img.shields.io/badge/OS-Windows%20%7C%20Linux%20%7C%20macOS%20%7C%20Termux-informational.svg)](#cross-platform-support)

---

## Which path should I take?

| I want to... | Start here |
|---|---|
| Install it and try it | [Quick start](#quick-start) |
| Understand what it does | [How RCoder works](#how-rcoder-works) |
| See proof that it helps | [Before and after](#before-and-after-evidence) |
| Know if my OS is supported | [Cross-platform support](#cross-platform-support) |
| Add Runtime or RFC | [Core components](#core-components) |
| Run the tests myself | [Development and verification](#development-and-verification) |

---

## Quick start

The whole setup is one install command and one check. Pick your shell.

**Windows (PowerShell)**

```powershell
irm https://raw.githubusercontent.com/RidTheWann/RCoder-Skills/main/install.ps1 | iex
```

**Linux, macOS, WSL, Termux**

```sh
git clone https://github.com/RidTheWann/RCoder-Skills.git
cd RCoder-Skills
sh ./install.sh --target agents --scope project
```

**Node.js / npm**

```sh
npx -y github:RidTheWann/RCoder-Skills
```

Open a new terminal, then confirm the launcher is available:

```sh
rcoder doctor --json
```

That is it. Your agent will find `skills/rcoder/SKILL.md` and follow it when the task is engineering work. Need another host or user scope? See [Installation](#installation).

> **No Rust required for normal use.** The Rust Runtime is optional and only needed for local task contracts and artifact-backed verification.

---

## Why RCoder?

A coding agent can write code quickly and still miss the point: wrong files, wrong specialist, forgotten constraints, or a "done" claim without a check.

RCoder adds a repeatable loop that is easy to inspect:

1. **Look first.** A bounded repository snapshot replaces guessing.
2. **Load only what matters.** Specialist guidance is disclosed progressively, not dumped into every prompt.
3. **Do the work with host tools.** RCoder never grants permissions or bypasses approvals.
4. **Verify against evidence.** Claims are separated from artifacts, digests, and observed results.
5. **Hand off cleanly.** A capsule records what was done, what is unknown, and what to do next.

The goal is not more code. It is work that is **focused, reviewable, reproducible, and honest about what has not been verified**.

---

## How RCoder works

```text
objective -> repository recon -> specialist choice -> implementation
          -> verification -> evidence-backed handoff
```

Four subsystems stay separate on purpose:

| Piece | Plain-language role |
|---|---|
| **RCoder** | The workflow and routing instructions. |
| **RSaver** | Measures and safely reduces context without rewriting source files. |
| **RFC Context Fabric** | Remembers typed context across requests with provenance and canaries. |
| **RCoder Runtime** | An optional local control plane for task contracts and verification. |

Host adapters (OpenCode, Claude Code, and others) only carry information into the real request. They are not a second task engine or a second database. See [Core components](#core-components) and [Supported agent hosts](#supported-agent-hosts).

---

## Before-and-after evidence

### Integration before and after

**The short version**

**Before:** we could show that the adapters existed and that unit tests passed. We could not show that a real editor actually sent our context to a model.

**Now:** we start the installed OpenCode app, point it at a local fake model, and read the exact request the app sends. The RFC memory and the Runtime task context arrive **in the same request**, with their provenance intact.

That is the difference between *"the code looks right"* and *"the host actually delivered it."*

| Question | Before | After | Why it matters |
|---|---|---|---|
| Does the plugin really load? | Checked by reading config and plugin files. | The real OpenCode process logs the plugin loading from the isolated workspace. | A file on disk is not the same as a loaded plugin. |
| Does context reach a model? | Adapter functions were called directly in tests. | The local mock provider captures the actual outgoing request body. | The host, not the test, is now the source of the request. |
| Do RFC and Runtime work together? | Tested separately. | Both markers appear in one request, with the RFC canary and Runtime digest. | Neither subsystem can fake the other's delivery. |
| Does one failure break everything? | Only configuration-level checks. | Four enable/disable combinations, missing context, retries, and a broken Runtime path were exercised. | Fail-open behavior is proven, not assumed. |
| Is my OS covered? | Fixture assumed POSIX paths and symlinks. | Portable resolvers with per-OS environment handling; Windows/macOS code paths unit-tested. | Lower friction on Windows and macOS, with honest limits. |

<details>
<summary><strong>Show the detailed evidence and commands</strong></summary>

All rows below are **VERIFIED locally** on aarch64 PRoot Debian 13 (trixie), OpenCode 2.4.2, Rust/Cargo 1.85.1, Python 3.13.5, Node 20.19.2. The provider was a loopback mock with a synthetic key; no public API or real credential was contacted.

| Capability | Before | After (observed) | Evidence tier |
|---|---|---|---|
| Native host request delivery | No host-generated request captured. | Installed OpenCode loaded the real plugin, connected RCoder MCP, and the mock provider captured `/v1/chat/completions`. | VERIFIED |
| RFC and Runtime in one request | Co-delivery unproven. | One system message contained `RFC_E2E_MARKER_<id>` with its `RFC-ACK` canary and `RUNTIME_E2E_MARKER_<id>`. | VERIFIED |
| Subsystem independence | Configuration-level unit tests only. | All four enable/disable configurations ran through the real host. | VERIFIED |
| Retry identity and missing context | Canary lifecycle covered offline. | Retries used distinct prompt identities; absent context produced no delivery claim. | VERIFIED |
| Runtime companion lifecycle | Offline session-state tests. | One companion per fixture reached `stopped`, bound to the fixture root, with no orphan process. | VERIFIED |
| Evidence verification | Caller attestations only. | Allowlisted parser, digest and mutation checks, cycle isolation, 58 passing Rust tests. | VERIFIED |
| Cross-platform fixture | Hardcoded `/tmp`, symlinks, XDG variables, literal command names. | Portable resolvers plus copy fallback; 13 parity tests pass and native E2E still passes on Linux. | VERIFIED on POSIX; NOT VERIFIED on Windows/macOS |

Reproduce locally:

```sh
python3 scripts/test-cross-platform.py
python3 scripts/test-opencode-native-e2e.py
cargo test --manifest-path runtime/Cargo.toml --workspace
```

**What this still does not prove:** hosted-model behavior, other OpenCode builds, native activation on Windows/macOS/Termux-native builds, or GitHub Actions results. Read [details](docs/OPENCODE-V2-ADAPTER.md) and [decision D-032](docs/DECISIONS.md).

</details>

### Model behavior, separately

The model-quality comparison is a different experiment and is **not** upgraded by the integration work above:

<details>
<summary><strong>Live ablation: WITHOUT RCoder vs WITH RCoder</strong></summary>

| Metric | WITHOUT RCoder | WITH RCoder | Difference |
|---|---:|---:|---:|
| Trigger precision | 0.000 | 0.952 | +0.952 |
| Trigger recall | 0.000 | 0.833 | +0.833 |
| Trigger F1 | 0.000 | 0.889 | +0.889 |
| Trigger accuracy | 0.429 | 0.881 | +0.452 |
| Behavioral scenarios passed | 4 / 19 | 6 / 19 | +2 scenarios |
| Scenario rubric pass rate | 0.500 | 0.592 | +0.092 |

Scope: 42 trigger prompts and 19 behavioral scenarios, both arms, with model, host, prompts, tools, permissions, fixture, and rubric held constant. Completed on OpenCode CLI 1.19.6 with `openrouter/tencent/hy4-flash`; the WITH arm used RCoder v1.11.0.

**Important:** this is one pinned model, host, skill version, and dataset. It is not a guarantee for every model or host, is not a measurement of the current v1.16.0 release, and the same model scored the rubric. Specialist exact-match was 4/24 (16.7%) in this run. See [run summary](evals/runs/hy4-flash-openrouter-2026-11-19/SUMMARY.md), [scorer output](evals/runs/hy4-flash-openrouter-2026-11-19/score-final.json), [per-case evidence](evals/runs/hy4-flash-openrouter-2026-11-19/evidence.json), and the [protocol](docs/LIVE-BENCHMARK.md).

</details>

---

## Common questions

**Do I need Rust?** No. The Rust Runtime is optional. Install the skill and your agent can follow the workflow without it.

**Do I need a paid model or API key?** No. The native E2E test uses a local fake provider and a synthetic key.

**Does RCoder take permissions away from my editor?** No. It never bypasses or replaces host approvals.

**Does "artifact_verified" mean the tests really ran?** It means a bounded artifact existed and matched an allowlisted, strictly parsed report. It does not prove a command ran or that a claim is true.

**Is Windows/macOS supported?** The portable code paths and unit tests exist, but native host activation on those OSes is NOT VERIFIED here. See [Cross-platform support](#cross-platform-support).

**Why does `cargo fmt` fail on my Termux image?** Some images ship a rustup proxy without a default toolchain. Use `rustfmt --edition 2024 --check <sources>`; the source contract is unchanged.

---

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

## Cross-platform support

RCoder keeps one canonical skill and one portable toolchain; OS differences are handled by thin resolvers rather than separate products. The shared helpers live in `skills/rcoder/scripts/platform_runtime.py`.

| Concern | POSIX (Linux, macOS, WSL, Termux) | Windows |
|---|---|---|
| Python discovery | `python3`, then `python`, with a real-interpreter health check | Health check plus `py -3` fallback; Microsoft Store stub rejected |
| Node discovery | `shutil.which("node")` | `node.exe` via `PATHEXT` |
| Host executable | Resolved absolute path | Resolved absolute path; `.cmd`/`.bat` launchers wrapped with `cmd.exe /c` |
| Isolated host config | `XDG_CONFIG_HOME`, `XDG_DATA_HOME`, `XDG_STATE_HOME`, `HOME`, `PWD` | `APPDATA`, `LOCALAPPDATA`, `USERPROFILE`, `HOME`, `TEMP`, `TMP` |
| Fixture workspace | Uses `TMPDIR` via `tempfile.gettempdir()` | Uses `TEMP`/`TMP` via `tempfile.gettempdir()` |
| Fixture file links | Symlinks preferred | Symlink attempted, then bounded copy fallback |
| Credential isolation | Provider keys and ambient OpenCode session variables removed before host start | Same sanitization |

**What is verified:** the portable resolvers and per-OS environment behavior have deterministic unit coverage in `scripts/test-cross-platform.py` (13 tests pass locally), and the native OpenCode E2E suite still passes on the POSIX host used for development.

**What is not verified:** native OpenCode execution and host discovery on Windows, macOS, and Termux-native builds were not run in this environment. Installer simulations are covered by separate suites, but an OS-specific pass here does not prove host activation there. See [docs/COMPATIBILITY.md](docs/COMPATIBILITY.md) and [docs/INSTALLATION-MATRIX.md](docs/INSTALLATION-MATRIX.md) for the retained platform records.

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

Native host adapters exist for **Claude Code** (UserPromptSubmit injects a fresh payload through `additionalContext`; Stop captures the final assistant response for canary verification and token-free transcript storage) and for **OpenCode 2.4.2** (the V2 plugin hydrates each model request and captures assistant text per step). Both are opt-in and fail open: the Claude adapter activates only when `.rcoder/context-fabric.sqlite3` exists, and the OpenCode bridge leaves host permissions untouched. Native OpenCode delivery was verified with a local mock provider; see [integration evidence](#integration-before-and-after). MCP write tools, encrypted storage, distributed synchronization, vector retrieval, and adapters for Codex/Gemini are not implemented. See [RFC Context Fabric design and usage](docs/CONTEXT-FABRIC.md) and its [agent reference](skills/rcoder/references/context-fabric.md).

### RCoder Runtime (optional local control plane)

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

Runtime is fail-open: if the executable is unavailable or startup fails, RCoder MCP continues normally. Set `RCODER_RUNTIME_DISABLE=1` to disable attachment, or `RCODER_RUNTIME_PATH` to use a non-PATH executable. The headless Runtime also provides typed execution contracts, reasoned reopening with fresh evidence cycles, audit-preserved historical evidence, acceptance-evidence gates, and a deterministic SHA-256-digested instruction packet for active tasks. The packaged Claude Code hook injects the unique active task packet on eligible UserPromptSubmit events; the OpenCode 2.4.2 V2 adapter compiles the same packet into real model requests, with native delivery verified against a local mock provider. Other hosts still need a dedicated adapter. `rcoder-runtime task verify` now performs bounded artifact-backed verification with an allowlisted report parser, digest and mutation checks, and current-cycle attribution — but it still cannot prove that a claimed command actually ran. Host tool permission enforcement, a Codex adapter, a fuller RFC/RSaver bridge, general verification of executed checks, and the desktop console remain future stages. See [Runtime architecture and boundaries](docs/RUNTIME.md).

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
python3 scripts/test-opencode-host.py
node scripts/test-opencode-v2-plugin.mjs
node scripts/test-opencode-plugin-host-state.mjs

# Cross-platform contracts and native host delivery
python3 scripts/test-cross-platform.py
python3 scripts/test-opencode-native-e2e.py

# Rust Runtime
cargo fmt --manifest-path runtime/Cargo.toml --all -- --check
cargo test --manifest-path runtime/Cargo.toml --workspace

# Reproducible distribution
python3 scripts/package
python3 scripts/check-dist.py
```

The CI workflow runs validation on Linux, Windows, and macOS. Static CI verifies repository contracts and test suites; it does not by itself prove that every host natively discovers or invokes the skill. On development images where the `cargo fmt` proxy cannot select a rustup toolchain, `rustfmt --edition 2024 --check <runtime sources>` is the equivalent direct formatting check; the source contract is unchanged.

Evidence tiers, the native request-capture method, and the explicit list of unverified hosts are recorded in [Integration before and after](#integration-before-and-after) and [docs/OPENCODE-V2-ADAPTER.md](docs/OPENCODE-V2-ADAPTER.md).

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
