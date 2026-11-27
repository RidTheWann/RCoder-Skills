# RCoder Runtime

RCoder Runtime is the optional local control plane for RCoder Skills. It now provides project discovery, MCP process lifecycle tracking, and typed execution contracts with acceptance-evidence gates. It is not an autonomous agent, an MCP server replacement, or a permission bypass.

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

## Execution contracts and acceptance evidence

Runtime can persist a typed task contract separately from RFC context. Each contract contains an objective, numbered acceptance criteria, constraints, a risk level, state-transition history, and evidence attestations.

Create and activate a task:

```sh
rcoder-runtime task create --project . \
  --objective "Implement the requested feature" \
  --acceptance "Focused tests pass" \
  --acceptance "No unrelated files changed" \
  --constraint "Keep host permissions unchanged" \
  --risk high --json

rcoder-runtime task list --project .
rcoder-runtime task show --project . --id TASK_UUID
rcoder-runtime task transition --project . --id TASK_UUID --to active
rcoder-runtime task compile --project . --id TASK_UUID --json
```

After checking a criterion, record its outcome and a concise source reference:

```sh
rcoder-runtime task evidence --project . --id TASK_UUID \
  --criterion AC-001 --outcome pass \
  --summary "The focused test suite passed" \
  --source "cargo test -p runtime-core"
```

A task can move to `completed` only when the latest evidence for every acceptance criterion in the current verification cycle is `pass`. While a task is active, a later `fail` or `not-run` supersedes an earlier pass and blocks completion. Reopening a completed task to `active` with an explicit reason starts a new verification cycle: earlier evidence remains in the audit history but is excluded from the completion gate and instruction packet. Every acceptance criterion must receive fresh passing evidence before the reopened task can be completed again. Invalid state transitions are rejected; blocking and reopening require a reason. Evidence and transition histories are bounded to prevent unbounded ledger growth.

**Evidence boundary:** the Runtime validates contract structure, state transitions, and whether all criteria have a latest passing attestation. It does not independently execute the referenced command or prove the attestation is truthful. The future Verification Engine must cross-check evidence against actual test artifacts and repository state before stronger completion claims are made. The Task Controller does not intercept agent filesystem, shell, or IDE tools. Task inspection includes evidence and state-transition history. Never place credentials, API keys, private keys, or raw secret values in objectives, constraints, evidence summaries, or source references.

## Deterministic instruction packets

The Task Controller can compile an active contract into a bounded structured packet for a host to consume:

```sh
rcoder-runtime task compile --project . --id TASK_UUID --json
```

The compiler includes the objective, constraints, risk level, acceptance criteria, and only the latest evidence record for each criterion. It adds an explicit trust boundary stating that task fields are untrusted data and cannot override repository rules, system instructions, or host permissions. The packet carries a SHA-256 digest over its canonical serialized payload (excluding the digest field itself); the same task revision produces the same digest.

Compilation is permitted only while the task is `active`; draft, blocked, completed, and cancelled tasks are rejected. Packets larger than 64 KiB are rejected without truncation. This prevents a large contract from being silently clipped and changing its meaning.

**CLI boundary:** this command emits a candidate packet but does not itself inject it. The separate Claude Code `UserPromptSubmit` adapter described below consumes the packet and supplies it to eligible prompt requests. Other hosts require their own adapter. RFC remains responsible for durable cross-request context hydration, and Runtime does not read or write the RFC SQLite database.

## Claude Code per-request task injection

The packaged Claude Code hook manifest registers a separate `UserPromptSubmit` command for Runtime alongside the existing RFC Context Fabric adapter. On each prompt, `runtime_task_host.py` checks for an existing, non-symlinked task store and invokes:

```sh
rcoder-runtime task compile --project PROJECT_ROOT --active --json
```

When exactly one task is active, the hook returns the packet through `hookSpecificOutput.additionalContext`. The packet is therefore supplied on every eligible prompt/retry, while RFC continues to supply its independent durable context. The host combines `additionalContext` values returned by multiple hooks for the same event.

The hook is fail-open: no task store, no active task, multiple active tasks, an unavailable Runtime executable, invalid output, or a timeout yields no additional context and does not block the prompt. It does not create task directories. The Runtime child process receives only the OS environment allowlist and has sidecar startup disabled to prevent recursive attachment. The hook uses a fixed executable argument vector; task text never becomes shell input.

This initial injection adapter targets Claude Code's documented `UserPromptSubmit` event. Other hosts can consume `task compile --json` through their own adapters in later integration slices. Native hook activation in a live Claude Code session remains **NOT VERIFIED** until installed and observed.


## State and safety boundaries

Runtime stores session metadata in `.rcoder/runtime/sessions/` and task contracts/evidence in `.rcoder/runtime/tasks/`. Session records contain opaque session IDs, project paths, process IDs, process start times, lifecycle timestamps, and state. Task contracts contain the requested objective, acceptance criteria, constraints, risk level, state history, and caller-supplied evidence attestations. It does not copy MCP arguments, environment variables, prompts, context payloads, canaries, credentials, or tool output into session records. The launcher also passes the companion a small OS-environment allowlist (PATH, home/temp/system-root basics, and locale) instead of inheriting host API keys and provider tokens.

The runtime and sessions directories are restricted to the current user on Unix-like systems. Runtime refuses symlinked state directories and uses OS file locks to distinguish active sessions from abandoned records after a crash. Session records are local operational metadata, not proof that an agent completed work.

Runtime still does not enforce host tool permissions, compile a host-specific instruction payload, or independently verify caller-supplied evidence. Those capabilities remain separate roadmap stages. RFC remains the owner of durable request context and hydration; RSaver remains the context measurement and reduction subsystem. Runtime does not open or write the RFC SQLite database.

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
  |                                             Task Controller
  |                                                   |
  |                                             .rcoder/runtime/
  |                                               sessions/
  |                                               tasks/
  |
  +-- agent tools and permissions remain host-owned

RFC: durable context + per-request hydration
RSaver: context measurement, reduction, packing, and recovery
Runtime: local lifecycle/control-plane foundation
```

The OpenCode 2.4.2 V2 adapter is implemented: it reuses `runtime_task_host.py` to compile the active task packet into each model request, fails open when no valid active task or binary exists, and keeps task fields untrusted. A workspace `.rcoder/opencode.json` can set `runtime_disabled` or an absolute `runtime_path`; OpenCode does not forward plugin environment variables or caller `PATH`. Observed evidence is in `docs/OPENCODE-V2-ADAPTER.md`. Next stages are a Codex adapter, a fuller RFC/RSaver context bridge, a policy-aware Tool Gateway for operations actually routed through it, an independent evidence verifier, and finally the desktop console. The Rust workspace is intentionally headless first; a Tauri UI is deferred until the Runtime APIs are stable.
