# RFC — Context Fabric

RFC is RCoder's explicit, provenance-aware context persistence and request-hydration layer. It does **not** make a model stateful: every request receives only the context actually supplied to that request.

## Responsibilities

- **RCoder** owns engineering workflow, task orchestration, and deciding which durable facts should be recorded.
- **RSaver** measures context, performs safe reduction and redaction, and supports packing, recovery, and evidence cross-checking. RFC byte budgets are not provider-token counts.
- **RFC Context Fabric** persists typed context with provenance and assembles a new bounded payload for a specific session/prompt pair.
- **Host adapter** transports that payload into a model request and captures the corresponding response. It is the delivery boundary, not another source of model memory.
- **REPS2** may consume RFC through RCoder later. This implementation does not modify REPS2.

## Request lifecycle

1. Store sanitized context items with a stable session identity.
2. Receive a fresh host prompt event with a session ID and prompt ID.
3. Call build_context(session_id, prompt_id); every request and retry must have a new prompt ID.
4. Inject the returned payload into that exact request.
5. Capture the host's final assistant response and verify the canary against the same composite identity.
6. Export only through export_transcript(); the exported record contains no acknowledgement token.

A database, content hash, retrieval result, or payload receipt without step 4 is not evidence that the model received context.

## Local implementation

The standard-library implementation is skills/rcoder/scripts/context_fabric.py, with the repository CLI wrapper at scripts/context-fabric.py.

It provides:

- SQLite storage at .rcoder/context-fabric.sqlite3.
- SHA-256 content-addressed artifacts and deduplication.
- Typed records: objective, constraint, decision, fact, evidence, unresolved, and next_action.
- Source references, confidence, priority, pinning, and expiry metadata.
- Whole-item selection under a UTF-8 byte budget; records are included whole or excluded, never silently truncated.
- Payload receipts, session/prompt-bound unique canaries, token-free response export, best-effort credential-pattern redaction, and explicit-clock garbage collection.
- ensure_session(), so a host can register a session before any context item has been stored.

## Claude Code host injection

The first native host adapter is Claude Code: skills/rcoder/scripts/context_fabric_host.py.

The plugin manifest at hooks/hooks.json registers three events:

| Event | Adapter behavior |
|---|---|
| UserPromptSubmit | Reads session_id, prompt_id, and cwd; builds the fresh RFC payload; returns it through hookSpecificOutput.additionalContext. |
| Stop | Reads the same identity and last_assistant_message; verifies the per-delivery canary and stores a token-free transcript record. |

The adapter is deliberately opt-in. It does nothing unless .rcoder/context-fabric.sqlite3 already exists. Initialize the store once:

~~~sh
python scripts/context-fabric.py --root . stats
~~~

The first prompt then receives the session and prompt identifiers in its context header. Session-scoped items can be stored against that session:

~~~sh
python scripts/context-fabric.py --root . put --session SESSION_ID --kind objective --title "Active objective" --source README.md --file objective.md
~~~

The next prompt in that same Claude session will receive the selected item. The adapter creates one fresh canary per prompt in .rcoder/private/rfc-canaries, with restrictive directory/file permissions where supported. If the host omits prompt_id (which can occur before the first user input), RCoder creates a unique runtime prompt ID and stores a private session-to-delivery pointer until the corresponding Stop event. The raw token is not stored in SQLite; only its SHA-256 digest is stored there. The payload asks the model to append the marker as an HTML comment so it is not presented as ordinary prose. The token file remains available across repeated Stop events (for example, when a separate completion gate continues the turn). It is removed at the next UserPromptSubmit or SessionEnd; interrupted prompts are cleaned when a later prompt arrives.

The host hook is fail-open: malformed events, unavailable state, duplicate prompt identities, and internal errors do not block the prompt or stop event. Set RCODER_RFC_DISABLE=1 to disable RFC injection while leaving other RCoder hooks active; RCODER_HOOKS_DISABLE=1 disables all RCoder hooks. The default budget is 16,000 UTF-8 bytes. Use RSaver for token estimation and safe reduction.

## Canary acceptance and export

- **B-5(a):** the raw assistant response must contain the exact acknowledgement token for the matching (session_id, prompt_id).
- **B-7(b) and A36:** exported RFC transcripts must contain zero occurrences of that token.
- A canary is unique to one delivery. The adapter keeps the raw token only in a private local file until the corresponding Stop event.
- If the assistant response omits the marker, the response is still recorded but the delivery remains unacknowledged. The hook does not force the model to repeat or block the user's turn.

The canary is a delivery signal, not proof that every selected fact was understood or followed.

## Deterministic retention

A record with expires_at == now is eligible for collection (expires_at <= now). The caller must pass an explicit timestamp to gc(); test fixture creation and evaluation must use the same value. Pinned records are preserved.

## Usage and safety notes

- Run python scripts/test-context-fabric.py and python scripts/test-context-fabric-host.py for store and host-adapter regression coverage.
- stats reports local counters without exposing stored content.
- The SQLite database is unencrypted. The redactor is best-effort and does not guarantee detection of arbitrary sensitive data.
- Keep .rcoder/ private and do not deliberately store credentials.
- Native loading and invocation in a live Claude Code process remain **NOT VERIFIED** by the local simulator and CI. The runtime-generated ID fallback is covered by regression tests.
- Host adapters exist for Claude Code and for OpenCode 2.4.2 (dual V2/V1 plugin). The OpenCode bridge hydrates per model request, captures raw assistant text per step, and uses the same canary/export rules; see `docs/OPENCODE-V2-ADAPTER.md` for observed evidence. Gemini CLI, Codex, and other hosts are not implemented by this slice.
- MCP write tools, cross-device synchronization, encryption at rest, vector retrieval, and background GC are not implemented.
