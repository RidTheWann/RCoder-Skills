# RFC — Context Fabric

RFC is the Context Fabric development track for RCoder. Its purpose is to make durable project context available to an agent on every new request through an explicit, auditable handoff. It does **not** make a model stateful and does not treat a content-addressed store as memory by itself.

## Relationship to the existing projects

- **RCoder** owns the engineering workflow and orchestration: identify the active objective, decide what belongs in context, assemble a request, inject the payload, verify the response, and checkpoint the result.
- **RSaver** remains responsible for context measurement, safe reduction, redaction, lossless packing, recovery, and evidence cross-checking. RFC does not replace those functions or claim byte counts are model-token counts.
- **Context Fabric** persists provenance-aware context items and creates an explicit request payload for a specific (session_id, prompt_id) pair.
- **REPS2** can consume RFC through its RCoder workflow later. This first implementation does not change the REPS2 repository or introduce a project dependency on REPS2.

## The key model correction

A database, vector index, content hash, or retrieval result does not give the model persistent memory. Each model request starts with only the context actually supplied to that request. Therefore every request must perform this sequence:

1. Store or update verified context items in the local fabric.
2. Call build_context() with a unique session_id and a new prompt_id.
3. Inject the returned text into the actual model request. Merely storing or building it is not enough.
4. When a canary is enabled, verify the raw assistant response with record_response().
5. Use export_transcript() for the token-free exported record.

Reusing a (session_id, prompt_id) pair is rejected. A retry or subsequent model call must use a new prompt identity.

## First implementation slice

The implementation in skills/rcoder/scripts/context_fabric.py is a standard-library Python module with a local CLI wrapper at scripts/context-fabric.py.

It provides:

- SQLite storage under .rcoder/context-fabric.sqlite3.
- Content-addressed artifacts keyed by SHA-256, with deduplication across context items.
- Typed context records: objective, constraint, decision, fact, evidence, unresolved, and next_action.
- Deterministic priority/recency selection within a UTF-8 byte budget. Items are either included whole or excluded; they are never silently truncated.
- Explicit request hydration and a SHA-256 receipt for the assembled payload.
- Session-and-prompt-scoped canary verification, with globally unique canary tokens.
- Transcript storage and export that remove the exact canary before persistence. The raw canary is not stored; only its SHA-256 digest is retained for validation.
- Best-effort credential redaction before context and transcript persistence.
- Pinned records and deterministic expiry collection driven by an explicit timestamp.

### Canary acceptance errata

The final v0.2.3.5 review errata distinguish response verification from transcript export:

- **B-5(a):** the raw model response must contain the exact acknowledgement token for the delivery to be acknowledged.
- **B-7(b) and A36:** the exported transcript must contain zero occurrences of that acknowledgement token.

RFC checks the raw response before storage, strips every occurrence of the expected token, and exports only the token-free transcript plus an acknowledgement boolean. Canary identity is the composite (session_id, prompt_id), not either field alone. A token cannot be reused for another delivery.

### Deterministic GC boundary

A record with expires_at == now is eligible for collection (expires_at <= now). The caller must pass now explicitly to gc(), or --now to the CLI. GC never reads SQLite's implicit current clock. Tests construct expiry and comparison timestamps from the same fixed value, so test eligibility cannot drift with wall-clock seconds.

## Local usage

Store a verified item:

~~~sh
python scripts/context-fabric.py --root . put --session demo --kind objective --title "Project objective" --source README.md --file objective.md
~~~

Build a request payload. The canary token is read from a local file so it does not need to appear in shell arguments:

~~~sh
python scripts/context-fabric.py --root . build --session demo --prompt request-0001 --budget-bytes 12000 --ack-token-file .rcoder/private/canary.txt
~~~

The caller must inject the returned text into that exact model request. After receiving the response:

~~~sh
python scripts/context-fabric.py --root . ack --session demo --prompt request-0001 --token-file .rcoder/private/canary.txt --response-file response.txt
python scripts/context-fabric.py --root . export --session demo --prompt request-0001
~~~

Collect expired unpinned items using an explicit timestamp:

~~~sh
python scripts/context-fabric.py --root . gc --now 1795776000
~~~

stats reports local counters without exposing stored content. Context is stored locally and is not encrypted by RFC. The redactor is best-effort, not a guarantee that arbitrary sensitive data will be detected. Keep .rcoder private and never deliberately store credentials. Protect canary files and avoid logging the build output, because it contains the token intended for the model.

## Explicit limits of this slice

This is the first RFC implementation, not completion of the entire Context Fabric roadmap. It does not yet provide MCP tools, automatic host interception/injection, cross-device synchronization, encryption at rest, vector retrieval, or background GC. The caller is responsible for invoking the API/CLI and injecting each returned payload. The budget is in UTF-8 bytes, not provider tokens. RSaver remains the tool for estimating model-token cost and reducing context safely.

## Verification

scripts/test-context-fabric.py covers request hydration, composite canary identity, token-free transcript export (B-7(b)/A36), response-side canary acceptance (B-5(a)), unique canary use, secret redaction, no silent content truncation, and deterministic GC at the inclusive expiry boundary.
