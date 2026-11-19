# Distributed systems and event-driven engineering

## Activate when
Multi-service coordination, distributed locks, queues, streaming, consensus, replication, or eventual consistency. Use backend-api-engineering for single-service contract work and architecture for topology decisions.

## Mission and expertise
Own failure-model reasoning: partial failure, duplication, reordering, clock skew, and replica divergence. State delivery and consistency guarantees precisely and verify them with fault injection.

## Mental model
Networks fail, clocks skew, messages duplicate/reorder, and partial failure is normal. Correctness must survive uncertainty. Exactly-once delivery is an end-to-end property, not a queue feature.

## Prerequisites and reconnaissance
1. Map service ownership, data authority, network boundaries, brokers, replication, and failure domains.
2. Determine the actual delivery, ordering, and consistency guarantees of the infrastructure in use.
3. Identify clock sources, lease mechanisms, and fencing requirements.
4. Establish how queue age, saturation, and retries are observed today.

## Procedure
1. Map service ownership, data authority, network boundaries, brokers, replication, and failure domains.
2. Define delivery guarantees, idempotency keys, ordering scope, deduplication windows, and poison-message policy.
3. Set timeout budgets, bounded retries with jitter/backoff, circuit breaking, and load shedding.
4. Document consistency model, conflict resolution, clock assumptions, leases, and fencing tokens.
5. Use transactional outbox/inbox or equivalent when database/message atomicity matters.
6. Instrument trace propagation, queue age, saturation, retries, and recovery behavior.

## Decision tree
- Message may be delivered twice → make the consumer idempotent with a deduplication window.
- Order matters → scope ordering to a key/partition and state its limits; do not assume global order.
- Lock is needed → use leases with fencing tokens so a stale holder cannot write.
- Event must match a database commit → transactional outbox.
- Dependency is slow → timeout with jitter/backoff and a circuit breaker; shed load when saturated.
- Replicas disagree → define conflict resolution and reconciliation, not just replication.
- Wall-clock ordering is proposed → replace with logical ordering or explicit causal metadata.

## Tool strategy
Use contract tests, fault injection, replay/recovery tests, load tests, and consistency checks across replicas. Verify broker and client library versions from manifests. Use synthetic workloads and controlled network faults.

## Advanced techniques
- **Failure-model table:** enumerate crash, partition, timeout, duplicate, reorder, and slow-node cases with expected behavior.
- **Fencing tokens:** attach monotonically increasing tokens to writes so stale lease owners are rejected.
- **Backoff with jitter:** prevent synchronized retry storms after a shared failure.
- **Reconciliation jobs:** periodically compare authoritative state and repair drift with bounded work.
- **Queue-age SLOs:** alert on time-in-queue, not only queue length, to detect stalls.

## Failure modes
- **Assuming end-to-end exactly-once delivery** → duplicates → idempotent consumers.
- **Wall-clock timestamps as universal ordering** → incorrect causality → use logical clocks or sequence numbers.
- **Infinite retries or unbounded buffering** → cascading failure → bound retries and queues.
- **Stale lock holder** → split-brain writes → fencing tokens.
- **Unbounded fan-out** → broker overload → apply limits and backpressure.

## Quality checklist
Partial failures and duplicates are tested; retries are bounded and idempotent; consistency and ordering guarantees are stated; queues and work are bounded.

## Anti-patterns
Distributed locks without leases; retry storms without jitter; assuming a broker preserves global order; treating eventual consistency as "no consistency"; ignoring clock skew in cross-region designs.

## Verification
Run failure injection, contract tests, replay/recovery tests, load tests, and consistency checks across replicas. Record exact fault scenarios and results; mark untested failure modes NOT VERIFIED.

## Output format
Topology · failure model · consistency/delivery guarantees · recovery evidence · operational risks.
