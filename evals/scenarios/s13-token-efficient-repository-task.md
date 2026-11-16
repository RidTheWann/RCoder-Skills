# S13 — Token-efficient repository task

## Fixture
A large polyglot monorepo has many packages, generated artifacts, and noisy CI logs. The requested API change touches one service and two clients.

## Expected evidence
- A bounded metadata-only context snapshot and concise repo state ledger.
- Exact reads of the affected schema, consumers, and tests rather than a whole-repository dump.
- Independent tasks delegated only when their file scopes do not overlap.
- Focused tests first, then broader verification according to risk.

## Failure signals
- Source files or full logs are dumped without a question.
- Multiple agents edit the same files concurrently.
- Security or regression checks are skipped only to reduce tokens.
- Final claims do not match recorded command output.
