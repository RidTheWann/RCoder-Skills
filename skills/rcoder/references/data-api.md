# Data and API expert module

## Activate when
SQL/NoSQL persistence, schemas, migrations, endpoints, events, serialization, pagination, or external contracts.

## Mental model
Data and API surfaces are durable contracts. Consider compatibility, consistency, ownership, lifecycle, and failure behavior before changing fields.

## Procedure
1. Inspect schema/constraints/indexes, query paths, API spec, generated clients, and consumers.
2. Identify data owner, invariants, cardinality, sensitivity, retention, and access controls.
3. Define old/new reader-writer compatibility, defaults/nullability, ordering, pagination, and versioning.
4. Prefer expand → migrate → contract: add compatible structure, bounded backfill, switch readers/writers, then remove obsolete structure after evidence.
5. Make migrations bounded, observable, retry-safe, and reversible or document recovery.
6. Use parameterized queries, explicit transactions, appropriate isolation, and query timeouts.
7. Specify API errors, validation, idempotency, rate limits, pagination, timeouts, retries, and observability.
8. Test compatibility, partial failure, duplicates, concurrent updates, and representative data.

## Quality checklist
Schema invariants enforced; sensitive data identified; rollout works across deployed versions; backfill/retry/rollback bounded; consumers informed; large query plans measured.

## Anti-patterns
Destructive migrations too early; unbounded backfills/retries; unspecified row ordering; HTTP 2xx as proof of contract correctness.

## Verification
Use disposable databases, schema diff, contract tests, query plans, and concurrent/duplicate request tests. Never migrate production without explicit authorization.

## Output format
Schema/contract impact · compatibility plan · migration safety · tests · rollout/rollback · risks.
