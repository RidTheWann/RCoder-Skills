# RCoder plugin and extension integration matrix

Updated: 2026-11-27. Product version is 1.16.0.

## Integration principles

- A portable Agent Skill and a host plugin/extension are different installation artifacts.
- Use each host's own manifest and launcher contract; do not copy one host's schema into another.
- MCP is kept on stdio by default. Plugin installation does not rewrite host MCP settings.
- Installer output distinguishes a copied file, a marketplace source, a native installation, and observed invocation. A successful CLI command is not automatically proof of model invocation.
- Node-to-Python launchers use an executable argument vector rather than a shell command string. The Python interpreter is selected per platform; set `RCODER_PYTHON` to override it.

## Host components

### OpenCode (dual V2/V1 adapter)

- Project skill: `.opencode/skills/rcoder/`
- Project plugin: `.opencode/plugins/rcoder.js`
- V2 hooks (observed on 2.4.2): `setup(ctx)` registers `ctx.session.hook('context')`, `ctx.session.hook('compaction')`, `ctx.tool.hook('execute.before'/'after')`, and `ctx.event.subscribe()`.
- V1 compatibility: `server(options)` retains `experimental.chat.system.transform`, `tool.execute.before`, `tool.execute.after`, and `experimental.session.compacting` for the older API.
- Runtime/RFC configuration: `<workspace>/.rcoder/opencode.json` or `<workspace>/.opencode/rcoder.json`; keys `runtime_disabled`, `rfc_disabled`, and absolute `runtime_path`. Env and configured plugin options are not forwarded by this host build.
- Installer: `rcoder integration install opencode --scope project`
- User scope uses `~/.config/opencode/skills/rcoder/` and `~/.config/opencode/plugins/rcoder.js`.
- `verify` checks that the plugin and skill files exist; it does not start OpenCode or prove the plugin loaded. Native evidence is recorded in `docs/OPENCODE-V2-ADAPTER.md`.
- Existing MCP configuration is untouched. Configure MCP separately with the MCP setup action.

The generated RScan V2 adapter remains a separate artifact and is not the target runtime for this plugin.

### Gemini CLI extension

The source tree contains `gemini-extension.json`, `GEMINI.md`, and namespaced TOML commands in `commands/rcoder/`. The extension manifest launches `launcher/rcoder-mcp.mjs` using the extension root and workspace root variables.

- Install: `gemini extensions install https://github.com/RidTheWann/RCoder-Skills`
- Update: `gemini extensions update rcoder`
- Remove: `gemini extensions uninstall rcoder`
- List/verify: `gemini extensions list`

The RCoder integration manager invokes those CLI commands. The host must be restarted after installation. Extension listing does not prove that a model invoked the skill or MCP tools.

### Codex plugin and marketplace

The repository root contains the portable Agent Plugins manifest and `mcp.json`. Compatibility metadata is also provided in `.codex-plugin/plugin.json` and `.mcp.json`. The Git marketplace source is recorded in `.agents/plugins/marketplace.json`.

- Add marketplace: `codex plugin marketplace add RidTheWann/RCoder-Skills`
- Upgrade marketplace: `codex plugin marketplace upgrade rcoder-skills`
- Remove marketplace: `codex plugin marketplace remove rcoder-skills`
- Then open `/plugins`, choose the `rcoder` plugin, and install it.

Marketplace registration and plugin installation are separate actions. The integration manager does not claim the plugin is active merely because the source was added.

### Claude Code plugin

The repository contains `.claude-plugin/plugin.json`, commands, agents, and a Claude-specific MCP config at `.claude-plugin/mcp.json`. The manifest references that file; its launcher path uses `${CLAUDE_PLUGIN_ROOT}` and its project root uses `${CLAUDE_PROJECT_DIR}`. The generic Codex/Agent Plugins compatibility file remains `.mcp.json` at the root. The marketplace entry uses a git source so the plugin resolves from both repository-hosted and URL-hosted catalogs.

Run from a shell or inside a Claude Code session:

```sh
claude plugin marketplace add RidTheWann/RCoder-Skills
claude plugin install rcoder@rcoder-skills
```

```text
/plugin marketplace add RidTheWann/RCoder-Skills
/plugin install rcoder@rcoder-skills
```

The integration manager prints these commands; it does not claim to execute an in-session plugin action. `claude plugin list` and `claude mcp list` are the local checks; native skill invocation by a model remains a separate gate.

## Shared stdio launcher

`launcher/rcoder-mcp.mjs` selects `python3`/ `python` on POSIX and `python`/ `py -3` on Windows, or uses `RCODER_PYTHON` when set. It launches the modern MCP server with inherited stdin/stdout/stderr so the host retains the standard stdio framing. HTTP transport is an optional separate process and is not selected by any plugin manifest.

## Evidence status

| Evidence | Status |
|---|---|
| JSON syntax and version parity | Enforced by `scripts/validate-all` and the CI manifest checks |
| Installer file behavior | Covered by isolated temporary-directory integration tests |
| Gemini/Codex CLI argument construction | Covered by dry-run tests; live host CLI installation depends on the user's installed host |
| OpenCode native loading and invocation of the dual adapter | VERIFIED on 2.4.2 only (`docs/OPENCODE-V2-ADAPTER.md`) |
| Gemini extension discovery/invocation | NOT VERIFIED |
| Codex plugin installation/invocation | NOT VERIFIED |
| Claude Code plugin install and MCP connection | VERIFIED locally with CLI 2.1.332: marketplace add, plugin install, `claude plugin list` enabled, `claude mcp list` → `✔ Connected` (`plugin:rcoder:rcoder`) |
| Claude Code skill/agent invocation by a model | NOT VERIFIED |
| Native MCP tool calls for all 39 tools over HTTP | NOT VERIFIED |
| Multilingual live routing accuracy | NOT VERIFIED |

The existing OpenCode 1.19.6 skill-discovery and RScan hook evidence predates this new adapter and must not be used as evidence for its activation. The 2.4.2 observation is version-scoped and does not raise the 1.19.6 row. CI can raise static/config evidence only; native-host claims require direct host observation.
