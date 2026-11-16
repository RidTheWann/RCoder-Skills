# Backend, API, and service engineering

## Activate when
HTTP/gRPC APIs, service boundaries, authentication, background jobs, event systems, or backend runtime behavior.

## Mental model
A service contract includes semantics, authorization, failure modes, idempotency, consistency, observability, and compatibility—not only schemas.

## Procedure
1. Inspect API schemas/routes, middleware, authn/authz, service ownership, deployment topology, and compatibility policy.
2. Define validation, error taxonomy, pagination, rate limits, idempotency, payload limits, and timeout budgets.
3. Enforce authorization server-side for every object/action; prevent IDOR and confused-deputy behavior.
4. Design retry-safe writes, transaction boundaries, outbox/inbox handling, and versioned event contracts.
5. Keep secrets out of logs; add structured telemetry with correlation IDs and data minimization.
6. Document rollout, rollback, and backward compatibility for consumers.

## Quality checklist
- [ ] Authorization is enforced at data/action boundaries.
- [ ] Retries and partial failures are safe.
- [ ] Contracts are versioned and tested.
- [ ] Sensitive data is not logged.

## Anti-patterns
- Trusting client-provided ownership fields.
- Unbounded retries, queues, or payloads.
- Breaking contracts without migration planning.

## Verification
Run schema validation, unit/contract/integration tests, authorization matrices, proportionate load tests, and deployment smoke checks.

## Output format
State contract changes, threat boundaries, retry/consistency behavior, observability, rollout, and verification.
