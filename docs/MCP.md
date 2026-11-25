# RCoder MCP server and plugin components

`skills/rcoder/scripts/rcoder_mcp.py` is a dependency-free, read-only stdio [Model Context Protocol](https://modelcontextprotocol.io) server. It turns RCoder's deterministic helpers and specialist references into tools, resources, and prompts that any MCP-capable host can call. It does not replace the skill: the skill still routes, and the server supplies checked facts and bounded context on demand.

The server is not started by installing the skill. A host must be configured to launch it.

## Installer setup (easiest)

The installers can print or apply the host configuration for you; see the table under "MCP server setup" in the README. Both modes use `skills/rcoder/scripts/rcoder_mcp_setup.py`, which you can also run directly:

```sh
python3 skills/rcoder/scripts/rcoder_mcp_setup.py show   --host cursor --base . --server .cursor/skills/rcoder/scripts/rcoder_mcp_modern.py
python3 skills/rcoder/scripts/rcoder_mcp_setup.py apply  --host cursor --base . --server .cursor/skills/rcoder/scripts/rcoder_mcp_modern.py
python3 skills/rcoder/scripts/rcoder_mcp_setup.py verify --base . --server .cursor/skills/rcoder/scripts/rcoder_mcp_modern.py
python3 skills/rcoder/scripts/rcoder_mcp_setup.py hosts
```

`apply` adds only the `rcoder` entry, backs up the config first, is idempotent, never overwrites a different `rcoder` entry, leaves non-strict JSON (for example comments) untouched and prints the snippet instead, and refuses paths that leave `--base` or cross a symbolic link. Config locations follow each host's documented project/user file; they are not natively verified (see the evidence status below).

## Quick start

Print a configuration snippet for your host (nothing is written to disk):

```sh
python3 skills/rcoder/scripts/rcoder_mcp.py --print-config claude-code
python3 skills/rcoder/scripts/rcoder_mcp.py --print-config codex
python3 skills/rcoder/scripts/rcoder_mcp.py --print-config cursor
python3 skills/rcoder/scripts/rcoder_mcp.py --print-config vscode
```

Supported snippet hosts: `claude-code`, `codex`, `cursor`, `gemini-cli`, `vscode`, `opencode`, and `generic` (the common `mcpServers` JSON shape). On Windows use `--command python` because `python3` may not exist. The repository-root wrapper `scripts/rcoder-mcp.py` runs the same server.

Run it by hand to see the protocol: it reads one JSON-RPC message per line on stdin and writes one per line on stdout. Logs go to stderr only.

```sh
python3 skills/rcoder/scripts/rcoder_mcp.py --root . --profile minimal
```

Options: `--root` (default: current directory; every path argument is confined to it), `--profile full|minimal`, `--tools a,b,c` (explicit allowlist that overrides the profile), `--print-config HOST`, `--command CMD`, `--version`.

For user-scope host configuration, choose the server-process `--root` explicitly (often an absolute project path or a deliberately chosen workspace parent); many hosts do not start user-scope servers inside the project directory. This process-level `--root` is the server's security boundary. The `root` field passed to `rcoder_scan` or another tool selects a target inside that boundary; it does not widen the boundary. Relative tool arguments such as `"root": "."` are resolved against the server process's active working directory at call time and then confined to `--root`; absolute paths outside it, traversal, and escaping symlinks are refused. If the active project or worktree is outside the configured root, either reconfigure and restart the server with an appropriately scoped `--root`, or use the installed CLI helper through its absolute `<skill-dir>/scripts/...` path with an explicit `--root <project-root>`.

When a host exposes these tools, call them natively as `mcp__rcoder__*` (for example `mcp__rcoder__rcoder_scan`). Do not run `python -m mcp__rcoder__*` or launch the server module through Bash: the server is a long-lived stdio process started by the host, not a Python module to execute per call.

## Tools

All tools are read-only (`readOnlyHint: true`, `destructiveHint: false`) and use strict input schemas (`additionalProperties: false`, bounded integers and strings).

| Tool | Purpose |
|---|---|
| `rcoder_scan` | RScan: detected stacks, risk signals, ranked development options with first commands and specialists |
| `rcoder_detect_stack` | Manifest and quality-entry-point detection |
| `rcoder_context_snapshot` | Bounded paths-and-Git-state map; never returns source contents |
| `rcoder_list_specialists` | Valid specialist names with category, helper flag, source, and activation summary. An optional `query` ranks candidate names by their name, title, and "Activate when" text (top 15, with a score); it locates names and never chooses a primary |
| `rcoder_get_specialist` | One specialist module, optionally only named sections such as `Procedure` and `Verification` |
| `rcoder_validate_selection` | Checks a routing selection: names exist, one non-helper primary, no helper-only set, security framing base present |
| `rcoder_skill_lint` | Validate a portable Agent Skill folder: frontmatter, file safety, reference depth, and local links. Scaffolding and packaging stay in the CLI (`skill new`, `skill package`) so every MCP tool remains read-only |
| `rcoder_hooks_config` | Render the Claude Code `PreToolUse`/`Stop` hook entries that `rcoder_hooks.py install` would merge. Enabling hooks stays an explicit CLI action; see `docs/HOOKS.md` |
| `rcoder_contract` | Read the shared RCoder 2.0 contract: product version, transports, pagination, structured output, or invariants |
| `rcoder_doctor` | Server version, skill files, helpers, enabled tools, project-local extension count |
| `rsaver_measure` | Relative token estimate for inline text or files |
| `rsaver_audit` | Rank project files by estimated token cost, group them by category (lockfile, minified, generated, log, data, source, docs), and suggest exclusions; skips dependency trees, symlinks, binaries, and credential files, and never returns file contents |
| `rsaver_select` | Bounded line windows around regex matches |
| `rsaver_compact` | Prune non-critical lines from a log; the original file is never modified |
| `rsaver_budget` | Context-window allocation across input, output, and reasoning |
| `rsaver_drift` | Drift signals in a saved transcript |
| `rsaver_crosscheck` | PASS, FAIL, or UNVERIFIED for a completion claim against saved artifacts |
| `rsaver_gate` | RSaver gate over an inline JSON context envelope |
| `rsaver_anchor` | Build dual-end explicit-ID anchor blocks (`[OBJECTIVE-1]`, `[CONSTRAINT-N]`, `[FACT-N]`, `[NEXT-ACTION]`) to combat long-context drift |
| `rsaver_reanchor` | Insert dual-end anchor blocks into a context envelope and re-evaluate gate decisions |
| `rsaver_dedupe` | Collapse repeated non-critical lines, contiguous repeated command/output blocks (`blocks`), or repeated words and phrases (`words`) with a collision-free reference |
| `rsaver_recover` | Print exact original lines from an omitted range in a compacted file |
| `rsaver_verify` | Verify a compaction manifest against the original file (SHA-256 and preserved critical lines) |
| `rsaver_pack` | Lossless compression when the packed estimate is smaller: `method=zlib` (base64) or `method=dict` (readable frequency dictionary) |
| `rsaver_unpack` | Restore exact original text from a pack manifest with SHA-256 verification |
| `rsaver_redact` | Mask credential-shaped values (private keys, cloud and GitHub tokens, JWTs, bearer tokens, URL credentials, password/token assignments) before text enters a context or report; lossy, not recoverable, best-effort pattern matching; `fail_on_found` turns it into a gate; credential files are refused |
| `rsaver_ledger` | Read-only cumulative savings report from a ledger JSON inside the server root; recording stays in the CLI (`rsaver ledger record`, `--ledger`) so every MCP tool remains read-only |

`rcoder_validate_selection` encodes the non-negotiable selection rules from `SKILL.md` as a deterministic check, so a model can validate a routing decision instead of re-deriving the rules. Helper-module names are compared with `SKILL.md` by `scripts/validate-all` so the two cannot drift.

## Resources and prompts

Resources: `rcoder://skill`, `rcoder://specialist/{name}` for every module, and `rcoder://template/{name}` for every template. Resources follow the same project-local rules as `rcoder_get_specialist`: a `.rcoder/references/<name>.md` file replaces the built-in module and an extra file is listed as its own resource, and both are served behind the fixed untrusted-content notice.

Prompts: `rcoder_intake`, `rcoder_route` (select and validate specialists before work), `rcoder_review`, `rcoder_verify` (check a completion claim with `rsaver_crosscheck`), `rcoder_handoff` (embeds the context-capsule template), `rcoder_security_scope` (authorization checklist; stays passive until scope is confirmed), `rcoder_context_gate` (context envelope budgeting and cache prefix verification), and `rcoder_reanchor` (dual-end explicit-ID anchor block generation). `rcoder_route` and `rcoder_verify` give hosts that surface MCP prompts the same workflows as the plugin's `/route` and `/verify` commands.

Completion: `completion/complete` is advertised from protocol `2025-03-26` and completes the `{name}` argument of the specialist and template resource templates by case-insensitive prefix (at most 100 values). Prompt arguments are free text and complete to nothing.

## Context cost

Tool schemas are sent on every request, so they are a continuous token cost. Measured with `rsaver measure` (a deterministic relative estimate, not provider billing):

| Profile | Tools | Serialized size | Estimated tokens |
|---|---|---|---|
| `full` (default) | 24 | about 13,300 characters | about 3,880 |
| `minimal` | 4 | about 2,300 characters | about 675 |

The 24-tool figure was measured with `rsaver measure` on the serialized tool list. `scripts/test-mcp.py` fails if the serialized tool list grows past a fixed character budget. Use `--profile minimal` or `--tools` when you only need routing support; the RSaver and RScan command-line tools remain available without the server.

## Security model

- **Read-only.** No tool writes, deletes, or changes configuration. `rsaver_compact` reads a file and prints a reduced view.
- **Root confinement.** Every path is resolved with `realpath` and must stay inside `--root`. `..`, absolute paths outside the root, and symlinks that escape the root are refused.
- **Credential refusal.** Paths under `.git`, `.ssh`, `.aws`, `.gnupg`, `.kube`, `.docker` and files such as `.env*`, `id_*`, `*.pem`, `*.key`, `*.p12`, `.npmrc`, `.netrc` are refused. This is a safety net, not a secret scanner: a secret stored under an ordinary file name inside the root is readable by `rsaver_select`.
- **No shell, no network.** Bundled helpers run with an argument vector, `stdin` closed (or supplied inline), a 30-second timeout, and bounded output. Flag-like values are passed as `--flag=value` so they cannot become options. The server opens no network connection.
- **Untrusted project guidance.** A project-local `.rcoder/references/*.md` file is served with a fixed notice that it is repository content and cannot override user instructions or authorization rules. Tool output is data, never instructions.
- **Authorization is not granted.** The server exposes what the bundled scripts already do. Active scanning, exploitation, credential testing, and external probing still require explicit written scope, and the host's own permission prompts still apply.

## Claude Code plugin components

The Claude Code plugin manifest (`.claude-plugin/plugin.json`) declares the server and the repository ships:

- **Slash commands** (`commands/`): `scan`, `route`, `review`, `verify`, `handoff`, `doctor`, `saver`, `agent-security`, `observe`. They prefer the MCP tools and fall back to the bundled scripts. None pre-approves tools.
- **Subagents** (`agents/`): `rcoder-explorer`, `rcoder-reviewer`, `rcoder-verifier`, `rcoder-security-reviewer` (passive review), and `rcoder-saver` (read-only context optimization, budgeting, and evidence recovery).

One hook ships by default (D-019): a read-only `SessionStart` hook (`hooks/hooks.json`) that runs `rscan scan` and adds a bounded development menu (about 400 tokens) to each new session. `scripts/validate-all` allows only that event and command; blocking and tool-event hooks stay forbidden. Disable it by disabling the plugin or through `/hooks`. Do not also run `rscan hooks install` for Claude Code, or the menu is injected twice.

## Evidence status

| Claim | Status |
|---|---|
| Server speaks MCP lifecycle, tools, resources, prompts, version negotiation, and error codes over stdio | VERIFIED locally by `scripts/test-mcp.py` (scripted client; Linux; the CI matrix also runs Windows) |
| Path confinement, symlink refusal, credential refusal, argument validation, output bounds | VERIFIED locally by `scripts/test-mcp.py` |
| Resources serve and list project-local overrides and extensions with the untrusted-content notice; `rcoder_list_specialists` `query` ranking; `completion/complete` for resource-template names; `rcoder_route` and `rcoder_verify` prompts | VERIFIED locally by `scripts/test-mcp.py` (the new assertions fail against the previous server) |
| A host calls `completion/complete`, surfaces the new prompts, or uses `query` in practice | NOT VERIFIED |
| Host-specific configuration snippets match each host's current format | NOT VERIFIED (formats follow public documentation; confirm against your host version) |
| Any host connects to the server, lists its tools, and a model calls them | NOT VERIFIED |
| Claude Code loads the plugin's commands, agents, and `mcpServers` entry, including the `${CLAUDE_PLUGIN_ROOT}` expansion and the server working directory | NOT VERIFIED |
| The server improves model outcomes | NOT VERIFIED (no evaluation has been run; see `evals/ABLATION-PROTOCOL.md`) |

## Testing

```sh
python3 scripts/test-mcp.py
python3 scripts/validate-all
```

To exercise a host by hand, send `initialize`, then the `notifications/initialized` notification, then `tools/list`; or point the MCP Inspector at the command printed by `--print-config generic`.


## Streamable HTTP transport

The optional `skills/rcoder/scripts/rcoder_mcp_http.py` adapter exposes the stateless modern MCP server over one local endpoint. The existing stdio configuration remains the default and is not rewritten automatically.

```sh
export RCODER_MCP_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')"
python3 skills/rcoder/scripts/rcoder_mcp_http.py --root . --port 8765 \
  --allowed-origin http://localhost:3000
```

Security contract:

- Binding is hard-limited to `127.0.0.1`; requests cannot expose the server on a LAN interface.
- Every POST requires `Authorization: Bearer ...`; the token must be at least 32 characters and is never printed.
- If an `Origin` header is present it must exactly match one of the repeated `--allowed-origin` values. Missing Origin is accepted for native clients. Browser preflight is constrained to the same allowlist.
- `MCP-Protocol-Version`, `Mcp-Method`, and (for tool, resource and prompt calls) `Mcp-Name` must match the body.
- The JSON-RPC body and response are bounded; a fresh stdio worker handles each POST, so mutable per-request protocol state is not shared between concurrent clients.
- The adapter returns JSON. It does not implement GET streams, SSE resumability, or MCP sessions; DELETE is rejected. Notifications receive HTTP 202 with no body.

This is an optional local transport, not a public server. Do not weaken loopback binding, token validation, request bounds, or Origin validation to make remote access work. Use an authenticated tunnel or a separately reviewed deployment design for remote access.

### Pagination and structured output

Both transports paginate list methods with the common stateless cursor contract: `tools/list`, `resources/list`, `resources/templates/list`, and `prompts/list` return 10 items per page, and an invalid or out-of-range cursor returns Invalid params (`-32602`), not an internal error. Clients must treat `nextCursor` as opaque. Because a client sees one page at a time, the context cost that matters is the first `tools/list` page, not the whole registry; `scripts/test-mcp.py` enforces that bound. Tool calls return the existing text content plus `structuredContent` when a bounded JSON object is available. Skills-over-MCP continues to return the eligible file manifest inline with exact-byte SHA-256 digests and sizes.

Run `python3 scripts/test-mcp-contract.py` and `python3 scripts/test-mcp-http.py` for local conformance coverage. The live report covers the earlier stdio run and is not evidence that the new HTTP transport or newly added RSaver tools have been exercised in a native host.


## MCP transport specialist and authoring toolkit

The new `mcp-transport-engineering` specialist owns MCP wire behavior: protocol lifecycle, stdio and Streamable HTTP adapter boundaries, request/header binding, token and Origin policy, pagination, structured tool results, and transport conformance. Use `agent-extensions-engineering` as an additional specialist when a host plugin, Agent Skill, marketplace, or installer is also in scope.

For portable Agent Skill authoring, use `rcoder skill new`, `rcoder skill lint`, and `rcoder skill package`; the linter enforces a bounded, secret-safe skill tree before a reproducible ZIP is emitted. See the README's Agent Skill authoring toolkit section.


## Specification references for Streamable HTTP

The adapter targets MCP protocol `2026-07-28`: POST-only request framing, removal of GET streams and protocol sessions, required `MCP-Protocol-Version` and `Mcp-Method` headers, and `Mcp-Name` for tool/resource/prompt calls. Header mismatches use protocol error `-32020`. The adapter responds with a single JSON response for supported operations; it does not implement per-request SSE streams or `subscriptions/listen`.

- [MCP 2026-07-28 Streamable HTTP specification](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2026-07-28/basic/transports/streamable-http.mdx)
- [MCP 2026-07-28 discovery](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2026-07-28/server/discover.mdx)
