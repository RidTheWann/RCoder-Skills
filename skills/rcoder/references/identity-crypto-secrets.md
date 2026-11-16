# Identity, cryptography, and secrets management

## Activate when
Authentication, authorization, cryptographic protocols, key management, API tokens, certificates, secrets, or signing.

## Mental model
Identity proves who/what; authorization decides what; cryptography protects defined properties. Keep responsibilities separate.

## Procedure
1. Define identity types/lifecycle, assurance level, authorization model, token audience/scope, and revocation.
2. Use established libraries/protocols; do not design custom cryptography or encodings.
3. Check algorithm agility, nonce/IV uniqueness, authentication-before-decryption, key derivation, rotation, storage, backup, and destruction.
4. Store secrets in approved managers or OS keystores; scope access by workload identity and environment.
5. Prevent credentials from entering source, logs, prompts, crash dumps, telemetry, and test fixtures.
6. Review recovery, service identities, certificate renewal, trust roots, and compromised-key response.

## Quality checklist
- [ ] Authorization is distinct from authentication.
- [ ] Keys have ownership, rotation, revocation, and recovery.
- [ ] Cryptographic parameters follow vetted standards.
- [ ] Secrets are excluded from logs and artifacts.

## Anti-patterns
- Custom cryptography or home-grown password hashing.
- One shared admin token for all services.
- Assuming encryption at rest protects compromised identities.

## Verification
Run authz tests, token audience/scope checks, secret scans, certificate validation, and key-lifecycle exercises.

## Output format
State identity model, algorithms/libraries, key lifecycle, exposure boundaries, tests, and recovery gaps.
