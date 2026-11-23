# RCoder plugin and extension integration matrix

Updated: 2026-11-23. Product version remains 1.14.0 during this development branch.

## Integration principles

- A portable Agent Skill and a host plugin/extension are different installation artifacts.
- Use each host's own manifest and launcher contract; do not copy one host's schema into another.
- MCP is kept on stdio by default. Plugin installation does not rewrite host MCP settings.
- Installer output distinguishes a copied file, a marketplace source, a native installation, and observed invocation. A successful CLI command is not automatically proof of model invocation.
- Node-to-Python launchers use an executable argument vector rather than a shell command string. The Python interpreter is selected per platform; set `RCODER_PYTHON` to override it.

## Host components

### OpenCode (V1 adapter)

- Project skill: `.opencode/skills/rcoder/`
- Project plugin: `.opencode/plugins/rcoder.js`
- Hook: `experimental.chat.system.transform`, aligned with the repository's observed OpenCode 1.19.6 V1 hook types.
- Installer: `RCoder integration install opencode --scope project`
- User scope uses `~/.config/opencode/skills/rcoder/` and `~/.config/opencode/plugins/rcoder.js`.
- `verify` checks that the plugin and skill files exist; it does not start OpenCode or prove the plugin loaded.
- Existing MCP configuration is untouched. Configure MCP separately with the MCP setup action.

V2 hooks are not emitted by this adapter. The generated RScan V2 adapter remains a separate artifact and is not treated as the target runtime.

### Gemini CLI extension

The source tree contains `gemini-extension.json`, `GEMINI.md`, and namespaced TOML commands in `commands/rcoder/`. The extension manifest launches `launcher/rcoder-mcp.mjs` using the extension root and workspace root variables.

- Install: `gemini extensions install https://github.com/RidTheWann/RCoder-Skills`
- Update: `gemini extensions update rcoder`
- Remove: `gemini extensions uninstall rcoder`
- List/verify: `gemini extensions list`

The RCoder integration manager invokes those CLI commands. The host must be restarted after installation. Extension listing does not prove that a model invoked the skill or MCP tools.

### Codex plugin and marketplace

The repository root contains the portable Agent Plugins manifest and `mcp.json`. Codex uses `.codex-plugin/plugin.json` plus `codex-mcp.json` (a direct server map); Claude Code uses `.claude-plugin/plugin.json` plus `claude-mcp.json` (an `mcpServers` wrapper). The Git marketplace source is recorded in `.agents/plugins/marketplace.json`.

- Add marketplace: `codex plugin marketplace add RidTheWann/RCoder-Skills`
- Upgrade marketplace: `codex plugin marketplace upgrade rcoder-skills`
- Remove marketplace: `codex plugin marketplace remove rcoder-skills`
- Then open `/plugins`, choose the `rcoder` plugin, and install it.

Marketplace registration and plugin installation are separate actions. The integration manager does not claim the plugin is active merely because the source was added.

### Claude Code plugin

The repository contains `.claude-plugin/plugin.json`, commands, agents, and a compatibility MCP config at `claude-mcp.json`. The plugin manifest references that file as a relative MCP server configuration.

Run inside a Claude Code session:

```text
/plugin marketplace add RidTheWann/RCoder-Skills
/plugin install rcoder@rcoder-skills
```

The integration manager prints these commands; it does not claim to execute an in-session plugin action. The repository retains the existing marketplace metadata for compatibility with the documented workflow; check the current host's marketplace guidance before a future public registry submission.

## Shared stdio launcher

`launcher/rcoder-mcp.mjs` selects `python3`/ `python` on POSIX and `python`/ `py -3` on Windows, or uses `RCODER_PYTHON` when set. It launches the modern MCP server with inherited stdin/stdout/stderr so the host retains the standard stdio framing. HTTP transport is an optional separate process and is not selected by any plugin manifest.

## Evidence status

| Evidence | Status |
|---|---|
| JSON syntax and version parity | Enforced by `scripts/validate-all` and the CI manifest checks |
| Installer file behavior | Covered by isolated temporary-directory integration tests |
| Gemini/Codex CLI argument construction | Covered by dry-run tests; live host CLI installation depends on the user's installed host |
| OpenCode native loading of the new adapter | NOT VERIFIED |
| Gemini extension discovery/invocation | NOT VERIFIED |
| Codex plugin installation/invocation | NOT VERIFIED |
| Claude Code plugin invocation | NOT VERIFIED |
| Native MCP tool calls for all 24 tools over HTTP | NOT VERIFIED |
| Multilingual live routing accuracy | NOT VERIFIED |

The existing OpenCode 1.19.6 skill-discovery and RScan hook evidence predates this new adapter and must not be used as evidence for its activation. CI can raise static/config evidence only; native-host claims require direct host observation.
