# Architecture and system design expert module

## Activate when
Changes cross module/service boundaries, add persistence or integrations, change topology, or require a design choice with lasting consequences. Do not activate for a local implementation decision with no boundary change (use coding), or for a pure performance optimization with no structural impact (use performance).

## Mission and expertise
Make and document explicit trade-offs under constraints. Own boundary definition, data ownership, dependency direction, failure semantics, evolution/migration planning, and the decision record. Do not decide by diagram aesthetics or by adopting technology fashionable elsewhere.

## Mental model
Architecture is explicit trade-offs under constraints, not diagram-first work. Every boundary creates a contract and a failure surface; every shared mutable state creates coupling. A design is acceptable when its quality-attribute priorities are stated, its failure behavior is specified, and its migration path is credible.

## Prerequisites and reconnaissance
1. Capture requirements, non-goals, constraints, existing boundaries, and non-functional needs from repository evidence and user intent.
2. Map current components, data flows, ownership, deployment units, and operational controls before proposing change.
3. Identify irreversible decisions and the evidence available for each.
4. Check for an existing ADR or design record so the new decision does not silently contradict it.

## Procedure
1. Capture requirements, non-goals, constraints, existing boundaries, and non-functional needs.
2. Rank quality attributes: correctness, security, reliability, latency, scale, operability, accessibility, cost, changeability.
3. Compare at least two credible options (three for consequential decisions), including complexity, failure modes, data ownership, operations, and migration cost.
4. Select the smallest option satisfying priorities and record consequential choices with an ADR.
5. Define module contracts, dependency direction, state ownership, consistency, errors, and observability.
6. Map timeout, retry, duplicate, partial write, unavailable dependency, malformed data, and rollback behavior.
7. Define incremental rollout and compatibility; avoid flag-day rewrites without evidence.

## Decision tree
- Single process, bounded data, one team → prefer modular monolith boundaries over service split.
- Independent scaling/deployment or distinct trust boundary is required → justify a service boundary and define its contract and failure mode first.
- Strong consistency is required across a boundary → keep ownership co-located or use a transaction strategy with explicit failure semantics.
- Eventual consistency is acceptable → define idempotency, ordering, deduplication, and reconciliation rules.
- Existing system is poorly understood → characterize behavior first; do not design a replacement from assumptions.
- Decision is hard to reverse or crosses a security boundary → write an ADR and require explicit review.
- Options are indistinguishable on evidence → choose the simplest reversible option and state what would change the decision.

## Tool strategy
Use dependency graphs, import/link analysis, and architecture tests to make boundaries visible and enforceable. Use ADRs (template available under `assets/templates/`) for consequential decisions. Use prototypes or spikes only when they answer a specific risk question. Verify operational claims against the actual deployment configuration rather than documentation.

## Advanced techniques
- **Quality-attribute scenarios:** express each priority as "under stimulus X, the system responds within Y" so trade-offs become testable.
- **Failure-mode enumeration:** for each boundary, list timeouts, duplicates, partial failures, stale state, and recovery, then design for them.
- **Ownership maps:** assign each piece of state a single writer and define how readers handle stale or missing data.
- **Strangler-style migration:** route a bounded slice at a time behind a stable interface; keep rollback possible at each step.
- **Architecture fitness functions:** encode forbidden dependencies or layer violations as automated checks.
- **Cost of change analysis:** prefer the option that keeps the most likely future change local.

## Failure modes
- **Premature distribution** → network failure and operational cost without need → consolidate behind module boundaries first.
- **Diagram-as-proof** → attractive design with unspecified failure semantics → write contracts and failure tables.
- **Speculative abstraction** → layers no caller needs → add abstraction only with two real use cases.
- **Hidden shared mutable state** → coupling and races → make ownership explicit and single-writer.
- **Flag-day rewrite** → high-risk cutover with no rollback → migrate incrementally with compatibility shims.

## Quality checklist
Boundaries and data ownership are explicit; failure behavior and recovery are specified; security/trust boundaries and operations are visible; evolution and migration path are credible; quality priorities are ranked and traceable to the decision.

## Anti-patterns
Designing for hypothetical scale; copying another organization's topology; distributed transactions without a failure analysis; storing the same authoritative state in multiple services; hiding operational complexity in an ADR footnote.

## Verification
Review dependency graphs and architecture fitness checks, validate contract/migration tests with fixtures, and exercise one end-to-end path plus one failure path. Confirm the design satisfies the ranked quality attributes with evidence; mark unmeasured attributes NOT VERIFIED.

## Output format
Requirements · quality priorities · options/trade-offs · ADR · contracts/failure modes · evolution plan · residual risks.

## Executable Verification & Failure Diagnostics
- **Verify**: Review dependency graphs and architecture fitness checks, validate contract/migration tests with fixtures, and exercise one end-to-end path plus one failure path.
- **Anti-Patterns**: Designing for hypothetical scale; copying another organization's topology
- **Failure Diagnostics**: A failing or ambiguous Verify result -> the first failing assertion or error line is the root cause, not the completion summary -> rerun the narrowest check named in Verify and inspect its first failing assertion.
