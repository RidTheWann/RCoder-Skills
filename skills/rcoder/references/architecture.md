# Architecture and system design expert module

## Activate when
Changes cross module/service boundaries, add persistence/integrations, change topology, or require a design choice.

## Mental model
Architecture is explicit trade-offs under constraints, not diagram-first work.

## Procedure
1. Capture requirements, non-goals, constraints, existing boundaries, and non-functional needs.
2. Rank quality attributes: correctness, security, reliability, latency, scale, operability, accessibility, cost, changeability.
3. Compare at least two credible options (three for consequential decisions), including complexity, failure modes, data ownership, operations, and migration cost.
4. Select the smallest option satisfying priorities and record consequential choices with an ADR.
5. Define module contracts, dependency direction, state ownership, consistency, errors, and observability.
6. Map timeout, retry, duplicate, partial write, unavailable dependency, malformed data, and rollback behavior.
7. Define incremental rollout and compatibility; avoid flag-day rewrites without evidence.

## Quality checklist
Boundaries and data ownership are explicit; failure behavior and recovery are specified; security/trust boundaries and operations are visible; evolution and migration path are credible.

## Anti-patterns
Premature distribution; diagram-as-proof; speculative abstraction; hidden shared mutable state.

## Verification
Review dependency graphs, contract/migration tests, and one end-to-end plus one failure path.

## Output format
Requirements · quality priorities · options/trade-offs · ADR · contracts/failure modes · evolution plan.
