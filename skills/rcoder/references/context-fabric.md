# RFC Context Fabric

## Activate when
A long-running engineering task needs durable, source-aware context reintroduced across separate model requests or agent handoffs. Do not activate it for a one-shot task that fits safely in the current request.

## Mission and expertise
Own the local persistence and explicit rehydration of typed project context. Preserve provenance and delivery receipts while keeping the model-host boundary explicit. This module does not replace RCoder orchestration, RSaver reduction, or the existing episodic lesson store.

## Mental model
A model request has only the context actually supplied to that request. A database, content hash, retrieval index, or prior transcript does not create model memory by itself. Persistence becomes useful only when the caller assembles and injects a fresh payload for every request. Keep source facts, decisions, constraints, evidence, and unresolved hypotheses distinguishable.

## Prerequisites and reconnaissance
1. Confirm workspace root, active session identity, and local write permission before opening the store.
2. Inspect the existing RCoder capsule, repository instructions, and recent verified evidence.
3. Classify each item by kind, attach a source reference where available, and preserve confidence separately from verification status.
4. Use RSaver for model-token estimates, context reduction, and shared-output redaction; RFC budgets UTF-8 bytes only.

## Procedure
1. Store durable, sanitized context with ContextFabric.store_context(). Keep objective, constraint, decision, fact, evidence, unresolved, and next_action records distinct.
2. Use a stable session ID for one continuous task and a new prompt ID for every model call, including retries.
3. Call build_context(session_id, prompt_id, budget_bytes=...) before each request. Its returned text and payload hash describe the exact context assembled.
4. Inject that returned text into the actual model request. A build receipt without observed injection is not proof of model delivery.
5. Keep whole records only: the selector includes an item or excludes it; it must never silently truncate an item to fit.
6. When delivery confirmation is required, use a fresh single-use canary, verify the raw response with record_response(), then export only through export_transcript().
7. Run gc(now=...) with a fixed, explicit timestamp. Review the retention boundary and pinned records before collection.
8. Check the exported transcript, current store counters, and repository diff; record any host-level behaviour that was not observed as NOT VERIFIED.

## Decision tree
- Need durable notes across requests in one task -> store typed context and rehydrate by session/prompt identity.
- Need to reduce an oversized prompt or estimate provider-token cost -> use RSaver; do not treat RFC's byte budget as a tokenizer.
- Need proof that the model received a context payload -> inject it into the actual request and verify the response canary; a stored payload alone is insufficient.
- Need to share or publish logs -> redact with RSaver first and inspect the redacted copy.
- Need automatic host interception, MCP exposure, encryption, sync, or vector retrieval -> treat it as a separate implementation milestone; those capabilities are not present in this slice.

## Tool strategy
The local API is skills/rcoder/scripts/context_fabric.py and the repository wrapper is scripts/context-fabric.py. Store canary tokens in a private local file and pass a file path to the CLI; avoid command-line literals and shell history. The SQLite store is local and unencrypted. Keep .rcoder private, and do not rely on best-effort redaction as a complete secret detector.

## Advanced techniques
- Use content SHA-256 as a deduplication key for identical sanitized artifacts, not as proof that source evidence is true.
- Keep the selected item IDs and payload hash alongside the handoff so a later reviewer can identify exactly what was assembled.
- Prefer source-linked evidence and explicit confidence. Never promote an inferred statement to verified merely because it was persisted.
- For deterministic retention tests, create fixture expiry timestamps and evaluate GC against the same injected clock value.

## Failure modes
- A model appears to forget stored material -> the caller stored it but did not inject a fresh payload -> build and inject for the current prompt.
- A canary is rejected -> the delivery identity or token differs -> verify the session ID, prompt ID, and private token file used for that exact request.
- A transcript contains a canary -> response sanitization or export regressed -> block publication and add a regression test proving zero token occurrences.
- A boundary fixture changes outcome between runs -> test and GC use different clocks -> inject one fixed timestamp into fixture creation and the GC call.
- A context item disappears unexpectedly -> TTL or pinning policy was misclassified -> inspect expiry metadata and retain an explicit source-backed record.

## Quality checklist
- [ ] Every request has a unique prompt ID within its session, including retries.
- [ ] The actual request receives the exact payload whose SHA-256 receipt was recorded.
- [ ] Source, confidence, and kind remain visible for every selected context item.
- [ ] Canary acceptance is checked against the raw response; exported transcript contains zero token occurrences.
- [ ] GC uses an explicit clock and preserves pinned items.
- [ ] Unencrypted local storage and incomplete host integration are disclosed.

## Anti-patterns
- Treating a vector store, SQLite database, content hash, or summary as autonomous model memory.
- Reusing prompt IDs or canary tokens across requests.
- Exporting raw model transcripts or logging canary-bearing build output.
- Treating byte counts as exact model tokens or silently clipping evidence to meet a budget.
- Running GC against implicit wall-clock values in a deterministic boundary test.
- Claiming encryption, MCP exposure, synchronization, or automatic injection when these are not implemented.

## Verification
Run python scripts/test-context-fabric.py and python -m py_compile for the module, wrapper, and test. Exercise a CLI stats smoke test. Confirm B-5(a), B-7(b), A36, session/prompt replay resistance, secret masking, whole-item budget selection, and the inclusive expires_at <= now boundary. Run scripts/validate-all and the repository CI matrix; mark unrun checks NOT VERIFIED.

## Output format
Report the session/prompt identity, selected item IDs, payload hash and byte count, observed injection evidence, canary result, transcript-export result, GC timestamp and result, exact commands, and all remaining host or storage limitations.

## Executable Verification & Failure Diagnostics
- **Verify**: Run the focused RFC regression test, CLI smoke test, repository validator, and applicable CI jobs; inspect the final diff and confirm transcript export contains zero canary-token occurrences.
- **Anti-Patterns**: Do not infer model delivery from local persistence, treat byte counts as token counts, publish raw canary output, or claim unsupported host integration.
- **Failure Diagnostics**: A missing context item -> expired or unselected record -> inspect its source, priority, TTL, and byte budget; a canary mismatch -> wrong session/prompt/token association -> compare the exact delivery identity and protected token file; a GC boundary mismatch -> drifting clocks -> rerun with one injected timestamp.
