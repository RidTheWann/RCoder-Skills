# RFC Context Fabric

## Activate when

A long-running engineering task needs durable, source-aware context to be reintroduced across separate model requests or agent handoffs. Do not activate for a one-shot task that fits safely in the current prompt.

## Responsibility boundary

- RCoder orchestrates the workflow and decides which facts should persist.
- RFC Context Fabric stores and rehydrates typed context for a specific request.
- RSaver measures, redacts, reduces, packs, recovers, and cross-checks context. Use RSaver for token-cost estimates; RFC's byte budget is not a tokenizer.
- The model has no implicit state between requests. A stored item is not memory until the caller builds and injects it into a fresh request.

## Required workflow

1. Use verified facts only. Keep objective, constraint, decision, fact, evidence, unresolved, and next_action distinct.
2. Store context with ContextFabric.store_context(). Source references and confidence should make provenance inspectable.
3. Call build_context(session_id, prompt_id, ...) for every model request. Use a new prompt ID every time, including retries. The returned payload is what must be injected into that request.
4. Use a byte budget deliberately. Records are included whole or excluded; do not imply that a UTF-8 byte budget is an exact token count.
5. For a canary-enabled delivery, provide a unique single-line ack_token. Verify the raw assistant response with record_response() using the same session ID, prompt ID, and token.
6. Export with export_transcript(). Never persist or publish the raw canary token. The exported transcript is expected to contain zero occurrences of it.
7. Run gc(now=...) only with an explicit timestamp. Expiry is inclusive at the boundary (expires_at <= now). Keep pinned items until explicitly unpinned or otherwise managed.

## Canary invariants

- The canary belongs to the composite (session_id, prompt_id) identity.
- The raw model response must contain the exact token to acknowledge the delivery (B-5(a)).
- The exported transcript must contain zero occurrences of the token (B-7(b), A36).
- A token is single-delivery and cannot be replayed for another prompt.
- The database retains only a SHA-256 digest, not the raw token.

## Security and data integrity

The local SQLite store is not encrypted. Keep .rcoder private and do not intentionally store credentials. Built-in secret masking is best-effort; use RSaver redaction before moving sensitive content into a shared context. Context item contents are preserved except LF normalization and credential-shaped redaction. Never claim a record is verified solely because it exists in the database.

## Current implementation boundary

The first RFC slice provides a Python API and local CLI. MCP exposure, automatic agent-host request interception, distributed sync, encrypted storage, and background collection are not implemented. If an API/CLI invocation or actual injection was not observed, mark delivery as NOT VERIFIED.
