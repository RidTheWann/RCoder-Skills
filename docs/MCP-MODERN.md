# RCoder MCP: stateless protocol and Skills over MCP

`skills/rcoder/scripts/rcoder_mcp_modern.py` is a dual-era entry point for the RCoder MCP server. It serves the stateless MCP revision `2026-07-28` and the Skills extension, and hands every legacy `initialize` session to the unchanged `rcoder_mcp.py` core. The legacy server file, its 21 tools, and `scripts/test-mcp.py` are not modified.

Nothing here is started by installing the skill. A host must be configured to launch the entry point.

## Run it

```sh
python3 skills/rcoder/scripts/rcoder_mcp_modern.py --root . --profile minimal
python3 skills/rcoder/scripts/rcoder_mcp_modern.py --print-config generic   # snippet points at this entry point
python3 scripts/test-mcp-modern.py
```

All options of `rcoder_mcp.py` (`--root`, `--profile`, `--tools`, `--print-config`, `--command`, `--version`) work unchanged. Existing host configurations keep working because they still launch `rcoder_mcp.py`; switch a configuration to the new file to opt in.

## How requests are routed

A request is modern only when `params._meta["io.modelcontextprotocol/protocolVersion"]` is present. Everything else, including `initialize`, notifications, and malformed lines, takes the legacy path unchanged. The two eras can interleave in one process.

| Behavior (modern requests only) | Detail |
|---|---|
| `server/discover` | Returns `supportedVersions: ["2026-07-28"]`, capabilities, `instructions`, and server identity in `_meta`. |
| Version check | Any other version returns `-32022` with `data.supported` and `data.requested`; a non-string version returns `-32602`. |
| `resultType` | Every result carries `"complete"`. |
| Identity | Every result carries `_meta["io.modelcontextprotocol/serverInfo"]`. |
| Cache hints | `tools/list`, `prompts/list`, `resources/list`, `resources/templates/list`, `resources/read`, `server/discover`, and the skills methods return `ttlMs` and `cacheScope` (`private`). |
| Removed methods | `ping`, `initialize`, `logging/setLevel`, `resources/subscribe`, and `resources/unsubscribe` return `-32601`. |
| Resource not found | `-32602` (legacy requests keep `-32002`). |
| Tools, prompts, completion | Delegated to the core with titles and `structuredContent` enabled; behavior and security model are identical to `docs/MCP.md`. |

Not implemented: `subscriptions/listen`, Multi Round-Trip Requests, the Tasks extension, MCP Apps, progress, and cancellation handling beyond ignoring the notification. The server never emits log notifications, which is correct for requests without `io.modelcontextprotocol/logLevel`.

## Skills over MCP

When `SKILL.md` can be exposed faithfully, `server/discover` advertises `io.modelcontextprotocol/skills` (with `directoryRead: false`) and the server implements:

- `skills/list` and `skills/get`: one entry, `skill://rcoder/SKILL.md`, with the frontmatter and a complete manifest of URI, SHA-256 digest, and byte size per file. The digest and size are computed from the exact bytes served, so line endings are preserved.
- `resources/read` for every URI in the manifest. Text is served as `text`; non-UTF-8 files are served as base64 `blob`.

The manifest covers `SKILL.md`, everything under `references/`, and everything under `assets/`. It excludes `scripts/` (executable code is exposed only as MCP tools), hidden files, credential-looking files, and symlinks. Reads are looked up by exact manifest URI, so `..` segments and unlisted paths return `-32602`. Project-local `.rcoder/references` overrides are never part of the skill manifest.

The frontmatter parser deliberately accepts only flat string fields plus one level of nested string maps, and refuses plain scalars that a YAML parser would type as numbers or booleans. If `SKILL.md` ever uses a construct outside that subset, the extension is not advertised and a message is written to stderr, instead of serving frontmatter that a host would fail to verify.

## Evidence status

| Claim | Status |
|---|---|
| Routing, discovery, version errors, cache fields, legacy non-regression, manifest digests recomputed from disk, hostile-URI refusal | Asserted by `scripts/test-mcp-modern.py`. Run against the full repository (2026-11-23): passes, alongside `scripts/test-mcp.py` and `scripts/validate-all`; also registered in CI. |
| Frontmatter parser agrees with PyYAML on `SKILL.md` | Asserted by the same test when PyYAML is installed. |
| Any host calls `server/discover`, `skills/list`, or `skills/get` against this server | NOT VERIFIED. The community support matrix lists Skills support only as partial for a few clients. Use `npx @modelcontextprotocol/inspector` or another client that implements the extension to check. |
| The Streamable HTTP transport | NOT IMPLEMENTED. Only stdio is served. |
| Claude Code plugin manifest (`.claude-plugin/plugin.json`) launches this entry point | DONE. Legacy `initialize` sessions still reach the unchanged core, so existing clients are unaffected (asserted by `scripts/test-mcp-modern.py`). `.codex-plugin` and `plugin.json` declare no MCP server. |

## Maintenance notes

- The adapter reaches into the core through its public names (`handle`, `State`, `RpcError`, `respond`, `process_line`, `main`, `render_config`, `SKILL_DIR`, `NAME_RE`, `is_sensitive`, `PROTOCOLS`, `SERVER_NAME`, `product_version`). Renaming any of them breaks the adapter; `scripts/test-mcp-modern.py` will fail loudly.
- `scripts/validate-all` should list `rcoder_mcp_modern.py` and `scripts/test-mcp-modern.py` wherever it enumerates scripts, and CI should run the new test next to `scripts/test-mcp.py`.
- When the legacy era is retired, fold the adapter into the core instead of keeping two entry points.
