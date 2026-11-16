# Distributed systems and event-driven engineering

## Activate when
Multi-service coordination, distributed locks, queues, streaming, consensus, replication, or eventual consistency.

## Mental model
Networks fail, clocks skew, messages duplicate/reorder, and partial failure is normal. Correctness must survive uncertainty.

## Procedure
1. Map service ownership, data authority, network boundaries, brokers, replication, and failure domains.
2. Define delivery guarantees, idempotency keys, ordering scope, deduplication windows, and poison-message policy.
3. Set timeout budgets, bounded retries with jitter/backoff, circuit breaking, and load shedding.
4. Document consistency model, conflict resolution, clock assumptions, leases, and fencing tokens.
5. Use transactional outbox/inbox or equivalent when database/message atomicity matters.
6. Instrument trace propagation, queue age, saturation, retries, and recovery behavior.

## Quality checklist
- [ ] Partial failures and duplicates are tested.
- [ ] Retries are bounded and idempotent.
- [ ] Consistency and ordering guarantees are stated.
- [ ] Queues and work are bounded.

## Anti-patterns
- Assuming end-to-end exactly-once delivery.
- Using wall-clock timestamps as universal ordering.
- Infinite retries or unbounded buffering.

## Verification
Run failure injection, contract tests, replay/recovery tests, load tests, and consistency checks across replicas.

## Output format
State topology, failure model, consistency/delivery guarantees, recovery evidence, and operational risks.
