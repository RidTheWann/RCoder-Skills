# Fixture: polyglot Go auth service

The repository contains `auth/session.go`, `auth/keys.go`, `migrations/`, and a Go test suite.
Sessions are signed with the active key from a keyring; PostgreSQL stores user and session rows.
The task requires key rotation with an overlap window, a reversible migration that keeps existing
sessions valid, and unchanged rejection of expired or revoked tokens. A disposable PostgreSQL
snapshot is available locally. Routing must choose one primary specialist plus at most two
addendums, and the agent must load only each addendum's `## Executable Verification & Failure
Diagnostics` section. Record the exact test and migration commands, the rollback path, and any
tokens or keys only as redacted placeholders.
