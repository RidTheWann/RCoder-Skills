# API and protocol contract engineering

## Activate when
Designing, evolving, or debugging HTTP, gRPC, message, binary, or inter-process protocols.

## Mental model
A protocol contract includes schema, semantics, compatibility, ordering, error handling, versioning, security, and resource limits.

## Procedure
1. Identify consumers, ownership, transport, schema format, version policy, and compatibility promises.
2. Define canonical encoding, field presence/defaults, unknown-field handling, error taxonomy, limits, and idempotency.
3. Test old/new producer-consumer pairs and partial rollout combinations.
4. Validate authentication, authorization, replay protection, payload limits, and downgrade behavior.
5. Version schemas and generated clients from their source of truth.
6. Document deprecation, migration windows, and rollback.

## Quality checklist
- [ ] Compatibility matrix is tested.
- [ ] Unknown/malformed fields follow explicit safe rules.
- [ ] Payload/time limits and auth boundaries are explicit.
- [ ] Generated artifacts are reproducible.

## Anti-patterns
- Changing field meaning without a version change.
- Assuming all clients upgrade together.
- Treating transport encryption as endpoint authorization.

## Verification
Run schema validation, consumer-driven contract tests, parser fuzzing, and old/new interoperability tests.

## Output format
Describe contract, version compatibility, errors, security, rollout, and verification.
