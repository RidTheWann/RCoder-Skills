# RCoder

**RCoder** is a portable, model-agnostic engineering skill and installer for Agentic AI and coding CLIs. It routes implementation, architecture, debugging, QA, performance, DevOps, data/API, cybersecurity, and reverse-engineering tasks to focused expert references.

Its core follows progressive disclosure: agents receive concise skill metadata first, then load only specialist guidance relevant to the current task.

## Installation

RCoder retains both official installation methods. Choose PowerShell `irm` or Node.js/npm.

### Windows PowerShell — `irm`

Run from the project directory where the default skill should be installed:

```powershell
irm https://raw.githubusercontent.com/RidTheWann/RCoder-Skills/main/install.ps1 | iex
```

The bootstrap supports Windows PowerShell 5.1 and PowerShell 7+. It installs `.agents/skills/rcoder` by default, then creates a Windows-native global launcher at `%USERPROFILE%\.rcoder\bin\RCoder.cmd`. The manager invokes the bundled PowerShell script, so **Node.js is not required for the `irm` route**.

To select a target or user scope directly:

```powershell
& ([scriptblock]::Create((irm 'https://raw.githubusercontent.com/RidTheWann/RCoder-Skills/main/install.ps1'))) -Target qoder -Scope user
```

Add `-Mcp show` to print the MCP server config for that host, or `-Mcp install` to set it up automatically (see [MCP server setup](#mcp-server-setup)). If PowerShell blocks a downloaded script, run the one-liner above instead of saving the file, or start it with `powershell -ExecutionPolicy Bypass -File .\install.ps1`.

### Node.js and npm

Run from the project directory:

```sh
npx -y github:RidTheWann/RCoder-Skills
```

The command installs the generic Agent Skills path and provisions the global `RCoder` terminal command. Requirements: Node.js 18.18+, npm, and Git (npm uses Git to retrieve the GitHub package). On Linux/macOS, the launcher is installed under `~/.local/bin/RCoder`; on Windows, it is installed under `%USERPROFILE%\.rcoder\bin\RCoder.cmd`.

Choose a specific host and scope:

```sh
npx -y github:RidTheWann/RCoder-Skills --target codex --scope project
npx -y github:RidTheWann/RCoder-Skills --target factory --scope user
```

### Open the terminal launcher

Open a **new terminal** after installation and type:

```sh
RCoder
```

The interactive menu provides:

1. **Install / Update RCoder** — select one or more hosts, then Project or User scope.
2. **Uninstall RCoder** — remove the selected skill and restore the latest pre-existing backup when available.
3. **Show supported agents** — display the available integrations.
4. **Set up MCP server** — configure the MCP server for hosts where RCoder is already installed.
0. **Exit**.

Select several target numbers separated by commas, or enter `A` for all. Shared discovery roots are installed only once. The manager then offers two optional tools:

- **RSaver** — context pruning, budgeting, and re-anchoring for long sessions.
- **RScan** — read-only project scan with ranked development options at session start.

Choose both (default), one, or neither. During an install the manager then asks about the MCP server: show the config to paste (default, changes nothing), set it up automatically, or skip. The choice is saved in `<target-root>/.rcoder-features.json` so an agent can see which tools are enabled; changing the choice requires reinstalling with a different selection.

For non-interactive use, run `npx -y github:RidTheWann/RCoder-Skills --help`. Use `--features rsaver,rscan` (or `--features none`) to select tools, `--list-features` for descriptions, `--dry-run` to preview, `--uninstall` to remove an installation, and `--no-launcher` to install only the selected skill. The PowerShell `irm` route accepts the same selection with `-Features`, and the offline POSIX helper uses `--features`.

### MCP server setup

The MCP server is optional and is not started by installing the skill; the host must be told how to launch it. The installers can configure the stdio transport. An additional loopback-only Streamable HTTP transport is available for local clients that specifically need HTTP; it requires a locally generated bearer token and explicit Origin allowlist and is never enabled by the installer.

| Route | Print the config | Set it up automatically |
|---|---|---|
| Terminal manager (`RCoder`) | MCP step during install, or action 4 | choose "Set it up automatically" |
| PowerShell | `-Mcp show` | `-Mcp install` |
| Node / npx | `--mcp show` | `--mcp install` |
| POSIX helper | `--mcp show` | `--mcp install` |

Automatic setup needs Python 3 (the server is a Python script) and supports Claude Code, Cursor, Gemini CLI, GitHub Copilot (VS Code, project scope), OpenCode, and Codex (user scope). It only adds the `rcoder` entry, backs up the file first, never overwrites a different entry, leaves files with comments untouched (printing the snippet instead), and finishes with a live self-test. Other hosts print the generic `mcpServers` snippet. Project scope uses a relative script path, so the config is safe to commit; user scope uses an absolute path. For the optional HTTP transport, see [MCP Streamable HTTP](docs/MCP.md#streamable-http-transport); it is not configured automatically.

## Plugin and extension integrations

The regular skill installer copies only the canonical skill. When a host-specific plugin or extension is also needed, use the integration manager:

```sh
RCoder integration install opencode --scope project
RCoder integration install gemini-cli
RCoder integration install codex
RCoder integration install claude-code
RCoder integration verify opencode --scope project
```

The equivalent Node/npm entry point is `npx -y github:RidTheWann/RCoder-Skills integration <action> <host>`. The global `RCoder` command forwards `integration`, `skill`, and `doctor` subcommands; typing `RCoder` without arguments still opens the interactive manager.

- **OpenCode:** installs the canonical skill under `.opencode/skills/rcoder/` and the V1 plugin adapter under `.opencode/plugins/rcoder.js`. Existing MCP configuration is not changed by this action. The adapter uses the V1 `experimental.chat.system.transform` hook and adds bounded RCoder guidance plus the read-only RScan summary. The `verify` action checks file presence only, not native plugin loading.
- **Gemini CLI:** runs `gemini extensions install https://github.com/RidTheWann/RCoder-Skills`. The extension contains `gemini-extension.json`, `GEMINI.md`, three namespaced commands, and the portable MCP launcher. Start a new Gemini CLI session after installation.
- **Codex:** adds the repository marketplace with `codex plugin marketplace add RidTheWann/RCoder-Skills`. Then open Codex `/plugins`, select the `rcoder` plugin from `rcoder-skills`, and install it. Adding the marketplace does not install or activate the plugin by itself.
- **Claude Code:** prints the commands `/plugin marketplace add RidTheWann/RCoder-Skills` and `/plugin install rcoder@rcoder-skills` for execution inside Claude Code. The local manager does not claim to have installed the plugin when it only prints these instructions.

Use `update`, `uninstall`, `verify`, or `instructions` in place of `install`. Gemini and Codex actions invoke their native CLIs; set `RCODER_GEMINI_BIN` or `RCODER_CODEX_BIN` when the executable is not named `gemini` or `codex`. Claude Code integration commands are intentionally printed for the host session.

See [Plugin integration matrix](docs/PLUGIN-INTEGRATION-MATRIX.md) for manifests, exact paths, version constraints, and evidence status. Installation simulations verify file operations and command construction; native host discovery and invocation remain separate gates.

## Supported Agentic AI and CLI hosts

`targets.json` is the catalog used by the Node CLI, PowerShell bootstrap, and terminal manager. The same canonical `skills/rcoder/` folder is installed in the following native roots:

| Host | Project skill root | User skill root |
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

Host discovery can vary by product version and UI surface. Path simulations do not prove that a native host will invoke the skill. See `docs/COMPATIBILITY.md` for the five-tier evidence matrix (file install, documented discovery, native discovery, invocation, behavioral evaluation) and `docs/RESEARCH-TODO.md` for runtime checks. Observed runtimes and capability limits for the primary development shell are recorded in `docs/ENVIRONMENT.md`.

## Model adaptation and orchestration

RCoder adapts to the model and host actually present. The [model adaptation specialist](skills/rcoder/references/model-adaptation.md) provides an observable capability-discovery checklist, four execution profiles (Focused, Engineering, Deep Research, Long-Running Project), a smallest-sufficient-workflow rule, subagent strategy, and a reusable ablation methodology that holds model, settings, tools, permissions, fixture, prompt, and rubric constant. Capabilities that cannot be observed are recorded as UNKNOWN, not guessed. No model-specific performance claim is made without a retained evaluation; see `evals/results.md`.

## RSaver crosscheck and safe maximum compression

`rsaver crosscheck` verifies a completion claim against the observed diff, test output, and optional provider usage, returning `PASS`, `FAIL`, or `UNVERIFIED` with line-referenced evidence. `rsaver pack`/`unpack` provide exact-recovery compression that is used only when the estimated token count actually decreases. RSaver **cannot** change provider billing, zero charges, or guarantee compensation: it prevents avoidable token waste and produces evidence a user may attach to a provider support request under that provider's policy. See `docs/BILLING-AND-CROSSCHECK.md`.

## RScan: automatic project reconnaissance

After installation, a fresh session can start with `python3 skills/rcoder/scripts/rscan.py scan --root .`. RScan is read-only and bounded: it reports detected stacks, quality entry points, risk signals, and a ranked menu of development options with first commands and specialist references. For automatic launch scanning, `rscan hooks install --host claude-code|gemini-cli --scope project|user` merges a documented `SessionStart` hook with a backup and idempotence check; other hosts require manual invocation until evidence exists. See `docs/RSCAN-HOOKS.md` and `skills/rcoder/references/rscan.md`.

## MCP server and plugin components

RCoder ships an optional, read-only, dependency-free stdio [MCP](https://modelcontextprotocol.io) server (`skills/rcoder/scripts/rcoder_mcp.py`) that exposes RScan, the complete RSaver toolset (budgeting, gating, compaction, deduplication, drift detection, anchor/re-anchor, pack/unpack, range recovery, verification), stack detection, the bounded snapshot, specialist lookup with section-level loading, and a deterministic routing-selection validator, plus resources and workflow prompts. Every path is confined to the project root, credential files are refused, helpers run without a shell, and output is bounded.

```sh
python3 skills/rcoder/scripts/rcoder_mcp.py --print-config claude-code   # also: codex, cursor, gemini-cli, vscode, opencode, generic
python3 skills/rcoder/scripts/rcoder_mcp.py --root . --profile minimal   # 4 tools, about 675 estimated tokens
```

The Claude Code plugin additionally provides slash commands (`scan`, `route`, `plan`, `debug`, `test-plan`, `threat-model`, `review`, `verify`, `handoff`, `doctor`, `saver`, `agent-security`, `observe`) and seven least-privilege subagents (`rcoder-explorer`, `rcoder-planner`, `rcoder-debugger`, `rcoder-reviewer`, `rcoder-verifier`, `rcoder-security-reviewer`, `rcoder-saver`). A new `agent-extensions-engineering` specialist covers building, reviewing, packaging, and debugging MCP servers, Agent Skills, plugins, hooks, and subagents. The only hook that ships enabled is the read-only `SessionStart` RScan menu. A separate, **opt-in** guard (`PreToolUse`) and completion gate (`Stop`) can be enabled explicitly with `python3 skills/rcoder/scripts/rcoder_hooks.py install`; see [docs/HOOKS.md](docs/HOOKS.md) for rules, limits, and evidence status. See [docs/MCP.md](docs/MCP.md) for tools, security model, context cost, and the evidence status: protocol behavior is verified locally; native host connection and plugin loading are NOT VERIFIED.

## Engineering and programming coverage

The router selects focused specialists on demand. Coverage includes:

- **Languages and runtimes:** C, C++, Rust, Python, JavaScript/TypeScript, Node.js, C#, .NET, Java/JVM, Go, Swift, Kotlin, PHP, Ruby, Dart/Flutter, Scala, Elixir/Erlang, Haskell, Lua, R/Julia, plus functional and reactive programming.
- **Product and platform engineering:** frontend, browser/SSR, backend/API, database, protocol contracts, mobile, game engines and emulators, embedded firmware, ML/AI systems, distributed systems, build systems, compilers, and toolchains.
- **Platform engineering:** Android platform/AOSP and custom ROMs, Windows platform (Win32, services, installers, PowerShell), infrastructure as code and Kubernetes, and graphics/GPU programming.
- **Core disciplines:** architecture, accessibility/UI, debugging, test engineering, performance, DevOps/CI/CD, review/refactoring, verification, and technical documentation.
- **Agent extensions:** MCP servers, Agent Skills, plugins and marketplaces, slash commands, hooks, and subagents.

## Cybersecurity coverage

Security work is defensive and evidence-led. Specialist areas include:

- Threat modeling and secure code review.
- Application, API, web, mobile, cloud, container, infrastructure, network, and protocol security.
- Identity and access control, cryptography, certificate/key lifecycle, and secrets management.
- Dependency and software supply-chain security.
- Vulnerability research and authorized penetration testing with written scope, rate limits, stop conditions, and non-destructive proof.
- Incident response, digital forensics, suspicious-file triage, and malware analysis in isolated environments.
- Binary exploitation mitigation and smart-contract security.

RCoder does not grant authorization. Active scanning, exploitation, malware execution, credential testing, or external-system probing requires explicit permission and a defined scope. When authorization is unclear, remain in passive source/configuration review and local test fixtures.

## Reverse engineering

Use the reverse-engineering specialists for authorized binary analysis, disassembly/decompilation, undocumented file formats/protocols, ABI/ISA reconstruction, emulator/recompiler semantics, and compatibility research.

Preserve originals and hashes; record tool versions and offsets; distinguish observations from hypotheses; isolate dynamic analysis; and validate conclusions through differential tests, reference implementations, or hardware evidence. Unresolved machine-state or ABI behavior must remain unknown rather than guessed.

## Token-efficient engineering and RSaver

RCoder uses progressive disclosure to reduce unnecessary context. The token-efficiency module applies these practices:

1. Read the lightweight router, then load only directly relevant references.
2. Use `skills/rcoder/scripts/context_snapshot.py` for a bounded metadata-only repository map. It lists paths and Git state, skips dependency/build trees and symlinks, and does not print source contents.
3. Search exact symbols and read bounded file ranges; inspect focused diffs rather than dumping entire repositories or logs.
4. Keep a concise working ledger and use `assets/templates/context-capsule-template.md` for long tasks and handoffs.
5. Deduplicate tool calls and parallelize only independent read-only work. Give subagents explicit file scopes and acceptance criteria.
6. Preserve exact verification evidence, security constraints, and unresolved risks. Never reduce test quality or omit safety checks merely to save tokens.

**RSaver** (`skills/rcoder/scripts/rsaver.py`, with a repository-root wrapper at `scripts/rsaver.py`) is a dependency-free tool that measures relative context size, ranks a whole project's files by estimated context cost with `rsaver audit` (read-only; flags lockfiles, minified or generated files, logs, and data files and never prints contents), masks credential-shaped values with `rsaver redact`, tracks cumulative savings with `rsaver ledger`, extracts bounded symbol windows, prunes non-critical lines from verbose output, collapses exact duplicates only when the marker costs less than the repetition, and records a hash-checked manifest so every omitted range can be recovered exactly. Token figures are deterministic relative estimates, not model-specific counts. Usage and limits are documented in `skills/rcoder/references/rsaver.md`. The **RSaver Gate** (`rsaver gate` / `rsaver budget`) runs before routing and again at each model boundary: it reserves output and reasoning budget, keeps required context, defers optional history with recovery pointers, and checks that the stable cache prefix is contiguous and large enough. Provider mechanics are documented in `docs/TOKEN-ECONOMICS.md`; the gate is a planning layer, not a runtime interceptor. For long sessions that drift, `rsaver drift` reports text signals and `rsaver anchor`/`rsaver reanchor` restate the objective and hard constraints at both ends of the next request using explicit IDs, with observed facts separated from decisions and unknowns (`docs/CONTEXT-DRIFT.md`).

## Agent Skill authoring toolkit

The Node/npm CLI and global `RCoder` command expose three authoring operations:

```sh
RCoder skill new mcp-observability --description "Use when designing and verifying MCP observability workflows."
RCoder skill lint ./mcp-observability
RCoder skill package ./mcp-observability --out ./dist/mcp-observability.zip
```

`skill new` creates a non-overwriting Agent Skill scaffold with a specialist-module template. `skill lint` checks frontmatter, semantic version metadata, the 300-line instruction/reference limit, local Markdown links, one-level reference layout, file/byte limits, symlinks, and credential/private-key filenames. Specialist references that declare `Activate when` must follow the full 13-section module structure. `skill package` lints first, builds a deterministic ZIP, and writes a SHA-256 sidecar. The package is reproducible for identical source bytes and normalized executable modes. The PowerShell-only global launcher can run these three commands with Python 3 even when Node.js is not installed.

## Opt-in hook management

The same CLI manages the opt-in Claude Code guard and completion-gate hooks (see `docs/HOOKS.md` and decision D-021):

```sh
RCoder hooks install --scope project --dry-run
RCoder hooks install --scope user --profile strict
RCoder hooks uninstall --scope project
RCoder hooks print-config
```

`install` merges idempotently with a backup, refuses symbolic links and non-strict JSON, and only touches the RCoder entries. Hook handlers fail open and never use a subprocess, network, or dynamic code. The MCP tools `rcoder_hooks_config`, `rcoder_skill_lint`, and `rcoder_contract` expose read-only views of the same capabilities; they never write.

`RCoder doctor --json` checks the runtime, package/manifest version parity, shared MCP contract, required adapters, and bundled helper files. It is an environment/static check—not proof of host discovery or model invocation.

## Repository structure

- `skills/rcoder/SKILL.md` — portable router and operating protocol with a layered execution map.
- `skills/rcoder/references/` — focused engineering, cybersecurity, reverse-engineering, and model-adaptation modules.
- `docs/COMPATIBILITY.md` — host evidence tiers; `docs/ENVIRONMENT.md` — observed capability record.
- `evals/ABLATION-PROTOCOL.md`, `scripts/score-eval.py` — runnable scoring and with/without-RCoder ablation.
- `skills/rcoder/scripts/detect_stack.py` — read-only stack reconnaissance.
- `skills/rcoder/scripts/context_snapshot.py` — bounded metadata-only repository snapshot.
- `skills/rcoder/scripts/rsaver.py` — RSaver measurement, budgeting, gating, pruning, deduplication, and recovery CLI (bundled); `scripts/rsaver.py` is a repository-root wrapper.
- `skills/rcoder/scripts/rcoder_mcp.py` — legacy stdio MCP server; `rcoder_mcp_modern.py` is the stateless modern dispatcher; `rcoder_mcp_http.py` is the optional loopback/token/Origin-protected HTTP adapter; `rcoder_contract.py` is the shared protocol and pagination contract.
- `commands/` and `agents/` — Claude Code plugin slash commands and least-privilege subagents.
- `skills/rcoder/scripts/rcoder_hooks.py` — opt-in `PreToolUse` guard and `Stop` completion-gate handlers with an idempotent settings installer (`scripts/rcoder-hooks.py` is the repository-root wrapper); see `docs/HOOKS.md`.
- `skills/rcoder/scripts/rscan.py` — RScan bounded project scanner and session-start hook installer (bundled); `scripts/rscan.py` is a repository-root wrapper.
- `docs/RSCAN-HOOKS.md` — evidenced host hook matrix.
- `docs/TOKEN-ECONOMICS.md` — input, cached-input, output, and reasoning token mechanics.
- `docs/CONTEXT-DRIFT.md` — long-context drift research and re-anchoring evidence.
- `skills/rcoder/assets/templates/` — ADR, issue, specialist-module, context-capsule, test, and UX templates.
- `targets.json` — supported host labels and Project/User discovery roots.
- `CONTRIBUTING.md`, `SECURITY.md`, and `.github/` templates — contribution gates, vulnerability reporting, and issue and pull request templates.
- `launcher/RCoder.ps1` — PowerShell terminal manager.
- `scripts/rcoder.mjs` — Node/npm installer, integration manager, doctor command, and skill-authoring CLI.
- `launcher/rcoder-mcp.mjs` — portable Node-to-Python stdio launcher used by plugin manifests.
- `skills/rcoder/scripts/skill_authoring.py` — Agent Skill scaffold, linter, and reproducible packager.
- `.rcoder/` — optional project-local specialist guidance.

## Development checks

```sh
python3 scripts/validate-all
python3 scripts/test-context-snapshot.py
python3 scripts/test-score-eval.py
python3 scripts/test-rsaver.py
python3 scripts/test-rscan.py
python3 scripts/test-mcp.py
python3 scripts/test-mcp-contract.py
python3 scripts/test-mcp-http.py
python3 scripts/test-hooks.py
python3 scripts/test-skill-authoring.py
python3 scripts/test-multilingual-data.py
node --check scripts/rcoder.mjs
node scripts/test-cli-skill.mjs
node scripts/test-integrations.mjs
node scripts/test-node-installer.mjs
npm pack --dry-run --json
bash scripts/test-installers.sh
python3 scripts/package
```

Windows CI also parses the PowerShell entry points and runs the PowerShell installer matrix. Static checks and simulations do not prove that every host model discovers or invokes the skill; native activation remains a separate verification gate.

## Evaluation

Static gates verify structure, installers, and packaging; they do not prove model improvement. `docs/LIVE-BENCHMARK.md` defines the controlled with/without-RCoder protocol for Hy4 Flash Free on OpenCode. A completed controlled ablation (61 cases × 2 arms, strict scorer exit 0) is retained in `evals/runs/hy4-flash-openrouter-2026-11-19/` and summarized in `evals/results.md`; the earlier quota-limited partial run is retained separately. Native skill discovery and end-to-end RScan menu injection were both directly observed in OpenCode 1.19.6. Results apply only to the pinned model and configuration recorded with the run.

v1.13.0 adds a separate, bounded control-vs-treatment live comparison on the authorized free tier (`evals/runs/v113-live-free-2026-11-19/`): specialist F1 0.368 -> 0.476 and empty positive selections 7/12 -> 5/12, with a trigger-F1 regression from 0.957 to 0.857 in the same small sample. No independent judge, full-dataset rerun, multilingual run, or non-OpenCode host activation is claimed. `docs/V1.13-DELIVERY.md` classifies every important assertion.

## License

MIT. See `LICENSE`.
