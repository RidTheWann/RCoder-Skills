# RCoder

**RCoder** is a portable, model-agnostic software engineering skill for coding agents. It routes software tasks to focused expert references and applies an evidence-led workflow across implementation, architecture, UI/UX, debugging, QA, security, performance, DevOps, data/API, review, and documentation.

## Install in one command

### Windows PowerShell

Supported on Windows PowerShell 5.1 and PowerShell 7 or newer. Run from the root of the project where RCoder should be installed:

```powershell
irm https://raw.githubusercontent.com/RidTheWann/RCoder-Skills/main/install.ps1 | iex
```

This installs the generic Agent Skills path at `.agents/skills/rcoder`. The bootstrap downloads the repository archive to a temporary directory, copies the bundled skill, and removes the temporary files.

To select a specific host or user scope:

```powershell
& ([scriptblock]::Create((irm 'https://raw.githubusercontent.com/RidTheWann/RCoder-Skills/main/install.ps1'))) -Target claude-code -Scope project
```

Available targets: `claude-code`, `codex`, `cursor`, `gemini-cli`, `copilot`, and `agents`. Available scopes: `project` and `user`.

### Node.js and npm

Run from the root of the project where RCoder should be installed:

```sh
npx -y github:RidTheWann/RCoder-Skills
```

The command installs the generic Agent Skills path at `.agents/skills/rcoder`.

Select a host or install scope with options:

```sh
npx -y github:RidTheWann/RCoder-Skills --target codex --scope project
npx -y github:RidTheWann/RCoder-Skills --target cursor --scope user
```

Requirements: Node.js 18.18 or newer, npm, and Git (npm uses Git to retrieve the GitHub package). No global RCoder installation or third-party runtime dependencies are required.

### Uninstall

```sh
npx -y github:RidTheWann/RCoder-Skills --uninstall
```

PowerShell:

```powershell
& ([scriptblock]::Create((irm 'https://raw.githubusercontent.com/RidTheWann/RCoder-Skills/main/install.ps1'))) -Uninstall
```

The installer preserves the current installation and restores the most recent backup when available. Use `--dry-run` with Node or `-DryRun` with PowerShell to preview changes.

> **Security note:** the PowerShell one-liner executes the repository's bootstrap script over HTTPS. Review [`install.ps1`](install.ps1) before running it in environments that require manual script approval. The Node installer retrieves the Git repository through npm and executes the checked-in CLI entry point.

## Quick start

After installation, reload your coding agent and ask:

> Trace the failing API test, identify the root cause, add a regression test, make the smallest correct fix, run the relevant checks, and report exact evidence.

Other examples:

- “Audit this Rust workspace for correctness and security risks. Fix only confirmed defects and run the relevant checks.”
- “Compare two API migration designs, record an ADR, and implement the first safe slice.”
- “Review this React settings screen for keyboard navigation, responsive states, and WCAG 2.2 AA.”

## Architecture

- `skills/rcoder/SKILL.md` is the portable router and operating protocol.
- `skills/rcoder/references/` contains focused expert modules, loaded only when relevant.
- `skills/rcoder/scripts/detect_stack.py` provides read-only repository reconnaissance.
- `skills/rcoder/assets/templates/` contains ADR, bug report, expert module, PR, test plan, and UX audit templates.
- `.rcoder/` can hold project-specific expert modules and conventions.
- `plugin.json` is the portable Agent Plugins manifest. `.codex-plugin/plugin.json` remains a compatibility fallback.

All repository-maintained instructions, docs, prompts, templates, comments, and installer messages are written in English. Do not mix languages within a repository artifact.

## Extend and maintain

Copy `skills/rcoder/assets/templates/expert-module-template.md` into `skills/rcoder/references/`, keep each expert module at or below 300 lines, add a routing signal to `skills/rcoder/SKILL.md`, and add an evaluation case. Project-only expertise belongs in `.rcoder/`.

Update the installation baseline only after checking current official product documentation. Record design choices in `docs/DECISIONS.md`, update `docs/research-log.md`, synchronize SemVer across `package.json`, plugin manifests, `CHANGELOG.md`, and `scripts/package`, then run the full validation suite.

## Development checks

```sh
python3 scripts/validate-all
node scripts/test-node-installer.mjs
npm pack --dry-run --json
bash scripts/test-installers.sh
python3 scripts/package
```

The CI workflow runs static validation, Node installer simulations, npm package validation, POSIX installer tests, PowerShell installer tests, and package builds on Linux and Windows.

## Verification boundaries

Static checks, installer simulations, and CI results do not prove that every coding-agent product discovers or activates RCoder. See `docs/HANDOFF.md` and `docs/RESEARCH-TODO.md` for verified evidence and remaining live-runtime checks.
