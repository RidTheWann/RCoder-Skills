# RCoder project handoff — v1.3.0

## Delivered

RCoder remains one portable Agent Skill with progressive disclosure. The core router selects focused references rather than injecting the entire specialist library into every agent context.

Version 1.3.0 adds:
- A model-adaptation specialist: observable capability discovery, four adaptive execution profiles, empirical ablation/evaluation methodology, subagent strategy, and long-task continuity.
- A five-tier host compatibility evidence matrix separating file installation from documented discovery, native discovery, invocation, and behavioral evaluation.
- An environment and capability record for the Termux/OpenCode development shell, with observed runtimes and explicitly unknown capabilities.
- A compact router layer map (A-F) and an English-only 13-section specialist authoring template.
- A normalized evaluation contract; `rubric.md` and `results.md` now match the enforced dataset and label non-English activation and model performance claims `NOT VERIFIED`.
- Depth parity across all 54 specialist modules (full 13-section structure) without removing any module.
- An executable evaluation harness: routing expectations, a deterministic scorer with ablation deltas, its self-test, an ablation protocol, and five additional scenarios (s15-s19) for capability discovery, tool adaptation, context handoff, finding classification, and evidence-led reverse engineering.

Version 1.2.0 added:
- A global terminal manager invoked by typing `RCoder`.
- Twenty Agentic AI/CLI integrations with Project/User scopes, multi-selection, shared-root deduplication, update, uninstall, backup, and restore.
- A Windows-native PowerShell launcher installed through the existing `irm` bootstrap; this route does not require Node.js.
- A Node/npm installer that provisions a global launcher on Node-enabled platforms.
- Expanded programming-language, systems, platform, cybersecurity, reverse-engineering, and smart-contract specialists.
- A metadata-only bounded repository snapshot helper and context-capsule template.
- 42 trigger prompts and 14 behavioral evaluation scenarios.

Repository: https://github.com/RidTheWann/RCoder-Skills
Main branch: `main`  
Merged PR: [#1](https://github.com/RidTheWann/RCoder-Skills/pull/1)  
Merge commit: `7f7c88f2fce5b8b2754d9cc10c65cca69a23f5ed`

## Installation

### Windows PowerShell

```powershell
irm https://raw.githubusercontent.com/RidTheWann/RCoder-Skills/main/install.ps1 | iex
```

Supports Windows PowerShell 5.1 and PowerShell 7+. It downloads the repository archive over HTTPS, installs the selected skill, registers `%USERPROFILE%\.rcoder\bin` in the user PATH, and creates `RCoder.cmd`. Node.js is not required for this Windows `irm` route.

### Node.js/npm

```sh
npx -y github:RidTheWann/RCoder-Skills
```

Requires Node.js 18.18+, npm, and Git. It installs the selected skill and provisions `RCoder` under `~/.local/bin` on POSIX or `%USERPROFILE%\.rcoder\bin` on Windows.

After installation, open a new terminal and type `RCoder`.

## Terminal manager

1. Install / Update.
2. Uninstall / restore the latest backup.
3. Show supported agents.
0. Exit.

Choose one or more target indices (comma-separated or `A` for all), then Project or User scope. Shared discovery roots are deduplicated.

## Target catalog

The catalog covers Claude Code, Codex CLI, Cursor, Gemini CLI, GitHub Copilot, generic Agent Skills, Qoder, OpenCode, Antigravity, Amp, Zed, Pi, OpenClaw, Autohand, Warp, Kilo Code, Cline, Roo Code, TRAE, and Factory Droid.

`targets.json` is the canonical label/path matrix. Node CLI and PowerShell terminal manager read the catalog; the PowerShell bootstrap downloads it before resolving the selected target. Offline shell/PowerShell adapters and CI tests validate their path maps.

## Specialist coverage

Programming references cover language/runtime routing, C/C++/Rust, Python, JavaScript/TypeScript, .NET/JVM, Go, polyglot ecosystems, frontend/browser, backend, databases, API protocols, mobile, game/emulation, embedded, ML/AI, distributed systems, functional programming, build systems, and debugging/testing.

Cybersecurity references cover threat modeling, secure review, application/cloud/container/network security, identity/cryptography/secrets, supply chain, vulnerability research, authorized penetration testing, incident response/forensics, defensive malware triage, binary hardening, and smart contracts.

Reverse-engineering references cover executable/binary analysis, evidence-led semantic reconstruction, undocumented file formats, and compatibility/emulator/recompiler research.

## Token-efficiency strategy

- Progressive disclosure: do not load the entire reference library by default.
- Bounded reconnaissance: the context snapshot prints repository metadata and paths only.
- Exact reads: symbol searches, line ranges, and focused diffs.
- Context capsule: preserve decisions, evidence, changed files, verification, and next actions.
- Deduplicated tool calls and non-overlapping subagent scopes.
- No reduction in authorization, security, test, or data-integrity checks to save tokens.

## Local verification for v1.3.0

Run in the Termux development shell on the `feat/adaptive-specialist-system` branch:

- `python3 scripts/validate-all` — PASS, 708 checks.
- `python3 scripts/test-context-snapshot.py` — PASS, including the new bounded-path assertion.
- `python3 scripts/test-score-eval.py` — PASS, scorer verified on synthetic perfect, mixed, inverted, and four rejection paths.
- `python3 scripts/score-eval.py --predictions <synthetic-fixture> --strict` — PASS on a generated fixture: 24 TP / 18 TN, specialist F1 1.0, 19/19 scenarios (synthetic only, not a model result).
- `node --check scripts/rcoder.mjs` — PASS (exit 0).
- `node scripts/test-node-installer.mjs` — PASS, all 40 target/scope combinations plus backup restore and launcher checks.
- `bash scripts/test-installers.sh` — PASS, all 40 POSIX target/scope combinations.
- `npm pack --dry-run --json` — PASS, package `rcoder@1.3.0`, 71 entries.
- `python3 scripts/package` — PASS; five ZIPs created and `sha256sum -c dist/SHA256SUMS` verified all OK.

**CI status for v1.3.0: NOT VERIFIED** (feature branch has not run the hosted matrix). Windows PowerShell, the `irm` bootstrap, host-native discovery, and live model activation are also NOT VERIFIED in this environment. The v1.2.0 CI evidence below is historical and does not cover v1.3.0 changes.

## Historical CI evidence (v1.2.0)

**CI status: PASS.** The pre-merge PR matrix passed, and post-merge GitHub Actions run [43940645566](https://github.com/RidTheWann/RCoder-Skills/actions/runs/43940645566) completed successfully on both Linux and Windows for the exact `main` merge commit `7f7c88f2fce5b8b2754d9cc10c65cca69a23f5ed`.

The run verified 644 static checks, context-snapshot regression, Node syntax, 40 Node target/scope cases per OS, launcher and interactive-menu behavior, npm package dry-run, 40 POSIX target/scope cases, 40 Windows PowerShell target/scope cases on both PowerShell 5.1 and 7, and reproducible skill/plugin/source package builds.

Do not claim native model activation in all hosts from path simulations alone. Native discovery and live model triggering remain separate verification gates.

## Safety and maintenance

1. Keep all repository-maintained text in English.
2. Require explicit authorization and written scope for active security testing.
3. Preserve sample provenance and hashes during reverse engineering and forensics.
4. Do not guess undocumented ABI or machine-state semantics.
5. Keep `targets.json`, Node/PowerShell/POSIX adapters, tests, and docs synchronized.
6. Keep package/plugin/skill/changelog versions synchronized.
