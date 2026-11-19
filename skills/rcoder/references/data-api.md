# Data and API expert module

## Activate when
SQL/NoSQL persistence, schemas, migrations, endpoints, events, serialization, pagination, or external contracts. Use database-engineering for engine-specific migration/query work and api-protocol-engineering for wire-level protocol design.

## Mission and expertise
Treat data and API surfaces as durable contracts. Own field-level compatibility, migration safety, validation, error semantics, pagination/ordering, and consumer impact across deployed versions.

## Mental model
Data and API surfaces are durable contracts. Consider compatibility, consistency, ownership, lifecycle, and failure behavior before changing fields. A 2xx response is not proof that the contract is correct; the shape, semantics, and error behavior matter.

## Prerequisites and reconnaissance
1. Inspect schema/constraints/indexes, query paths, API spec, generated clients, and consumers.
2. Identify data owner, invariants, cardinality, sensitivity, retention, and access controls.
3. Determine which application versions are deployed simultaneously and what compatibility window is required.
4. Check whether a migration has been run before and how it is tracked.

## Procedure
1. Inspect schema/constraints/indexes, query paths, API spec, generated clients, and consumers.
2. Identify data owner, invariants, cardinality, sensitivity, retention, and access controls.
3. Define old/new reader-writer compatibility, defaults/nullability, ordering, pagination, and versioning.
4. Prefer expand → migrate → contract: add compatible structure, bounded backfill, switch readers/writers, then remove obsolete structure after evidence.
5. Make migrations bounded, observable, retry-safe, and reversible or document recovery.
6. Use parameterized queries, explicit transactions, appropriate isolation, and query timeouts.
7. Specify API errors, validation, idempotency, rate limits, pagination, timeouts, retries, and observability.
8. Test compatibility, partial failure, duplicates, concurrent updates, and representative data.

## Decision tree
- Adding an optional field → expand first with a safe default; verify old readers tolerate it.
- Renaming or removing a field → expand → migrate → contract with an explicit deprecation window.
- Changing field meaning → treat as a breaking change and version the contract.
- Backfill required → bound batches, make retry-safe, and measure lock/IO impact.
- Pagination added → define stable ordering and cursor semantics; never rely on unordered results.
- Sensitive data involved → classify, minimize, encrypt, and constrain logging before release.
- Migration not reversible → require explicit authorization and a tested forward-repair path.

## Tool strategy
Use schema diffs, migration tooling, API specifications, generated-client checks, query plan tools, and disposable databases. Verify engine and client versions from manifests. Use contract tests to enforce producer/consumer compatibility and fuzz parsers for malformed payloads.

## Advanced techniques
- **Expand-migrate-contract:** separate structural addition, data migration, and removal into independently reversible stages.
- **Compatibility matrix:** test old/new combinations of producers, consumers, and schema versions.
- **Idempotency keys:** make retries safe for write endpoints and record outcomes for duplicate detection.
- **Bounded backfill:** process in small batches with progress, timeouts, and resumability.
- **Query plan evidence:** measure against representative data volume rather than tiny fixtures.
- **Error taxonomy:** define stable machine-readable error codes with documented retryability.

## Failure modes
- **Destructive migrations too early** → old versions break → delay removal until compatibility is verified.
- **Unbounded backfills/retries** → lock contention or timeouts → bound and observe them.
- **Unspecified row ordering** → unstable pagination → define a deterministic sort key.
- **HTTP 2xx as proof of contract correctness** → silent shape drift → validate schemas and semantics.
- **Sensitive data in logs** → privacy breach → redact at the boundary.

## Quality checklist
Schema invariants enforced; sensitive data identified; rollout works across deployed versions; backfill/retry/rollback bounded; consumers informed; large query plans measured.

## Anti-patterns
Mutable shared fixtures; silently dropping unknown fields; storing secrets in fixtures; changing defaults without consumer review; migrating production without authorization.

## Verification
Use disposable databases, schema diff, contract tests, query plans, and concurrent/duplicate request tests. Never migrate production without explicit authorization. Record exact commands and results.

## Output format
Schema/contract impact · compatibility plan · migration safety · tests · rollout/rollback · risks.
