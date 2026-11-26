# Database and data engineering

## Activate when
SQL/NoSQL schemas, migrations, query plans, transactions, indexing, ETL, or persistent data compatibility. Use data-api for API/schema contract design and database-specific engineering for the exact engine in the repository.

## Mission and expertise
Treat data changes as state migrations with durability, concurrency, compatibility, privacy, and operational cost. Own migration ordering, locking/downtime analysis, query measurement, and recovery planning.

## Mental model
Data changes are state migrations with durability, concurrency, backward compatibility, privacy, and operational cost. A rollback of application code does not reverse a destructive data change; recovery must be designed separately.

## Prerequisites and reconnaissance
1. Identify engine/version, migration tool, isolation level, replication, backup/restore, and data-retention constraints.
2. Inspect schema, constraints, indexes, data volume, query plans, and access patterns.
3. Determine which application versions are deployed and for how long.
4. Classify sensitive data and confirm retention, deletion, and audit requirements.

## Procedure
1. Identify engine/version, migration tool, isolation level, replication, backup/restore, and data-retention constraints.
2. Inspect schema, constraints, indexes, data volume, query plans, and access patterns.
3. Design expand-migrate-contract changes when old/new application versions coexist.
4. Make migration scripts idempotent or explicitly single-use; define rollback or forward-repair strategy.
5. Use parameterized queries, least-privilege identities, and deliberate transaction boundaries.
6. Check PII classification, retention, deletion, encryption, auditability, and export requirements.

## Decision tree
- Additive column → expand first with safe default; verify old writers still work.
- Rename/drop → expand → migrate → contract with a verified compatibility window.
- Bulk backfill → batch with progress, timeouts, and resumability; measure locks and IO.
- Query slow → inspect the query plan against representative volume before adding indexes.
- Concurrency anomaly → verify isolation level and transaction boundaries before adding locks.
- Sensitive data → minimize, encrypt, restrict access, and verify deletion/retention behavior.
- Migration is destructive → require explicit authorization and a tested recovery or forward-repair plan.

## Tool strategy
Use migration tooling, schema diff, query plan tools, database fixtures, and concurrency tests. Verify engine version from configuration, not memory. Run against disposable databases first; never test migrations directly on production data.

## Advanced techniques
- **Expand-migrate-contract:** split structure, data movement, and cleanup into separate reversible steps.
- **Representative volume fixtures:** generate data with realistic cardinality and distribution before measuring plans.
- **Lock budget:** record expected lock scope and duration for each migration step.
- **Consistency checks:** assert invariants after migration with queries that fail on partial data.
- **Recovery drill:** restore a prior-version backup and verify the application can run against it.
- **Index evidence:** add an index only when the query plan demonstrates the benefit and write cost is acceptable.

## Failure modes
- **Dropping/renaming columns in one incompatible deploy** → old versions break → use staged migration.
- **Hiding N+1 queries with tiny fixtures** → production latency → measure with representative data.
- **Assuming rollback can reverse destructive data changes** → unrecoverable loss → design forward repair.
- **Unbounded migrations** → timeouts and contention → batch and bound them.
- **Overprivileged database identity** → security risk → apply least privilege.

## Quality checklist
Migration is compatible with rolling deploys; constraints preserve invariants under concurrency; query plans are measured against representative volume; backup/recovery impact is explicit.

## Anti-patterns
Manual production schema edits; unbounded ETL; storing secrets in migration fixtures; disabling constraints to make a migration pass; skipping recovery verification.

## Verification
Run migrations against clean and prior-version fixtures, concurrency tests, query-plan checks, data-consistency tests, and recovery drills when relevant. Record exact engine versions and commands; mark untested environments NOT VERIFIED.

## Output format
Schema changes · migration order · locks/downtime · recovery · query measurements · privacy.

## Executable Verification & Failure Diagnostics
- **Verify**: Run migrations against clean and prior-version fixtures, concurrency tests, query-plan checks, data-consistency tests, and recovery drills when relevant.
- **Anti-Patterns**: Manual production schema edits; unbounded ETL
- **Failure Diagnostics**: A failing or ambiguous Verify result -> the first failing assertion or error line is the root cause, not the completion summary -> rerun the narrowest check named in Verify and inspect its first failing assertion.
