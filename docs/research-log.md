# Research log

Access date: **2026-11-17**. Official product documentation was preferred. Community-only path evidence is labelled where native official sources were not available. Host documentation is mutable and must be rechecked before future path changes.

| Host / topic | Documentation | Relevant finding |
|---|---|---|
| Agent Skills format | [Specification](https://agentskills.io/specification) | `SKILL.md` with YAML frontmatter; required `name`/`description`; progressive disclosure through references and scripts. |
| Claude Code | [Skills](https://code.claude.com/docs/en/skills) | Project `.claude/skills` and user `~/.claude/skills`. |
| Codex | [Skills](https://developers.openai.com/codex/skills) | Project/user `.agents/skills` interoperable roots. |
| Cursor | [Agent Skills](https://cursor.com/docs/skills) | Project `.cursor/skills` and `.agents/skills`; user `~/.cursor/skills` and `.agents/skills`. |
| Gemini CLI | [Managing skills](https://geminicli.com/docs/cli/using-agent-skills/) | Project `.gemini/skills` and `.agents/skills`; user `~/.gemini/skills` and `.agents/skills`. |
| GitHub Copilot | [Agent skills](https://docs.github.com/en/copilot/concepts/customizations/agent-skills) | Project `.github/skills`; user `~/.copilot/skills`; compatibility roots vary by host surface. |
| Qoder | [CLI Skills](https://docs.qoder.com/cli/Skills) | Project `.qoder/skills`; user-level Qoder skills and `.agents/skills` discovery are documented. |
| OpenCode | [Skills](https://opencode.ai/docs/skills/) | Project `.opencode/skills`; global `~/.config/opencode/skills`; also reads compatible roots. |
| Antigravity | [Agent Skills](https://antigravity.google/docs/skills) | Project `.agents/skills`; user `~/.gemini/config/skills` on App/IDE surfaces. |
| Amp | [Skills](https://ampcode.com/docs/customize/skills) | Project `.agents/skills`; user `~/.config/agents/skills` and `.agents/skills`. |
| Zed | [Agent Skills](https://zed.dev/docs/ai/skills) | Project/user `.agents/skills`. |
| Pi | [Skills](https://docs.pi.dev/latest/skills) | Project `.agents/skills` and `.pi/skills`; user `.agents/skills` and `.pi/agent/skills`. |
| OpenClaw | [Skills](https://docs.openclaw.ai/tools/skills) | Workspace `.agents/skills`; personal `~/.agents/skills`; workspace-local `skills/` can have higher precedence. |
| Autohand | [Skills System](https://docs.autohand.ai/working-with-autohand-code/skills) | Project `.autohand/skills`; user `~/.autohand/skills`. |
| Warp | [Skills for agents](https://docs.warp.dev/agents/capabilities/skills) | Project `.warp/skills` and `.agents/skills`; global `~/.warp/skills` and `.agents/skills`. |
| Kilo Code | [Skills](https://kilo.ai/docs/customize/skills) | Project/user `.kilo/skills`; supports `.agents/skills` compatibility. |
| Cline | [Skills](https://github.com/cline/cline/blob/main/docs/customization/skills.mdx) | Project `.cline/skills`; user `~/.cline/skills`; `.claude/skills` compatibility. |
| Roo Code | [Skills](https://roocodeinc.github.io/Roo-Code/features/skills/) | Project/user `.roo/skills`; shared `.agents/skills` compatibility. |
| TRAE | [TRAE skills guidance](https://www.trae.ai/blog/trae_tutorial_0115) and [community path guide](https://github.com/trae-community/trae-skills) | Agent Skills support is described; `.trae/skills` and `~/.trae/skills` are community conventions and need current native verification. |
| Factory Droid | [Factory AI Skills examples](https://github.com/Factory-AI/skills) | Project `.factory/skills`; user `~/.factory/skills`. |

## Engineering and security references

- [OWASP ASVS](https://owasp.org/www-project-application-security-verification-standard/) — application-security control baseline.
- [OWASP WSTG](https://owasp.org/www-project-web-security-testing-guide/) — web-security testing methodology.
- [OWASP MASVS](https://mas.owasp.org/MASVS/) — mobile application security verification.
- [NIST SSDF](https://csrc.nist.gov/Projects/ssdf) — secure software development framework.
- [MITRE ATT&CK](https://attack.mitre.org/) — defensive behavior and incident-analysis knowledge base.
- [Agent Skills specification](https://agentskills.io/specification) — portable skill format and progressive-disclosure design.

## Research method

Inspect the repository and actual host surfaces first; prefer official current documentation; label community-only path evidence; test installer behavior; do not execute downloaded skill content as a second-stage installer; and mark native model activation NOT VERIFIED until tested in the corresponding product.
