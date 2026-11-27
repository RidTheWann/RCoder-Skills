# OpenCode V2 host adapter (RFC + Runtime)

This document records the observed contract and verification boundary for the
RCoder plugin in `.opencode/plugins/rcoder.js`. It does not extend claims to
other host versions or other hosts.

## Observed host contract (OpenCode 2.4.2)

The plugin exports a dual shape:

- V2: `{ id: 'rcoder', setup(ctx) }`, using `ctx.session.hook`, `ctx.tool.hook`,
  `ctx.event.subscribe`, and `ctx.session.hook('compaction')`.
- V1: `server(options)` returning the historical
  `experimental.chat.system.transform`, `tool.execute.before`,
  `tool.execute.after`, and `experimental.session.compacting` hooks.

Observed from the live 2.4.2 CLI and its installed type definitions:

- `ctx.session.hook('context')` runs **per model request**, including the
  continuation after a tool result. Its `system` parts are
  `{ type: 'text', text }` objects; appending a part was repeated verbatim by
  the answering model. This is the injection point for fresh RFC context and
  the active Runtime task packet.
- `ctx.tool.hook('execute.before'/'after')` receives `tool`, `input`, `status`,
  and `result` for live tool calls.
- `ctx.event.subscribe()` is server-wide, not workspace-scoped. Events include
  `session.step.started`, `session.text.ended`, `session.step.ended`,
  `session.execution.*`, and `session.deleted`. RCoder only records responses
  for sessions that received a delivery through this plugin instance.
- The plugin process environment is sanitized: `RCODER_*` variables and a
  caller-supplied `PATH` are not forwarded; only a host-defined `PATH`, `HOME`,
  and unrelated runtime variables are visible. Configured plugin `options`
  were observed as `{}` for an auto-discovered local plugin, so they cannot be
  the only configuration source.

## Payloads and ownership

One bounded JSON command is sent per model request to
`skills/rcoder/scripts/opencode_host.py`:

- `context`: calls the existing `runtime_task_host` validator/compiler and the
  existing RFC `build_context` helper. The outputs are independent; either can
  fail open without blocking the other.
- `response`: attributes raw assistant text to the exact delivery created for
  that model step, then records it through RFC. Raw canaries never enter
  SQLite; exported transcripts strip them.
- `cleanup`: removes private canary state on session deletion. Completion or
  repeated Stop-like events do **not** delete a live canary; age-based cleanup
  collects interrupted deliveries.

There is no second task engine and no second context store. Runtime owns task
contracts and the deterministic packet; RFC owns durable context, receipts,
and canaries; this bridge is transport glue only.

## Host configuration

Because env and plugin options are not reliably available in 2.4.2, the plugin
reads explicit workspace configuration from the first existing file:

1. `<workspace>/.rcoder/opencode.json`
2. `<workspace>/.opencode/rcoder.json`

Recognized keys: `runtime_disabled`, `rfc_disabled`, `runtime_path`. All are
optional; defaults are `false`, `false`, and `''`. A `runtime_path` must be
absolute or it is ignored. Values in `ctx.options`, when supplied, override the
file. The host bridge still sets `RCODER_RUNTIME_DISABLE=1` for the compiled
task child and uses the existing environment allowlist, so provider keys are
not inherited.

If no `runtime_path` is configured, Runtime injection requires a
`rcoder-runtime` executable on the host's plugin `PATH` (OpenCode replaces the
caller's `PATH`). A missing binary is fail-open.

For debugging only, an empty `.rcoder/opencode-no-optimize` file (or
`RCODER_OPENCODE_NO_OPTIMIZE=1` where env is forwarded) disables tool-output
redaction and RSaver compaction. It is opt-in and never affects RFC or Runtime
state.

## Canonical host state

`setupV2` builds one normalized state object through `createHostState()`. It
always contains `directory`, `hostOptions` (`runtimeDisabled`, `rfcDisabled`,
`runtimePath`), session tracking maps, and scan cache state. Every host payload
is produced by `hostPayload(state, extra)`, which re-normalizes the state
instead of assuming that `hostOptions` exists. This closes the lifecycle bug
where host configuration was defined but never stored by `setupV2`.

## Verification evidence (observed 2026-11-27)

All evidence below was observed locally on OpenCode **2.4.2** with the
`big-pickle` model. It is not a claim about hosted CI or another host build.

- **VERIFIED:** `context` fired twice in one session (initial request and the
  continuation after a tool call); a sentinel appended to `system` was echoed
  exactly by the model.
- **VERIFIED:** a seeded RFC delivery produced a canary in the live model
  response; the SQLite delivery became acknowledged; the raw token was absent
  from the SQLite bytes; the exported transcript contained zero raw-token
  occurrences.
- **VERIFIED:** an active Runtime packet injected from workspace configuration
  was reported by the model with its exact objective text.
- **VERIFIED:** `runtime_disabled: true` removed the Runtime packet while RFC
  injection still worked; `rfc_disabled: true` removed RFC injection.
- **VERIFIED:** the restored plugin loaded in fresh 2.4.2 processes and no
  `hostOptions` exception appeared in their run logs.
- **NOT VERIFIED:** Windows, macOS, Termux-native OpenCode on another build,
  hosted CI execution of the live model steps, provider retries of a single
  model request, and non-RCoder MCP servers as activation sources.

Regression coverage: `scripts/test-opencode-host.py`,
`scripts/test-opencode-v2-plugin.mjs`, and
`scripts/test-opencode-plugin-host-state.mjs`; all are registered in
`.github/workflows/quality.yml`.

### Native 2.4.2 end-to-end request delivery (VERIFIED)

`python3 scripts/test-opencode-native-e2e.py` starts the **installed OpenCode executable**
(`opencode run --standalone`) in an isolated workspace with isolated XDG config/data/state
directories, an OpenAI-compatible local mock provider, the real `.opencode/plugins/rcoder.js`,
and an RCoder MCP entrypoint. No public model API or real credential is used.

Observed with OpenCode 2.4.2 on aarch64 PRoot Debian 13:

- The host logged `loading plugin` for the isolated plugin path and invoked V2 `setup`.
- The host logged `mcp connected server=rcoder tools=...` with the isolated workspace directory.
- The mock provider captured the actual outgoing `/v1/chat/completions` body. A single system
  message contained both `RFC_E2E_MARKER_<id>` (inside the RFC payload with its `RFC-ACK` canary)
  and `RUNTIME_E2E_MARKER_<id>` (inside the compiled Runtime packet).
- All four independence configurations behaved correctly: each subsystem injected only when
  enabled; disabling one did not suppress the other; both disabled injected neither.
- Retries produced distinct RFC prompt identities/canaries; a session with no stored context
  produced no RFC delivery claim.
- A missing Runtime binary failed open for the packet adapter and produced no companion session;
  the MCP process with an invalid Runtime path also failed open without blocking routing.
- Direct MCP stdio JSON-RPC covered `initialize`, `notifications/initialized`, `tools/list`,
  and a real `tools/call`, with bounded stderr and a stopped companion bound to the fixture root.

Session IDs must start with `ses` in this build, and `PWD` must be set to the fixture root when
launching the host; both are enforced by the regression fixture. Live hosted-model behavior,
other OpenCode builds, and other platforms remain NOT VERIFIED.

### Artifact-backed Runtime summaries

The bridge remains transport glue. When an active task carries Runtime artifact
verification observations, the compiled packet includes a compact
`task.verifications` summary with the verifier state (for example
`artifact_verified`) beside the caller's declared outcome. The bridge neither
parses artifacts nor changes a caller claim into a verified result; RFC
hydration remains a separate payload. `scripts/test-opencode-host.py` asserts
that a strict passing report reaches the Runtime context with its structured
summary and that raw report content is not injected.
