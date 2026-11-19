# Fixture: ambiguous conflicting requirements

The issue text says: "Make our product API the lowest latency possible while guaranteeing strong
consistency for every write across regions." The repository contains a single-node SQLite store and
no replication layer. There is no named cloud provider, budget, or consistency SLA. The user is
available only asynchronously. The task is to avoid premature implementation: identify the conflict
between latency and cross-region strong consistency, state reversible assumptions grounded in the
checked-out code, propose a staged plan with observable acceptance criteria for each stage, and
record which decision requires user confirmation before any irreversible change.
