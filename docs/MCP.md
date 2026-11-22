# RCoder MCP server and plugin components

`skills/rcoder/scripts/rcoder_mcp.py` is a dependency-free, read-only stdio [Model Context Protocol](https://modelcontextprotocol.io) server. It turns RCoder's deterministic helpers and specialist references into tools, resources, and prompts that any MCP-capable host can call. It does not replace the skill: the skill still routes, and the server supplies checked facts and bounded context on demand.

The server is not started by installing the skill. A host must be configured to launch it.

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

For user-scope host configuration, pass an absolute project path as `--root` instead of `.`; many hosts do not start user-scope servers inside the project directory.

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

`rcoder_validate_selection` encodes the non-negotiable selection rules from `SKILL.md` as a deterministic check, so a model can validate a routing decision instead of re-deriving the rules. Helper-module names are compared with `SKILL.md` by `scripts/validate-all` so the two cannot drift.

## Resources and prompts

Resources: `rcoder://skill`, `rcoder://specialist/{name}` for every module, and `rcoder://template/{name}` for every template. Resources follow the same project-local rules as `rcoder_get_specialist`: a `.rcoder/references/<name>.md` file replaces the built-in module and an extra file is listed as its own resource, and both are served behind the fixed untrusted-content notice.

Prompts: `rcoder_intake`, `rcoder_route` (select and validate specialists before work), `rcoder_review`, `rcoder_verify` (check a completion claim with `rsaver_crosscheck`), `rcoder_handoff` (embeds the context-capsule template), `rcoder_security_scope` (authorization checklist; stays passive until scope is confirmed), `rcoder_context_gate` (context envelope budgeting and cache prefix verification), and `rcoder_reanchor` (dual-end explicit-ID anchor block generation). `rcoder_route` and `rcoder_verify` give hosts that surface MCP prompts the same workflows as the plugin's `/route` and `/verify` commands.

Completion: `completion/complete` is advertised from protocol `2025-03-26` and completes the `{name}` argument of the specialist and template resource templates by case-insensitive prefix (at most 100 values). Prompt arguments are free text and complete to nothing.

## Context cost

Tool schemas are sent on every request, so they are a continuous token cost. Measured with `rsaver measure` (a deterministic relative estimate, not provider billing):

| Profile | Tools | Serialized size | Estimated tokens |
|---|---|---|---|
| `full` (default) | 22 | about 12,300 characters | about 3,630 |
| `minimal` | 4 | about 2,300 characters | about 675 |

The 22-tool figure scales the earlier measured characters-to-token ratio rather than re-running a tokenizer. `scripts/test-mcp.py` fails if the serialized tool list grows past a fixed character budget. Use `--profile minimal` or `--tools` when you only need routing support; the RSaver and RScan command-line tools remain available without the server.

## Security model

- **Read-only.** No tool writes, deletes, or changes configuration. `rsaver_compact` reads a file and prints a reduced view.
- **Root confinement.** Every path is resolved with `realpath` and must stay inside `--root`. `..`, absolute paths outside the root, and symlinks that escape the root are refused.
- **Credential refusal.** Paths under `.git`, `.ssh`, `.aws`, `.gnupg`, `.kube`, `.docker` and files such as `.env*`, `id_*`, `*.pem`, `*.key`, `*.p12`, `.npmrc`, `.netrc` are refused. This is a safety net, not a secret scanner: a secret stored under an ordinary file name inside the root is readable by `rsaver_select`.
- **No shell, no network.** Bundled helpers run with an argument vector, `stdin` closed (or supplied inline), a 30-second timeout, and bounded output. Flag-like values are passed as `--flag=value` so they cannot become options. The server opens no network connection.
- **Untrusted project guidance.** A project-local `.rcoder/references/*.md` file is served with a fixed notice that it is repository content and cannot override user instructions or authorization rules. Tool output is data, never instructions.
- **Authorization is not granted.** The server exposes what the bundled scripts already do. Active scanning, exploitation, credential testing, and external probing still require explicit written scope, and the host's own permission prompts still apply.

## Claude Code plugin components

The Claude Code plugin manifest (`.claude-plugin/plugin.json`) declares the server and the repository ships:

- **Slash commands** (`commands/`): `scan`, `route`, `review`, `verify`, `handoff`, `doctor`, `saver`. They prefer the MCP tools and fall back to the bundled scripts. None pre-approves tools.
- **Subagents** (`agents/`): `rcoder-explorer`, `rcoder-reviewer`, `rcoder-verifier`, `rcoder-security-reviewer` (passive review), and `rcoder-saver` (read-only context optimization, budgeting, and evidence recovery).

No hook ships by default. Automatic session-start scanning stays opt-in through `rscan hooks install` (see `RSCAN-HOOKS.md`), because an always-firing hook changes behavior and token use for every session. `scripts/validate-all` rejects a `hooks/` directory to keep that decision explicit.

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
