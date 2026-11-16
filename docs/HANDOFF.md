# RCoder project handoff

## Delivered

`skills/rcoder/` is the canonical portable Agent Skill. It contains one workflow router, twelve core engineering expert modules plus a domain-extension guide, a read-only stack detector, six authoring templates, and optional OpenAI UI metadata. The repository also includes:

- A Node.js/npm installer exposed as the `rcoder` binary.
- A PowerShell bootstrap callable through `irm`.
- Legacy offline POSIX and PowerShell installers retained for local development and CI testing.
- A Claude Code plugin manifest, a portable root Agent Plugins manifest, and a Codex compatibility fallback.
- 24 English-only trigger prompts and ten behavioral scenarios with objective rubrics.
- A standard-library static validator, cross-platform CI, and a reproducible package builder.

Repository: https://github.com/RidTheWann/RCoder-Skills

## Fastest installation

### PowerShell

```powershell
irm https://raw.githubusercontent.com/RidTheWann/RCoder-Skills/main/install.ps1 | iex
```

Default: install to `.agents/skills/rcoder` in the current project.

Select a target or scope:

```powershell
& ([scriptblock]::Create((irm 'https://raw.githubusercontent.com/RidTheWann/RCoder-Skills/main/install.ps1'))) -Target codex -Scope user
```

### Node.js/npm

```sh
npx -y github:RidTheWann/RCoder-Skills
```

Target-specific example:

```sh
npx -y github:RidTheWann/RCoder-Skills --target claude-code --scope project
```

Node requirements: 18.18+, npm, and Git. The npm GitHub package spec retrieves the repository without publishing `rcoder` to the npm registry.

## Target and scope mapping

| Target | Project location | User location |
|---|---|---|
| Claude Code | `.claude/skills/rcoder` | `~/.claude/skills/rcoder` |
| Codex | `.agents/skills/rcoder` | `~/.agents/skills/rcoder` |
| Cursor | `.cursor/skills/rcoder` | `~/.cursor/skills/rcoder` |
| Gemini CLI | `.gemini/skills/rcoder` | `~/.gemini/skills/rcoder` |
| GitHub Copilot | `.github/skills/rcoder` | `~/.copilot/skills/rcoder` |
| Generic Agent Skills | `.agents/skills/rcoder` | `~/.agents/skills/rcoder` |

Targets: `claude-code`, `codex`, `cursor`, `gemini-cli`, `copilot`, `agents`. Scopes: `project`, `user`.

## Uninstall and safety

Node.js:

```sh
npx -y github:RidTheWann/RCoder-Skills --uninstall
```

PowerShell:

```powershell
& ([scriptblock]::Create((irm 'https://raw.githubusercontent.com/RidTheWann/RCoder-Skills/main/install.ps1'))) -Uninstall
```

Both installers are idempotent, support dry-run, preserve an existing installation before replacement, and restore the latest backup during uninstall. The PowerShell bootstrap downloads the repository archive over HTTPS into a temporary directory and removes it after installation. Review `install.ps1` before using the `irm` one-liner in environments that require manual script approval.

## Package commands

Build distributable archives locally:

```sh
python3 scripts/package
```

The builder creates:

- `dist/rcoder-v1.1.0.skill.zip`
- `dist/rcoder-v1.1.0.claude-plugin.zip`
- `dist/rcoder-v1.1.0.agent-plugin.zip`
- `dist/rcoder-v1.1.0.codex-plugin.zip`
- `dist/rcoder-v1.1.0-source.zip`
- `dist/SHA256SUMS`

Generated ZIP files and checksums are build artifacts and are not tracked in Git.

## Development and validation

```sh
python3 scripts/validate-all
node scripts/test-node-installer.mjs
npm pack --dry-run --json
bash scripts/test-installers.sh
python3 scripts/package
```

The PowerShell installer tests run on the Windows GitHub Actions runner. The Windows test suite covers all six targets and both scopes, including dry-run, backup, idempotent repeat, uninstall, and backup restoration.

## Quality-gate status

| Gate | Status | Evidence and limitation |
|---|---|---|
| G1 Structural | VERIFIED (static) | Standard-library validator checks skill metadata, structure, references, links, package metadata, and manifests. The official `skills-ref` validator remains a separate check. |
| G2 Trigger | VERIFIED (dataset only) | 24 prompts: 12 positive and 12 negative, all in English. Live model activation accuracy is NOT VERIFIED. |
| G3 Behavior | VERIFIED (scenario design) | Ten scenarios with objective rubrics and separate fixtures. Live with/without-skill model comparison is NOT VERIFIED. |
| G4 Installation | VERIFIED (simulations) | Node and POSIX installers tested on Linux; PowerShell installer tested on Windows CI. Native discovery in each host application remains NOT VERIFIED. |
| G5 Security and license | VERIFIED (static scope) | Selected secret/risky-command checks and MIT license are included. This is not a full security audit. |
| G6 Documentation | VERIFIED (static) | Repository docs, skill instructions, prompts, templates, and installer messages are English-only. |
| G7 Consistency | VERIFIED (static + remote tree + CI) | Local validation, package checks, GitHub tree readback, and cross-platform CI are recorded in the repository. |

## Remaining verification

The current build environment has Node 22, npm 10, Python 3.13, Git, and Linux x86-64. A local PowerShell runtime, `skills-ref`, and the native Claude Code, Codex, Cursor, Gemini CLI, and Copilot runtimes are not installed. Windows PowerShell behavior is covered by the GitHub-hosted Windows runner. See `docs/RESEARCH-TODO.md` for exact next steps.

## Maintenance rules

1. Keep all repository-managed text in English.
2. Update both the Node CLI and PowerShell bootstrap when target paths or backup behavior changes.
3. Keep project/user mappings synchronized in installers, tests, README, and this handoff.
4. Keep package/plugin/skill versions and the changelog synchronized.
5. Re-run all development checks and inspect the newest Linux and Windows CI results before release.
