# Installation matrix

Official product docs reviewed 2026-11-23. Native runtime discovery is listed as unverified until tested in each product. OpenAI plugin packaging uses root `plugin.json`; `.codex-plugin/plugin.json` is retained as a compatibility fallback.

| Product | Project | User |
|---|---|---|
| Claude Code | `.claude/skills/rcoder/` | `~/.claude/skills/rcoder/` |
| Codex | `.agents/skills/rcoder/` | `~/.agents/skills/rcoder/` |
| Cursor | `.cursor/skills/rcoder/` | `~/.cursor/skills/rcoder/` |
| Gemini CLI | `.gemini/skills/rcoder/` | `~/.gemini/skills/rcoder/` |
| Copilot | `.github/skills/rcoder/` | `~/.copilot/skills/rcoder/` |
| Generic Agent Skills | `.agents/skills/rcoder/` | `~/.agents/skills/rcoder/` |

Installer options: `--target`, `--scope`, `--project-dir`, `--home-dir`, `--features`, `--list-features`, `--dry-run`, and `--uninstall`. Optional tools are RSaver (context pruning/budgeting/re-anchoring) and RScan (read-only project scan with development options); the selection is saved as `<target-root>/.rcoder-features.json`. Identical content is a no-op. Existing content is moved to `.rcoder-backups/` before replacement. Scripts install only the canonical skill folder; they do not modify application settings or fetch remote code.

## One-command entry points

- Node.js/npm: `npx -y github:RidTheWann/RCoder-Skills`
- PowerShell: `irm https://raw.githubusercontent.com/RidTheWann/RCoder-Skills/main/install.ps1 | iex`

Both commands default to the generic Agent Skills target and project scope. Pass `--target` and `--scope` to the Node CLI, or `-Target` and `-Scope` to the PowerShell bootstrap for a product-specific location. Both paths preserve existing RCoder content in `.rcoder-backups/`, are idempotent, and support dry-run/uninstall. The Node package requires Node.js 18.18+, npm, and Git. The PowerShell bootstrap downloads the repository archive over HTTPS into a temporary directory and removes it after installation.

The lower-level offline installers in `scripts/` remain available for cross-platform testing and offline development.


## Plugin and extension installation routes (2026-11-23)

These routes are distinct from copying a portable skill directory. The command manager validates file operations and invokes native CLIs where available; activation still requires a new host session and direct observation.

| Host | rcoder command | Host-side action |
|---|---|---|
| OpenCode | `rcoder integration install opencode --scope project` | Copies the skill and the dual V2/V1 plugin adapter to the project. Start a new OpenCode session. |
| Gemini CLI | `rcoder integration install gemini-cli` | Runs `gemini extensions install https://github.com/RidTheWann/RCoder-Skills`; restart Gemini CLI. |
| Codex | `rcoder integration install codex` | Adds the Git marketplace; open `/plugins` and install the RCoder plugin explicitly. |
| Claude Code | `rcoder integration install claude-code` | Prints `/plugin marketplace add` and `/plugin install` commands to run inside Claude Code. |

- [Gemini CLI extensions](https://google-gemini.github.io/gemini-cli/docs/extensions/index.html)
- [OpenAI Codex plugins](https://developers.openai.com/codex/plugins/)
- [Claude Code plugins](https://docs.anthropic.com/en/docs/claude-code/plugins)
- [OpenCode plugins](https://opencode.ai/docs/plugins/)

Host command construction and manifest tests are static integration evidence. T2 discovery, T3 invocation, and T4 behavioral evaluation for these new adapters remain NOT VERIFIED until observed in each native product.
