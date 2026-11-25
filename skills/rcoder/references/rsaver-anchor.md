# RSaver anchor: re-anchoring a drifting context

## Activate when
A long session shows repeated tool calls, a restated or lost objective, missing constraints, a completion claim while unknowns remain, or a summary whose entries have no source. Also activate proactively at a resolved stage boundary, before compaction, and after resuming from a context capsule. Do not activate for a short prompt with no middle zone, or to repeat every instruction.

## Mission and expertise
Restore goal and constraint focus by restating a small set of high-priority items at the two high-attention ends of the next request, with explicit IDs and strict separation of observed facts, decisions, and unresolved hypotheses. Own the drift signal report, the bounded anchor block, and its budget impact; do not own the plan repair or evidence recovery.

## Mental model
Attention is not uniform: early and late positions receive more attention than the middle. A critical instruction stated once in the middle sits in the weakest zone. Restating the objective and hard constraints at both ends targets primacy and recency without flooding the window. Models do not reliably follow relative position instructions such as "the middle section", so use explicit IDs. Structural boundary tokens are load-bearing: preserve them when pruning. Drift signals are text heuristics, not a diagnosis of model state.

## Prerequisites and reconnaissance
1. Capture the current state in a JSON object: objective, at most three hard constraints, verified facts with evidence, decisions, unresolved items, security boundary, and immediate next action.
2. If available, scan the recent transcript with `drift` to identify which items have been lost or contradicted.
3. Confirm the remaining input budget with `budget`/`gate`; an anchor that displaces required evidence is not acceptable.
4. Verify each "verified fact" has a source. Unsourced reasoning must be labeled as a decision or unresolved hypothesis.

## Procedure
1. Run `python3 scripts/rsaver.py drift <transcript> --json` when a transcript file exists; review signal line numbers.
2. Build the state JSON with explicit, source-backed entries.
3. Run `python3 scripts/rsaver.py anchor state.json --max-tokens 400 --json` to get an opening block, a closing block, and their explicit IDs.
4. Check warnings: `anchor_exceeds_budget` or `too_many_repeated_constraints` means reduce or merge entries.
5. Use `reanchor --envelope envelope.json --state state.json` to insert both blocks and re-run the gate budget before the next request.
6. In the next prompt, refer to items by ID (for example "apply [DECISION-1]") rather than by position.
7. After the response, reconcile the anchor claims with new evidence and update the state file; do not reuse a stale anchor.

## Decision tree
- Objective missing from the recent window → re-anchor at both ends with `[OBJECTIVE-1]`.
- Constraint missing or rewritten → restate the exact constraint; do not paraphrase it differently at the two ends.
- Repeated identical command → stop looping, record the result, and set a new `[NEXT-ACTION]`.
- Completion claim with open unknowns → downgrade the claim and list each `[UNRESOLVED-n]` with the observation that would close it.
- Summary entry without source → move it from facts to decisions or unresolved; never promote it to a verified fact.
- Prompt is short → skip the anchor; duplication adds noise without a middle zone.
- More than three hard constraints → choose the truly critical ones; repetition of everything conveys no priority.
- Anchor exceeds budget → shorten by dropping low-value facts, never by dropping the objective, constraints, or security boundary.

## Tool strategy
`python3 <skill-dir>/scripts/rsaver.py` provides `drift`, `anchor`, and `reanchor`. State and envelope files are JSON; `-` reads state from stdin. All output can be requested with `--json` for deterministic tests and ledger capture. The drift detector uses the standard library only; it counts line-based signals and never inspects model internals.

## Advanced techniques
- **Bilateral anchoring:** identical objective and constraint text at both ends; the closing block exploits recency while the opening block exploits primacy.
- **ID-based reference:** absolute identifiers avoid reliance on relative position awareness.
- **Source-judged facts:** each fact entry includes the evidence path, command, or artifact; inferred decisions use a different prefix.
- **Stage-boundary re-anchoring:** do it when a stage is resolved, not only when the window is full.
- **Signal trend:** record signal counts per step; a rising repeated-command count is an early warning of a tool loop.
- **Budget reconciliation:** compare the anchor estimate plus projected total with observed usage after the response.

## Failure modes
- **Repeating everything** → no priority signal → repeat only objective, constraints, and next action.
- **Contradictory restatements** → the model treats them as conflicting rules → copy the exact text at both ends.
- **Unsourced summary entry treated as fact** → rewritten constraints or invented deliverables → source-judge every fact.
- **Anchor displaces evidence** → required items deferred → reduce anchor size or raise budget.
- **Drift signal treated as proof** → false diagnosis → label signals NOT VERIFIED and corroborate with transcript evidence.

## Quality checklist
- [ ] Objective and hard constraints appear at both ends with identical wording.
- [ ] Items carry explicit IDs and facts are separated from decisions and unresolved items.
- [ ] Security boundary is present and no required evidence was deferred.
- [ ] Anchor estimate fits the budget and warnings are resolved.
- [ ] Drift signals are recorded with line numbers and labeled heuristic.

## Anti-patterns
Re-anchoring every turn regardless of need; paraphrasing constraints; claiming an unsourced decision is verified; using positional prose such as "see the earlier section"; treating a clean drift scan as proof of coherence.

## Verification
Run `python3 scripts/test-rsaver.py`, which checks drift signals, dual-end structure, explicit IDs, budget warnings, and rejection paths. For a live session, retain the drift report, anchor state, gate output, and response usage; score with `evals/rubric.md` before claiming improvement.

## Output format
Drift signals with line numbers · anchor IDs and estimate · warnings · changed state entries · budget impact · evidence labels · residual uncertainty.
