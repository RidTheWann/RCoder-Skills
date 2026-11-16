# Outstanding verification

These are environment-dependent checks, not incomplete implementation placeholders. The root Agent Plugins manifest and legacy `.codex-plugin` compatibility fallback are both included; confirm them against current product runtime when available.

| Item | Current blocker | Exact next verification |
|---|---|---|
| Official `skills-ref` | Not installed. | Install the current official validator and run `skills-ref validate skills/rcoder`; record version/output. |
| Claude plugin/marketplace | Claude CLI unavailable. | Run `claude plugin validate . --strict` (v2.1.289+ validates co-located marketplace + plugin manifests); add the GitHub repo as marketplace; install `rcoder@rcoder-skills`; inspect `claude plugin list` and `/plugin`. |
| Codex runtime | Codex unavailable. | Install to `$HOME/.agents/skills/rcoder`; inspect skill list/invocation; test root `plugin.json` and `.codex-plugin` compatibility fallback in the supported Codex plugin host. |
| Cursor | App/runtime unavailable. | Install under `.cursor/skills`; inspect Customize → Skills and invoke `/rcoder`. |
| Gemini CLI | CLI unavailable. | Run `gemini skills list --all`, activate RCoder in test workspace, and verify references. |
| Copilot | CLI/VS Code runtime unavailable. | Install `.github/skills/rcoder`; inspect skill list and tool activity in supported Copilot harness. |
| PowerShell | No local `pwsh` binary. | GitHub-hosted Windows CI run `43868447283` verified all 12 combinations and the current portable manifest/package changes. Re-run `scripts/test-installers.ps1` after future installer changes. |
| Live G2/G3 | No model runtime. | Run 24 triggers and 10 scenarios with same model/tools with and without RCoder; score using `evals/rubric.md`. |
| ZIP import UI | No authenticated product UI. | Upload `dist/rcoder-v1.0.0.skill.zip` in the intended surface and invoke in a clean session. |

| Remote CI execution | No GitHub Actions run observed yet. | Open the Actions tab after pushing and confirm all quality jobs pass. |
