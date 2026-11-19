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
0. **Exit**.

Select several target numbers separated by commas, or enter `A` for all. Shared discovery roots are installed only once. The manager then offers two optional tools:

- **RSaver** — context pruning, budgeting, and re-anchoring for long sessions.
- **RScan** — read-only project scan with ranked development options at session start.

Choose both (default), one, or neither. The choice is saved in `<target-root>/.rcoder-features.json` so an agent can see which tools are enabled; changing the choice requires reinstalling with a different selection.

For non-interactive use, run `npx -y github:RidTheWann/RCoder-Skills --help`. Use `--features rsaver,rscan` (or `--features none`) to select tools, `--list-features` for descriptions, `--dry-run` to preview, `--uninstall` to remove an installation, and `--no-launcher` to install only the selected skill. The PowerShell `irm` route accepts the same selection with `-Features`, and the offline POSIX helper uses `--features`.

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

## Engineering and programming coverage

The router selects focused specialists on demand. Coverage includes:

- **Languages and runtimes:** C, C++, Rust, Python, JavaScript/TypeScript, Node.js, C#, .NET, Java/JVM, Go, Swift, Kotlin, PHP, Ruby, Dart/Flutter, Scala, Elixir/Erlang, Haskell, Lua, R/Julia, plus functional and reactive programming.
- **Product and platform engineering:** frontend, browser/SSR, backend/API, database, protocol contracts, mobile, game engines and emulators, embedded firmware, ML/AI systems, distributed systems, build systems, compilers, and toolchains.
- **Core disciplines:** architecture, accessibility/UI, debugging, test engineering, performance, DevOps/CI/CD, review/refactoring, verification, and technical documentation.

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

**RSaver** (`skills/rcoder/scripts/rsaver.py`, with a repository-root wrapper at `scripts/rsaver.py`) is a dependency-free tool that measures relative context size, extracts bounded symbol windows, prunes non-critical lines from verbose output, collapses exact duplicates only when the marker costs less than the repetition, and records a hash-checked manifest so every omitted range can be recovered exactly. Token figures are deterministic relative estimates, not model-specific counts. Usage and limits are documented in `skills/rcoder/references/rsaver.md`. The **RSaver Gate** (`rsaver gate` / `rsaver budget`) runs before routing and again at each model boundary: it reserves output and reasoning budget, keeps required context, defers optional history with recovery pointers, and checks that the stable cache prefix is contiguous and large enough. Provider mechanics are documented in `docs/TOKEN-ECONOMICS.md`; the gate is a planning layer, not a runtime interceptor. For long sessions that drift, `rsaver drift` reports text signals and `rsaver anchor`/`rsaver reanchor` restate the objective and hard constraints at both ends of the next request using explicit IDs, with observed facts separated from decisions and unknowns (`docs/CONTEXT-DRIFT.md`).

## Repository structure

- `skills/rcoder/SKILL.md` — portable router and operating protocol with a layered execution map.
- `skills/rcoder/references/` — focused engineering, cybersecurity, reverse-engineering, and model-adaptation modules.
- `docs/COMPATIBILITY.md` — host evidence tiers; `docs/ENVIRONMENT.md` — observed capability record.
- `evals/ABLATION-PROTOCOL.md`, `scripts/score-eval.py` — runnable scoring and with/without-RCoder ablation.
- `skills/rcoder/scripts/detect_stack.py` — read-only stack reconnaissance.
- `skills/rcoder/scripts/context_snapshot.py` — bounded metadata-only repository snapshot.
- `skills/rcoder/scripts/rsaver.py` — RSaver measurement, budgeting, gating, pruning, deduplication, and recovery CLI (bundled); `scripts/rsaver.py` is a repository-root wrapper.
- `skills/rcoder/scripts/rscan.py` — RScan bounded project scanner and session-start hook installer (bundled); `scripts/rscan.py` is a repository-root wrapper.
- `docs/RSCAN-HOOKS.md` — evidenced host hook matrix.
- `docs/TOKEN-ECONOMICS.md` — input, cached-input, output, and reasoning token mechanics.
- `docs/CONTEXT-DRIFT.md` — long-context drift research and re-anchoring evidence.
- `skills/rcoder/assets/templates/` — ADR, issue, specialist-module, context-capsule, test, and UX templates.
- `targets.json` — supported host labels and Project/User discovery roots.
- `launcher/RCoder.ps1` — PowerShell terminal manager.
- `scripts/rcoder.mjs` — Node/npm installer and launcher bootstrap.
- `.rcoder/` — optional project-local specialist guidance.

## Development checks

```sh
python3 scripts/validate-all
python3 scripts/test-context-snapshot.py
python3 scripts/test-score-eval.py
python3 scripts/test-rsaver.py
python3 scripts/test-rscan.py
node --check scripts/rcoder.mjs
node scripts/test-node-installer.mjs
npm pack --dry-run --json
bash scripts/test-installers.sh
python3 scripts/package
```

Windows CI also parses the PowerShell entry points and runs the PowerShell installer matrix. Static checks and simulations do not prove that every host model discovers or invokes the skill; native activation remains a separate verification gate.

## Evaluation

Static gates verify structure, installers, and packaging; they do not prove model improvement. `docs/LIVE-BENCHMARK.md` defines the controlled with/without-RCoder protocol for Hy4 Flash Free on OpenCode, and `evals/results.md` records the current live status as NOT VERIFIED.

## License

MIT. See `LICENSE`.
