# Outstanding verification

These are environment-dependent verification tasks, not implementation placeholders.

| Item | Current blocker | Exact next verification |
|---|---|---|
| Official `skills-ref` | Not installed. | Install the current official validator and run `skills-ref validate skills/rcoder`; record version and output. |
| Claude plugin/marketplace | Claude CLI unavailable. | Run `claude plugin validate . --strict`; add `RidTheWann/RCoder-Skills`; install `rcoder@rcoder-skills`; inspect `claude plugin list` and `/plugin`. |
| Codex runtime | Codex unavailable. | Install to `$HOME/.agents/skills/rcoder`; inspect skill discovery/invocation; test the root `plugin.json` and compatibility manifest in the supported plugin host. |
| Cursor | App/runtime unavailable. | Install under `.cursor/skills`; inspect Customize → Skills and invoke `/rcoder`. |
| Gemini CLI | CLI unavailable. | Run `gemini skills list --all`, activate RCoder in a test workspace, and verify reference loading. |
| Copilot | CLI/IDE runtime unavailable. | Install `.github/skills/rcoder`; inspect skill discovery and tool activity in a supported Copilot harness. |
| Native discovery | Product CLIs unavailable. | Test project and user installs in each target application; confirm task activation and selective reference loading. |
| Live G2/G3 | No model runtime in the build environment. | Run all 24 English trigger prompts and ten scenarios with identical model/tools/permissions with and without RCoder; score transcript and test evidence using `evals/rubric.md`. |
| ZIP import UI | No authenticated product UI. | Import `dist/rcoder-v1.1.0.skill.zip` or the portable plugin ZIP into the intended host and invoke RCoder in a clean session. |
| PowerShell bootstrap | No local PowerShell runtime. | Review and invoke `install.ps1` on a clean Windows project; test all six targets, both scopes, dry-run, backup, idempotence, uninstall, and failure recovery. |
| npm GitHub package | No network-dependent npx invocation in the local build environment. | Run `npx -y github:RidTheWann/RCoder-Skills --help` and a disposable install on a clean machine with Node, npm, and Git. |
