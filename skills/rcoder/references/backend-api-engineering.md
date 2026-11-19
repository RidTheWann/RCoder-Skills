# Backend, API, and service engineering

## Activate when
HTTP/gRPC APIs, service boundaries, authentication, background jobs, event systems, or backend runtime behavior. Use api-protocol-engineering for wire-level contracts and application-security for control review.

## Mission and expertise
Own service-contract semantics, server-side authorization, retry-safe writes, consistency boundaries, and observability. A schema is only one part of a contract; failure modes and compatibility are equally binding.

## Mental model
A service contract includes semantics, authorization, failure modes, idempotency, consistency, observability, and compatibility—not only schemas. Client-provided ownership fields are untrusted input.

## Prerequisites and reconnaissance
1. Inspect API schemas/routes, middleware, authn/authz, service ownership, deployment topology, and compatibility policy.
2. Identify which resources have separate owners and tenants, and where authority transitions occur.
3. Determine timeout budgets, retry policy, and whether writes are idempotent.
4. Check telemetry and secret-handling conventions before adding logging.

## Procedure
1. Inspect API schemas/routes, middleware, authn/authz, service ownership, deployment topology, and compatibility policy.
2. Define validation, error taxonomy, pagination, rate limits, idempotency, payload limits, and timeout budgets.
3. Enforce authorization server-side for every object/action; prevent IDOR and confused-deputy behavior.
4. Design retry-safe writes, transaction boundaries, outbox/inbox handling, and versioned event contracts.
5. Keep secrets out of logs; add structured telemetry with correlation IDs and data minimization.
6. Document rollout, rollback, and backward compatibility for consumers.

## Decision tree
- Client sends owner/tenant field → ignore it and derive authority from the authenticated context.
- Retry may duplicate a write → require an idempotency key and record outcomes.
- Event must be consistent with a database commit → use a transactional outbox.
- Consumer cannot upgrade immediately → version the contract and support overlap.
- Authorization check depends on a remote call → bound it with a timeout and fail closed.
- High load → apply rate limits and load shedding before adding capacity assumptions.
- Log may contain sensitive data → redact at the source and verify captured output.

## Tool strategy
Use schema validators, contract tests, authorization matrices, local service fixtures, load tools, and structured log inspection. Verify framework and runtime versions from configuration. Use synthetic identities and data for cross-user tests.

## Advanced techniques
- **Authorization matrix:** roles x actions x resources, including unauthenticated and cross-tenant rows.
- **Outbox/inbox pattern:** make state change and message publication atomic, with deduplication on consumption.
- **Timeout budgets:** allocate a total request budget and propagate remaining time to dependencies.
- **Error taxonomy:** stable codes with retryability and documented client handling.
- **Telemetry minimization:** log correlation IDs and outcomes, not payloads or secrets.

## Failure modes
- **Trusting client-provided ownership fields** → IDOR → derive ownership server-side.
- **Unbounded retries, queues, or payloads** → saturation → bound all three.
- **Breaking contracts without migration** → consumer failures → version and stage.
- **Concurrent writes to one resource** → lost updates → use optimistic concurrency or explicit locking.
- **Secrets in logs** → leakage → redact and scan outputs.

## Quality checklist
Authorization is enforced at data/action boundaries; retries and partial failures are safe; contracts are versioned and tested; sensitive data is not logged.

## Anti-patterns
Hidden UI controls as authorization; accepting client-side price or role; unbounded background goroutines; treating a 2xx response as proof of correct semantics; shipping without rollback documentation.

## Verification
Run schema validation, unit/contract/integration tests, authorization matrices, proportionate load tests, and deployment smoke checks. Record exact commands and results; mark untested environments NOT VERIFIED.

## Output format
Contract changes · threat boundaries · retry/consistency behavior · observability · rollout · verification.
