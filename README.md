<div align="center">

# RCoder

### A workflow layer for AI coding agents — reconnaissance, focus, memory, and proof.

RCoder does not replace your model or your editor. It gives the agent you already use a repeatable engineering loop, so the result is easier to review, easier to continue, and honest about what was actually checked.

**One skill. Four subsystems. Twenty installation targets. No new model required.**

[![Quality CI](https://github.com/RidTheWann/RCoder-Skills/actions/workflows/quality.yml/badge.svg)](https://github.com/RidTheWann/RCoder-Skills/actions/workflows/quality.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Agent hosts](https://img.shields.io/badge/Agent%20hosts-20-informational.svg)](#supported-agent-hosts)
[![Platforms](https://img.shields.io/badge/OS-Windows%20%7C%20Linux%20%7C%20macOS%20%7C%20Termux-informational.svg)](#cross-platform-support)

**[Start in 5 minutes](#quick-start)** · **[See Before → After](#before-and-after-evidence)** · **[Explore the features](#feature-tour)** · **[Read the docs](#documentation)**

`Agent Skill` · `MCP` · `RFC` · `RSaver` · `Rust Runtime` · `OpenCode V2`

</div>

---

## What RCoder gives you

The capabilities are deliberately split. You can adopt one at a time.

| Capability | What it does for you | Go deeper |
|---|---|---|
| 🔍 **Bounded reconnaissance** | RScan maps stacks, entry points, manifests, and risks before any edit. | [RScan](#rscan--look-before-you-edit) |
| 🧭 **Progressive specialists** | 60+ focused references are selected by deliverable, not dumped into every prompt. | [Specialist library](#specialist-library) |
| 🧠 **Durable context** | RFC Context Fabric rehydrates source-linked decisions on each new request. | [RFC](#rfc-context-fabric--memory-with-provenance) |
| ✂️ **Safe context control** | RSaver measures, budgets, redacts, compacts, and can recover reduced context exactly. | [RSaver](#rsaver--context-intelligence) |
| ✅ **Evidence gates** | Runtime task contracts and artifact-backed verification separate claims from inspected outcomes. | [Runtime](#rcoder-runtime-optional-local-control-plane) |
| 🔌 **Native tooling** | A stdio/HTTP MCP server, CLI, installers, hooks, and host plugins. | [Tooling](#mcp-server-and-cli--the-tooling-layer) |
| 🛡️ **Explicit boundaries** | Workspace confinement, symlink rejection, canaries, and env allowlists. | [Security](#security-and-execution-boundaries) |
| 🌍 **Portable setup** | Windows, Linux, macOS, WSL, and Termux installers with shared helpers. | [Cross-platform](#cross-platform-support) |

> **Design rule:** RCoder is an instruction and tooling layer. It never grants permissions, replaces host approvals, or claims that a stored record is proof of model delivery.

---

## Before-and-after evidence

### Before RCoder / with RCoder

The same request, two different experiences:

> **Task:** _"Fix the failing authentication test in this repo."_

| | Before RCoder | With RCoder |
|---|---|---|
| **Orientation** | Opens files in alphabetical order and guesses where auth lives. | RScan shows real entry points, stacks, risks, and likely work items first. |
| **Focus** | Loads an unrelated style guide; constraints disappear in the noise. | One narrow specialist at a time — security, testing, or backend. |
| **Memory** | Your earlier token-expiry decision is gone after compaction. | RFC rehydrates it with source, confidence, and prompt identity. |
| **Change** | Edits the first plausible file, then discovers a second caller too late. | Works through host-approved tools against the scope defined in intake. |
| **Proof** | "Should be fixed." No test output, no diff summary, no artifact. | Runs a focused check; a bounded report can back the recorded criterion. |
| **Handoff** | You scroll the chat to reconstruct what happened. | A capsule records objective, changes, verification, unknowns, next action. |

**How it feels:**

> **Before:** _"I don't know what it touched or whether it verified anything."_
>
> **With RCoder:** _"I can see the recon, the specialist it chose, the check output, and a clean handoff."_

### What actually changes

| Dimension | Before | After |
|---|---|---|
| Starting point | Guesswork | Bounded repository reconnaissance |
| Context | Everything, or nothing | Only what the task needs, with provenance |
| Specialists | Keyword guessing | Deliverable-based progressive selection |
| Verification | Claim → "done" | Claim → artifact → inspected outcome |
| Continuity | Chat history | Structured context capsule |
| Permissions | Assumed by the agent | Host approvals remain authoritative |

> RCoder does not make a weak model strong. It gives any model a better loop to work inside. The measured model-behavior ablation is separate below and is not upgraded by this description.

<details>
<summary><strong>Engineering proof behind these claims</strong></summary>

#### Integration before and after

**VERIFIED locally** on aarch64 PRoot Debian 13, OpenCode 2.4.2, Rust/Cargo 1.85.1, Python 3.13.5, Node 20.19.2. A loopback mock provider with a synthetic key was used; no public API or real credential was contacted.

| Capability | What was missing before | What is now observed | Tier |
|---|---|---|---|
| Native host delivery | Adapters existed; no host-generated request captured. | Installed OpenCode loaded the real plugin; the mock provider captured the actual request body. | VERIFIED |
| RFC + Runtime together | Tested separately. | Both markers arrived in one request with distinct provenance. | VERIFIED |
| Independence | Config-level checks only. | Four enable/disable combinations, retries, missing context, and broken Runtime path exercised. | VERIFIED |
| Companion lifecycle | Offline session tests. | One companion reached `stopped`, bound to the fixture root, no orphan process. | VERIFIED |
| Evidence verification | Caller attestations only. | Allowlisted parser, digest and mutation checks, cycle isolation, 58 passing Rust tests. | VERIFIED |
| Cross-platform fixture | POSIX-only assumptions. | Portable resolvers; 13 parity tests pass, native E2E passes on Linux. | VERIFIED on POSIX; NOT VERIFIED on Windows/macOS |

Reproduce: `python3 scripts/test-cross-platform.py`, `python3 scripts/test-opencode-native-e2e.py`, `cargo test --manifest-path runtime/Cargo.toml --workspace`.

Details: [OpenCode V2 evidence](docs/OPENCODE-V2-ADAPTER.md) · [D-032](docs/DECISIONS.md).

</details>

### Model behavior, measured separately

<details>
<summary><strong>Live ablation: WITHOUT RCoder vs WITH RCoder</strong></summary>

| Metric | WITHOUT | WITH | Difference |
|---|---:|---:|---:|
| Trigger precision | 0.000 | 0.952 | +0.952 |
| Trigger recall | 0.000 | 0.833 | +0.833 |
| Trigger F1 | 0.000 | 0.889 | +0.889 |
| Trigger accuracy | 0.429 | 0.881 | +0.452 |
| Behavioral scenarios passed | 4 / 19 | 6 / 19 | +2 |
| Scenario rubric pass rate | 0.500 | 0.592 | +0.092 |

42 trigger prompts and 19 behavioral scenarios, both arms, with model, host, prompts, tools, permissions, fixture, and rubric held constant. OpenCode 1.19.6 with `openrouter/tencent/hy4-flash`; WITH arm used RCoder v1.11.0.

**Limits:** one pinned model/host/version/dataset; not a claim about v1.16.0; same-model rubric scoring; specialist exact-match 4/24 (16.7%). See [summary](evals/runs/hy4-flash-openrouter-2026-11-19/SUMMARY.md), [scores](evals/runs/hy4-flash-openrouter-2026-11-19/score-final.json), [evidence](evals/runs/hy4-flash-openrouter-2026-11-19/evidence.json), [protocol](docs/LIVE-BENCHMARK.md).

</details>

---

## Why RCoder?

Engineering quality is a **process property**, not a model property. RCoder makes the process explicit:

1. **Look first** — bounded reconnaissance instead of guesses.
2. **Load only what matters** — progressive, task-matched references.
3. **Act through authorized tools** — no permission bypass.
4. **Verify against evidence** — claims stay separate from artifacts.
5. **Hand off cleanly** — a capsule, not a chat scroll.

---

## How RCoder works

```text
  ┌──────────┐   ┌───────────┐   ┌───────────┐   ┌──────────────┐
  │ objective│──▶│ recon     │──▶│ specialists│──▶│ implementation│
  └──────────┘   └───────────┘   └───────────┘   └──────┬───────┘
                                                        │
  ┌────────────────────┐   ┌───────────┐   ┌────────────▼─────────┐
  │ evidence handoff   │◀──│ verification│◀──│ host-approved tools  │
  └────────────────────┘   └───────────┘   └──────────────────────┘
```

| Subsystem | Owns | Does not own |
|---|---|---|
| **RCoder** | Workflow, routing, handoff | Model inference, permissions |
| **RScan** | Bounded repository facts | Source rewriting |
| **RSaver** | Measurement and safe reduction | Silent deletion of evidence |
| **RFC** | Durable context, receipts, canaries | Task state machine |
| **Runtime** | Contracts, transitions, verification | Agent tool interception |

Host adapters only carry information into the real request. They are not a second context store or task engine.

---

## Feature tour

### RScan — look before you edit

RScan is a read-only, bounded scanner. It produces stack detection, a project map, risk signals, and ranked development options before implementation starts.

```sh
python3 skills/rcoder/scripts/rscan.py scan --root . --json
python3 skills/rcoder/scripts/context_snapshot.py . --max-paths 80
```

It is deliberately metadata-first: large source files are sampled, not dumped into context.

### Specialist library

60+ references cover:

| Domain | Examples |
|---|---|
| Core engineering | coding, architecture, debugging, testing, QA, review, performance, DevOps |
| Languages | Rust, Python, JavaScript/TypeScript, Go, C/C++, Java, .NET, PHP, Ruby, Kotlin |
| Platforms | Windows, Linux, Android/AOSP, embedded, GPU, game engines, distributed systems |
| Security | threat modeling, secure review, app/cloud/network security, identity, supply chain, forensics |
| Reverse engineering | binary analysis, file formats, protocols, firmware, ABI reconstruction |
| Context helpers | RSaver, RFC, model adaptation, verification, routing |

Selection is by **deliverable and risk**, not trigger words. Helpers do not become primary specialists.

### RSaver — context intelligence

RSaver is a standard-library toolkit with 23 commands. Retained text is copied verbatim; omitted ranges are recorded so reduction is recoverable.

| Need | Commands |
|---|---|
| Measure and budget | `measure`, `budget`, `gate`, `audit` |
| Safe reduction | `optimize`, `compact`, `dedupe`, `pack`, `unpack`, `recover` |
| Anchoring | `anchor`, `reanchor`, `drift`, `select` |
| Trust | `redact`, `crosscheck`, `verify`, `ledger` |

```sh
python3 skills/rcoder/scripts/rsaver.py measure FILE
python3 skills/rcoder/scripts/rsaver.py optimize --help
```

Token figures are deterministic estimates for relative comparison — never provider billing. See [token economics](docs/TOKEN-ECONOMICS.md).

### RFC Context Fabric — memory with provenance

RFC stores typed context locally and assembles a bounded payload **per request**. A store is not memory: the host must inject the payload into the exact request.

| Lifecycle | Command / behavior |
|---|---|
| Store | `put` — typed item with source, confidence, priority, pinning, expiry |
| Hydrate | `build` — fresh prompt identity, canary, whole-item budget |
| Verify | `ack` — canary match against the raw response |
| Export | `export` — token-free transcript |
| Retain | `gc` — explicit timestamp, inclusive `expires_at <= now` |

```sh
python3 skills/rcoder/scripts/context_fabric.py put --help
python3 skills/rcoder/scripts/context_fabric.py build --help
```

Native adapters exist for Claude Code and OpenCode 2.4.2. Other hosts, MCP write tools, encryption, sync, and vector retrieval are not implemented. See [RFC design](docs/CONTEXT-FABRIC.md).

### RCoder Runtime (optional local control plane)

Runtime is a Rust 2024 executable that follows a real local RCoder MCP process. It is optional and fail-open.

| Area | Capability |
|---|---|
| Lifecycle | Project detection, parent-process monitoring, one companion per MCP process |
| Contracts | Objectives, criteria, constraints, risk, guarded transitions |
| Evidence | Bounded attestations, reopen cycles, auditable history |
| Verification | Confined artifact inspection, allowlisted report parsing, current-cycle attribution |
| Compiler | Deterministic, SHA-256-digested instruction packets with trust boundaries |

```sh
rcoder-runtime detect --project . --json
rcoder-runtime status --project . --json
rcoder-runtime task create --project . --objective "Fix auth test" \
  --acceptance "Focused test passes" --risk high --json
rcoder-runtime task compile --project . --id TASK_UUID --json
rcoder-runtime task verify --project . --id TASK_UUID \
  --evidence EVIDENCE_UUID --artifact reports/result.json \
  --parser rcoder_test_report_v1 --criterion AC-001 --enforce --json
```

`artifact_verified` means a bounded artifact matched a strict report. It does **not** prove a command ran. See [Runtime architecture](docs/RUNTIME.md).

### MCP server and CLI — the tooling layer

The stdio MCP server exposes **39 read-only tools** for reconnaissance, routing, specialist lookup, skill linting, hooks configuration, parity audit, and runtime introspection. It is launched by a host, never by installation.

```sh
python3 skills/rcoder/scripts/rcoder_mcp.py --print-config claude-code
python3 skills/rcoder/scripts/rcoder_mcp.py --root . --profile minimal
```

The `rcoder` CLI handles install/update/uninstall/verify/instructions, `doctor [--json] [--fix]`, `skill new|lint|package`, hooks, and integrations. See [MCP reference](docs/MCP.md).

### Host adapters and hooks

| Host path | Behavior |
|---|---|
| Claude Code | UserPromptSubmit injects RFC context and the active Runtime packet; Stop captures the response. |
| OpenCode 2.4.2 | V2 plugin hydrates each model request independently for RFC and Runtime; V1 middleware remains available. |
| Other hosts | Documented via manifests and CLI instructions; no native adapter is claimed. |

Optional hooks provide a tool guard, completion gate, drift reminders, and host-specific settings. They are lexical guardrails, not a sandbox. See [hooks](docs/HOOKS.md).

---

## Quick start

> **Three steps:** install → verify → ask your agent to do engineering work.

### 1 · Install

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

### 2 · Verify

Open a new terminal so the updated `PATH` is loaded:

```sh
rcoder doctor --json
```

`rcoder doctor --fix` repairs canonical launcher drift conservatively and reports `FIXED` or `SKIP`.

### 3 · Use it

> _"Inspect this repository, then implement the smallest safe fix for the failing test and show me the evidence."_

Full installer options and scopes are in [Installation](#installation).

---

## Installation

Standard skill installation does not require Node.js on native Windows/POSIX installers. The npm route requires Node.js 18.18+.

**Windows examples**

```powershell
& ([scriptblock]::Create((irm 'https://raw.githubusercontent.com/RidTheWann/RCoder-Skills/main/install.ps1'))) -Target qoder -Scope user
# -Mcp show | -Mcp install
```

**POSIX examples**

```sh
sh ./install.sh --host claude --scope user
sh ./install.sh --host gemini --scope project
sh ./install.sh --dry-run
sh ./install.sh --uninstall
```

Launcher locations: `~/.local/bin/rcoder` on POSIX; `%USERPROFILE%\.rcoder\bin\rcoder.cmd` on Windows. The full target list is in [docs/INSTALLATION-MATRIX.md](docs/INSTALLATION-MATRIX.md).

---

## Supported agent hosts

Twenty installation targets are cataloged with evidence tiers T0–T4. A target being installable does **not** prove native discovery or model invocation.

| Path | Meaning |
|---|---|
| T0/T1 | Repository-level packaging and documented configuration |
| T2/T3 | Native discovery and injection observed on a specific host build |
| T4 | Live model behavior observed under a pinned configuration |

Currently observed natively: **Claude Code** and **OpenCode 2.4.2**. Other hosts remain NOT VERIFIED for native activation. See [compatibility evidence](docs/COMPATIBILITY.md).

---

## Cross-platform support

One canonical skill; OS differences are handled by thin resolvers in `platform_runtime.py`.

| Concern | POSIX (Linux, macOS, WSL, Termux) | Windows |
|---|---|---|
| Python | `python3`, then `python`, with health check | Health check plus `py -3`; Store stub rejected |
| Node | `node` via `PATH` | `node.exe` via `PATHEXT` |
| Host command | Absolute path | Absolute path; `.cmd`/`.bat` wrapped with `cmd.exe /c` |
| Isolated config | `XDG_*`, `HOME`, `PWD` | `APPDATA`, `LOCALAPPDATA`, `USERPROFILE`, `TEMP` |
| Fixture links | Symlink preferred | Symlink with bounded copy fallback |

**VERIFIED locally:** POSIX development host. **NOT VERIFIED:** native OpenCode execution on Windows, macOS, and Termux-native builds. Installer simulations do not prove host activation.

---

## Recorded complex task: API migration

From retained case **`s10-api-migration`**:

> Add a required API field backed by a database column while older app versions remain deployed.

| Evidence | Result |
|---|---|
| Skill invoked and `SKILL.md` read | Yes |
| Specialists selected | `api-protocol-engineering`, `data-api`, `database-engineering`, `test-engineering`, `testing-qa` |
| Tool calls / errors | 19 / 3 |
| Rubric | **4 / 4 passed** — scenario PASS |

The workflow maps intake → recon/route → staged expand/migrate/contract plan → authorized execution → compatibility verification. **Boundary:** the retained run stores structured evidence, not a verbatim transcript; three tool errors were recorded. One case is not a universal migration guarantee. See [scenario](evals/scenarios.json) and [case evidence](evals/runs/hy4-flash-openrouter-2026-11-19/evidence.json).

---

## Security and execution boundaries

- **A skill is not authorization.** Security testing requires written scope; otherwise stay passive and local.
- **Host permissions remain authoritative.** RCoder never bypasses approval prompts.
- **Paths are confined.** MCP rejects traversal and escaping symlinks; Runtime rejects symlinked state directories.
- **Evidence is untrusted data.** Source strings are never executed as commands.
- **Canaries prove delivery only with raw-response acknowledgement.** A store or digest is not model memory.
- **Secrets never enter records or exports.** Env allowlists and redaction are mandatory.
- **Unverified stays unverified.** Missing checks, unknown host behavior, and unsupported claims are labeled.

See [SECURITY.md](SECURITY.md), [MCP security](docs/MCP.md), and [hooks limits](docs/HOOKS.md).

---

## Common questions

**Do I need Rust?** No. Runtime is optional.

**Do I need a paid model?** No. The E2E regression uses a local mock provider.

**Does `artifact_verified` mean tests really ran?** It means a bounded artifact matched an allowlisted report; it does not prove command execution or truth of a claim.

**Is Windows/macOS supported?** Portable code paths and unit tests exist, but native activation on those OSes is NOT VERIFIED here.

**Why does `cargo fmt` fail on my Termux image?** A rustup proxy may lack a default toolchain. Use `rustfmt --edition 2024 --check <sources>`; the source contract is unchanged.

**Does a plugin load prove activation?** No. Only observed request injection does.

---

## Development and verification

```sh
# Repository contract
python3 scripts/validate-all

# Rust Runtime
cargo test --manifest-path runtime/Cargo.toml --workspace
rustfmt --edition 2024 --check runtime/crates/runtime-core/src/*.rs \
  runtime/apps/rcoder-runtime/src/main.rs

# Host, RFC and cross-platform regressions
python3 scripts/test-runtime-bootstrap.py
python3 scripts/test-runtime-task-host.py
python3 scripts/test-context-fabric.py
python3 scripts/test-context-fabric-host.py
python3 scripts/test-opencode-host.py
python3 scripts/test-cross-platform.py
node scripts/test-opencode-v2-plugin.mjs
node scripts/test-opencode-plugin-host-state.mjs

# Native OpenCode request capture (local mock provider)
python3 scripts/test-opencode-native-e2e.py

# Packaging
python3 scripts/package
python3 scripts/check-dist.py
```

Local results at the time of writing: **58 Rust tests**, **13 cross-platform tests**, **5 native E2E cases**, **4,648 repository checks** pass. GitHub Actions for the latest local changes remains **NOT VERIFIED** unless the workflow is observed.

---

## Documentation

- [Execution kernel](skills/rcoder/SKILL.md)
- [Architecture](docs/ARCHITECTURE.md)
- [MCP reference](docs/MCP.md)
- [Runtime](docs/RUNTIME.md)
- [Context Fabric](docs/CONTEXT-FABRIC.md)
- [Token economics](docs/TOKEN-ECONOMICS.md)
- [Hooks](docs/HOOKS.md)
- [OpenCode V2 evidence](docs/OPENCODE-V2-ADAPTER.md)
- [Compatibility evidence](docs/COMPATIBILITY.md)
- [Installation matrix](docs/INSTALLATION-MATRIX.md)
- [Environment discovery](docs/ENVIRONMENT.md)
- [Live benchmark protocol](docs/LIVE-BENCHMARK.md)
- [Evaluation results](evals/results.md)
- [Decisions](docs/DECISIONS.md) · [Changelog](CHANGELOG.md) · [Contributing](CONTRIBUTING.md) · [Security](SECURITY.md)

---

## License

RCoder is released under the [MIT License](LICENSE).
