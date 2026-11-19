# RSaver crosscheck and safe maximum compression

## Activate when
A model reports that an edit is complete; a task ends with a failure, timeout, or incomplete status; a user asks whether a failed run cost tokens or can be compensated; an agent is about to retry after a failure; or an oversized context must be reduced as far as safely possible. Do not activate to request or promise a refund, or to compress evidence that must stay human-readable without a recovery manifest.

## Mission and expertise
Verify claims against artifacts, record failure evidence with line references, and reduce token cost only under an explicit economics and recovery contract. Own the verdict, the evidence pack, and the honest billing boundary; do not own provider billing or support decisions.

## Mental model
A completion claim is a hypothesis until artifacts confirm it. RSaver is local and cannot change provider accounting; it can prevent avoidable spend and document what happened. Maximum compression is only useful when the reduced representation both costs fewer estimated tokens and can be restored exactly. A larger packed form is a failed optimization, not a success.

## Prerequisites and reconnaissance
1. Capture the observed diff, test output, completion claim, and provider usage JSON when available.
2. Define expectations: required files, forbidden paths, and success/failure markers.
3. Record the provider status field (`incomplete`, `refused`, `error`) if exposed.
4. Decide whether compression must preserve human-readable text or only exact recovery.

## Procedure
1. Run `rsaver crosscheck --expect <json> --diff <file> --test-log <file> --claim <file> --usage <json> --json`.
2. Read the verdict and each check's evidence lines; do not accept a claim that contradicts a failed check.
3. On `FAIL`, stop retry loops, fix the cause with the smallest change, and re-run crosscheck after the fix.
4. Give the user the evidence pack and state plainly that RSaver cannot zero or refund charges.
5. For large inert context, run `rsaver pack <file> --json`; use the packed form only when `worthwhile` is true.
6. Keep the manifest and verify exact restoration with `rsaver unpack --manifest <file> --out <path>` before discarding the original.

## Decision tree
- Required edit absent from diff → `FAIL`; do not claim success.
- Forbidden path present → `FAIL`; revert immediately and re-scope.
- Test log has failure markers → `FAIL`; fix before reporting.
- No success or failure markers → `UNVERIFIED`; run the narrowest test and record it.
- Completion claim with a failed check → `FAIL`; treat the claim as unsupported.
- Provider usage shows reasoning tokens on an empty answer → report the fact; do not invent a refund.
- Packed estimate lower and hash-verified roundtrip → use packed form; otherwise keep original.
- Human must read the text without unpacking → use `compact`/`dedupe`, not `pack`.

## Tool strategy
`python3 skills/rcoder/scripts/rsaver.py` provides `crosscheck`, `pack`, and `unpack` with the standard library only. Usage JSON is copied from the provider response; RSaver does not contact the provider. `pack` uses zlib level 9 plus base64, records original SHA-256 and both estimates, and `unpack` refuses to emit content when the restored hash differs.

## Advanced techniques
- **Evidence line numbers:** every check cites the exact line in the artifact, so a reviewer can reproduce the verdict.
- **Claim consistency:** a "done" statement is cross-checked against test and scope evidence, not trusted by itself.
- **Economics guard:** compression is accepted only when the estimate decreases; this avoids base64 inflation on short or high-entropy text.
- **Exact recovery:** unpack verification makes aggressive compression reversible without trusting the compressed payload.
- **Failure learning:** record verdict frequency per specialist and add recurring failures as scenarios in `evals/scenarios.json`.

## Failure modes
- **Claiming 0% billing** → false promise → state the provider boundary explicitly.
- **Assuming a failed call is free** → surprise charges → preserve usage evidence and reserve output headroom.
- **Accepting a claim without artifacts** → false completion → require diff and test evidence.
- **Using packed text without a manifest** → unrecoverable context → keep manifest and verify roundtrip.
- **Retrying the same failed edit** → repeated cost → stop, diagnose, and change one variable.

## Quality checklist
- [ ] Verdict is derived from artifacts, not from the model's claim.
- [ ] Each failed check has line-referenced evidence.
- [ ] Provider usage is reported as observed, with no compensation promise.
- [ ] Compression is used only when `worthwhile` and hash-verified restorable.
- [ ] A retry follows a diagnosis, not a repeat of the same action.

## Anti-patterns
Promising refunds; deleting usage records; treating a test log with no output as a pass; forcing packed output on short text; summarising a stack trace instead of preserving it; retrying until the window fills.

## Verification
Run `python3 scripts/test-rsaver.py`, which checks failure/pass verdicts, scope detection, usage copying, billing caveat, pack economics, and exact unpack restoration. Provider billing behavior must be confirmed from the provider's own documentation and usage dashboard.

## Output format
Verdict · check statuses with evidence lines · observed usage fields · billing caveat · compression estimates and recovery manifest · next action.
