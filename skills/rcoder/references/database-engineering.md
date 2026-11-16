# Database and data engineering

## Activate when
SQL/NoSQL schemas, migrations, query plans, transactions, indexing, ETL, or persistent data compatibility.

## Mental model
Data changes are state migrations with durability, concurrency, backward compatibility, privacy, and operational cost.

## Procedure
1. Identify engine/version, migration tool, isolation level, replication, backup/restore, and data-retention constraints.
2. Inspect schema, constraints, indexes, data volume, query plans, and access patterns.
3. Design expand-migrate-contract changes when old/new application versions coexist.
4. Make migration scripts idempotent or explicitly single-use; define rollback or forward-repair strategy.
5. Use parameterized queries, least-privilege identities, and deliberate transaction boundaries.
6. Check PII classification, retention, deletion, encryption, auditability, and export requirements.

## Quality checklist
- [ ] Migration is compatible with rolling deploys.
- [ ] Constraints preserve invariants under concurrency.
- [ ] Query plans are measured against representative volume.
- [ ] Backup/recovery impact is explicit.

## Anti-patterns
- Dropping/renaming columns in one incompatible deploy.
- Hiding N+1 queries with tiny fixtures.
- Assuming rollback can reverse destructive data changes.

## Verification
Run migrations against clean and prior-version fixtures, concurrency tests, query-plan checks, data-consistency tests, and recovery drills when relevant.

## Output format
Describe schema changes, migration order, locks/downtime, recovery, query measurements, and privacy.
