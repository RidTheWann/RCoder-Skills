# RCoder Runtime

RCoder Runtime is the optional local control-plane companion for RCoder Skills. The first release slice focuses on project discovery and MCP session lifecycle; it is not an autonomous agent, an MCP server replacement, or a permission bypass.

## Activation model

The local Python RCoder MCP stdio server and loopback Streamable HTTP service are activation points:

1. The host starts the configured local RCoder MCP process.
2. The Node launcher forwards `RCODER_WORKSPACE_ROOT`; the MCP server uses it as the default `--root` (an explicit `--root` argument still takes precedence).
3. The MCP process looks for `rcoder-runtime` on `PATH`, or at the explicit `RCODER_RUNTIME_PATH`.
4. When the executable is available, the MCP process starts a detached companion with its own process group.
5. The companion records a session under `.rcoder/runtime/sessions/` and watches the MCP process identity, including its process start time.
6. When that exact MCP process exits, the companion records a stopped session and releases its lock.

This makes Runtime active for the lifetime of an actual local RCoder MCP process. The HTTP service owns one companion for its whole lifetime; its one-request worker subprocesses explicitly disable attachment. It does not activate merely because a repository contains an MCP configuration, and it does not start for unrelated MCP servers such as Serena. A remote RCoder MCP endpoint cannot launch a local companion.

If Runtime is not installed, cannot start, or is explicitly disabled, the MCP server continues normally. Runtime startup never writes to MCP stdout and is deliberately fail-open.

## Install

Install Rust 1.85 or newer, then build and install the executable from the repository root:

```sh
cargo install --path runtime/apps/rcoder-runtime
rcoder-runtime detect --project .
rcoder-runtime status --project .
```

On Windows, the installed executable is `rcoder-runtime.exe`. Ensure Cargo's binary directory is on `PATH`.

Environment controls:

- `RCODER_RUNTIME_PATH`: explicit path to the Runtime executable when it is not on `PATH`.
- `RCODER_RUNTIME_DISABLE=1`: disable companion startup for this MCP process.
- `RCODER_RUNTIME_DEBUG=1`: emit a generic startup-failure notice to stderr; never to protocol stdout.

## Commands

- `rcoder-runtime detect --project PATH` inspects supported project-local JSON manifests: `.mcp.json`, `mcp.json`, `.vscode/mcp.json`, `.cursor/mcp.json`, `.windsurf/mcp_config.json`, and OpenCode's `opencode.json` forms.
- `rcoder-runtime status --project PATH` reports active, stopped, and orphaned session records.
- The internal `attach` command is started by RCoder MCP and is not intended for manual use.

Detection inspects the configured command, executable, module, and argument fields for the exact bundled RCoder MCP entry points (`rcoder_mcp.py`, `rcoder_mcp_modern.py`, `rcoder-mcp`, or the Node `rcoder-mcp.mjs` launcher). A server merely named `rcoder` is not sufficient evidence. Unrelated MCP servers are ignored. JSONC, TOML, global user-level manifests, and remote endpoint lifecycle are not detected by this initial slice.

## State and safety boundaries

Runtime stores only session metadata in `.rcoder/runtime/sessions/`: opaque session ID, project path, process IDs, process start time, lifecycle timestamps, and state. It does not copy MCP arguments, environment variables, prompts, context payloads, canaries, credentials, or tool output into session records. The launcher also passes the companion a small OS-environment allowlist (PATH, home/temp/system-root basics, and locale) instead of inheriting host API keys and provider tokens.

The runtime and sessions directories are restricted to the current user on Unix-like systems. Runtime refuses symlinked state directories and uses OS file locks to distinguish active sessions from abandoned records after a crash. Session records are local operational metadata, not proof that an agent completed work.

This slice does not yet enforce tool permissions, compile task instructions, or validate acceptance criteria. Those capabilities remain separate roadmap stages. RFC remains the owner of durable request context and hydration; RSaver remains the context measurement and reduction subsystem. Runtime does not open or write the RFC SQLite database.

## Architecture and next stages

```text
Agent host
  |
  +-- local RCoder MCP process ----------------------+
  |                                                   |
  |                                             Runtime bootstrap
  |                                                   |
  |                                             rcoder-runtime
  |                                                   |
  |                                             session controller
  |                                                   |
  |                                             .rcoder/runtime/
  |
  +-- agent tools and permissions remain host-owned

RFC: durable context + per-request hydration
RSaver: context measurement, reduction, packing, and recovery
Runtime: local lifecycle/control-plane foundation
```

Next stages are the execution contract and instruction compiler, RFC/RSaver context bridge, policy-aware tool gateway, evidence verifier, and finally the desktop console. The Rust workspace is intentionally headless first; a Tauri UI is deferred until the Runtime APIs are stable.
