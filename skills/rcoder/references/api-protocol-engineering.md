# API and protocol contract engineering

## Activate when
Designing, evolving, or debugging HTTP, gRPC, message, binary, or inter-process protocols. Use data-api for persistence/field compatibility and api/protocol-specific language modules for implementation idioms.

## Mission and expertise
Define the complete contract — schema, semantics, compatibility, ordering, errors, versioning, security, and resource limits — and verify it across old/new combinations. Own wire-level decisions and the rule that a transport is not an authorization mechanism.

## Mental model
A protocol contract includes schema, semantics, compatibility, ordering, error handling, versioning, security, and resource limits. Transport encryption protects the channel; it does not prove the peer is authorized.

## Prerequisites and reconnaissance
1. Identify consumers, ownership, transport, schema format, version policy, and compatibility promises.
2. Determine which versions are deployed simultaneously and how clients discover schema changes.
3. Establish authentication, authorization, replay, and rate-limit requirements from the security model.
4. Determine the source of truth for generated schemas/clients and how they are produced.

## Procedure
1. Identify consumers, ownership, transport, schema format, version policy, and compatibility promises.
2. Define canonical encoding, field presence/defaults, unknown-field handling, error taxonomy, limits, and idempotency.
3. Test old/new producer-consumer pairs and partial rollout combinations.
4. Validate authentication, authorization, replay protection, payload limits, and downgrade behavior.
5. Version schemas and generated clients from their source of truth.
6. Document deprecation, migration windows, and rollback.

## Decision tree
- New optional field → define default and unknown-field behavior; verify old consumers tolerate it.
- Changed field meaning → breaking change; create a new version and a migration window.
- Multiple consumers with different upgrade speeds → support overlapping versions with a deprecation timeline.
- Message queue → define ordering, deduplication, at-least-once semantics, and dead-letter handling.
- Binary protocol → define endianness, alignment, length limits, and canonical encoding; fuzz the parser.
- Untrusted client → bound payload sizes and timeouts, authenticate, authorize per resource, and reject downgrades.
- Generated clients drift → regenerate from the canonical schema and verify reproducibility.

## Tool strategy
Use schema validators, contract test frameworks, parser fuzzers, and interop fixtures with old/new builds. Verify tool versions and do not hand-edit generated artifacts. Prefer version-matched official documentation for protocol semantics.

## Advanced techniques
- **Compatibility matrix:** enumerate producer and consumer versions and record pass/fail for each pair.
- **Canonical encoding:** define one valid byte representation to avoid signature and cache ambiguity.
- **Unknown-field policy:** decide explicitly whether to ignore, preserve, or reject unknown fields.
- **Error taxonomy:** stable machine-readable codes with retryability and documentation.
- **Replay defense:** nonces, timestamps with bounded skew, and idempotency keys for writes.
- **Interop fuzzing:** generate malformed and edge-case payloads against both old and new implementations.

## Failure modes
- **Changing field meaning without a version change** → silent semantic drift → version the contract.
- **Assuming all clients upgrade together** → partial rollout failures → test mixed-version pairs.
- **Treating transport encryption as endpoint authorization** → unauthorized access → authorize per resource.
- **Unbounded payloads** → resource exhaustion → enforce size and time limits.
- **Hand-edited generated clients** → drift → regenerate from source.

## Quality checklist
Compatibility matrix is tested; unknown/malformed fields follow explicit safe rules; payload/time limits and auth boundaries are explicit; generated artifacts are reproducible.

## Anti-patterns
Silent field removal; wildcard CORS with credentials; acceptance of any TLS certificate; inconsistent error shapes; undocumented deprecation.

## Verification
Run schema validation, consumer-driven contract tests, parser fuzzing, and old/new interoperability tests. Record exact versions and combinations tested; mark untested pairs NOT VERIFIED.

## Output format
Contract · version compatibility · errors · security · rollout · verification evidence.

## Executable Verification & Failure Diagnostics
- **Verify**: Run schema validation, consumer-driven contract tests, parser fuzzing, and old/new interoperability tests.
- **Anti-Patterns**: Silent field removal; wildcard CORS with credentials
- **Failure Diagnostics**: A failing or ambiguous Verify result -> the first failing assertion or error line is the root cause, not the completion summary -> rerun the narrowest check named in Verify and inspect its first failing assertion.
