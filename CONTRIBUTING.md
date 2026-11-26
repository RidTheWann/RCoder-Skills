# Contributing to RCoder

Thank you for improving RCoder. This repository is a portable engineering skill, so changes are judged on evidence, scope, and safety rather than size.

## Ground rules

- **English only.** All repository-managed instructions, references, templates, docs, prompts, and installer messages are English. Do not mix languages inside one artifact.
- **Smallest correct change.** Keep a pull request to one purpose. Do not refactor unrelated code.
- **Evidence over assertion.** Never claim a check passed unless you ran it and saw the result. Label statements VERIFIED, INFERRED, or NOT VERIFIED. Native host discovery and live model behavior stay NOT VERIFIED until observed.
- **No third-party runtime dependencies** in installers, helpers, or the MCP server. Use the standard library.
- **Least privilege.** Plugin subagents never get file-editing tools, the security reviewer has no shell, slash commands do not pre-approve tools, and bundled hooks stay local, bounded, and limited to the reviewed Claude lifecycle events (decisions D-018, D-019, D-021 in `docs/DECISIONS.md`).
- **Keep versions in sync.** A version bump must touch `skills/rcoder/SKILL.md`, `skills/rcoder/contracts/rcoder-v2.json`, `package.json`, `plugin.json`, `gemini-extension.json`, `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `.codex-plugin/plugin.json`, `scripts/package`, and `CHANGELOG.md` together. `scripts/validate-all` enforces this.

## Where things live

| Area | Path |
|---|---|
| Router and operating protocol | `skills/rcoder/SKILL.md` |
| Specialist modules (13-section template) | `skills/rcoder/references/` |
| Helpers and servers (Python, stdlib only) | `skills/rcoder/scripts/` |
| Claude Code commands and subagents | `commands/`, `agents/` |
| Bundled and opt-in hooks | `hooks/hooks.json`, `skills/rcoder/scripts/rcoder_hooks.py`, `docs/HOOKS.md` |
| Evaluation data and runs | `evals/` |
| Tests and validators | `scripts/` |

New specialists follow `skills/rcoder/references/domain-extension-guide.md`. Scaffold and lint a skill with `rcoder skill new`, `rcoder skill lint`, and `rcoder skill package`.

## Before you open a pull request

Run the gates that match your change; CI runs all of them on Linux and Windows (`.github/workflows/quality.yml`).

```sh
python3 scripts/validate-all
python3 scripts/test-hooks.py
python3 scripts/test-mcp.py
python3 scripts/test-rsaver.py
python3 scripts/test-rscan.py
node scripts/test-cli-skill.mjs
bash scripts/test-installers.sh
python3 scripts/package && python3 scripts/check-dist.py
```

Every new `scripts/test-*` file must be named in the workflow; a CI meta-check step fails otherwise. Add a `CHANGELOG.md` entry under `[Unreleased]`. If a change alters a documented decision, update `docs/DECISIONS.md` rather than editing an old entry silently.

## Reporting problems

Open an issue with the host, version, exact command, and observed output. For a suspected vulnerability, follow `SECURITY.md` instead of opening a public issue.

## License

By contributing you agree that your contribution is licensed under the MIT License in `LICENSE`.
