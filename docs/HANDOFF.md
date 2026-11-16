# RCoder project handoff — v1.2.0

## Delivered

RCoder remains one portable Agent Skill with progressive disclosure. The core router selects focused references rather than injecting the entire specialist library into every agent context.

Version 1.2.0 adds:
- A global terminal manager invoked by typing `RCoder`.
- Twenty Agentic AI/CLI integrations with Project/User scopes, multi-selection, shared-root deduplication, update, uninstall, backup, and restore.
- A Windows-native PowerShell launcher installed through the existing `irm` bootstrap; this route does not require Node.js.
- A Node/npm installer that provisions a global launcher on Node-enabled platforms.
- Expanded programming-language, systems, platform, cybersecurity, reverse-engineering, and smart-contract specialists.
- A metadata-only bounded repository snapshot helper and context-capsule template.
- 42 trigger prompts and 14 behavioral evaluation scenarios.

Repository: https://github.com/RidTheWann/RCoder-Skills
Feature branch: `feat/agent-cli-launcher-1.2.0`

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

## Validation

The feature branch must pass its Linux/Windows GitHub Actions matrix before merge. CI covers static validation, context-snapshot regression, Node syntax and installer tests, npm package dry-run, 40 POSIX target/scope cases, 40 PowerShell target/scope cases, and reproducible packages.

Do not claim native model activation in all hosts from path simulations alone. Native discovery and live model triggering remain separate verification gates.

## Safety and maintenance

1. Keep all repository-maintained text in English.
2. Require explicit authorization and written scope for active security testing.
3. Preserve sample provenance and hashes during reverse engineering and forensics.
4. Do not guess undocumented ABI or machine-state semantics.
5. Keep `targets.json`, Node/PowerShell/POSIX adapters, tests, and docs synchronized.
6. Keep package/plugin/skill/changelog versions synchronized.
