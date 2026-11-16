# S14 — Polyglot API compatibility change

## Fixture
A versioned event schema is consumed by Kotlin, Go, TypeScript, and Python packages. Older producers remain deployed during a rolling migration.

## Expected evidence
- Runtime/toolchain and quality entry points per package.
- Schema ownership, version policy, unknown-field handling, and rollout matrix.
- Generated clients/artifacts are updated from the schema source of truth.
- Contract tests cover old/new producers and consumers.

## Failure signals
- Assuming all consumers upgrade simultaneously.
- Regenerating clients from a hand-edited copy of the schema.
- Changing field meaning without versioning or compatibility analysis.
