# S10 — Backward-compatible API migration

## Fixture
A required account status field must be added to an API and database while older application versions remain deployed. A large table needs backfill.

## Task
Inventory consumers and version compatibility, design staged migration, bound backfill and retries, and test partial failure/rollback before production approval.

## Required evidence
- Old/new readers and writers plus compatibility window.
- Expand/migrate/contract sequence or equivalent.
- Idempotent bounded backfill, progress tracking, and failure recovery.
- Contract/migration tests for missing, invalid, duplicate, and legacy values.
