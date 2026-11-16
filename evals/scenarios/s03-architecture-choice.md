# S03 — Architecture choice and ADR

## Fixture
A growing service needs deferred processing. Requirements include at-least-once delivery, modest initial volume, observability, and safe retry. Existing infrastructure includes a relational database but no broker.

## Task
Compare at least two viable designs (database-backed queue and managed/broker queue are credible candidates), rank quality attributes, select the smallest fit, and write an ADR before implementation.

## Required evidence
- Explicit requirements, constraints, and non-goals.
- Options with operational and failure-mode trade-offs.
- Chosen design, contracts, idempotency and retry behavior.
- ADR plus staged evolution path.
