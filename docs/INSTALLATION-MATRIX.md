# Installation matrix

Official product docs reviewed 2026-11-16. Native runtime discovery is listed as unverified until tested in each product.

| Product | Project | User |
|---|---|---|
| Claude Code | `.claude/skills/rcoder/` | `~/.claude/skills/rcoder/` |
| Codex | `.agents/skills/rcoder/` | `~/.agents/skills/rcoder/` |
| Cursor | `.cursor/skills/rcoder/` | `~/.cursor/skills/rcoder/` |
| Gemini CLI | `.gemini/skills/rcoder/` | `~/.gemini/skills/rcoder/` |
| Copilot | `.github/skills/rcoder/` | `~/.copilot/skills/rcoder/` |
| Generic Agent Skills | `.agents/skills/rcoder/` | `~/.agents/skills/rcoder/` |

Installer options: `--target`, `--scope`, `--project-dir`, `--home-dir`, `--dry-run`, and `--uninstall`. Identical content is a no-op. Existing content is moved to `.rcoder-backups/` before replacement. Scripts install only the canonical skill folder; they do not modify application settings or fetch remote code.
