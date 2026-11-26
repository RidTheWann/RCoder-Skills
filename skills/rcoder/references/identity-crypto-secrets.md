# Identity, cryptography, and secrets management

## Activate when
Authentication, authorization, cryptographic protocols, key management, API tokens, certificates, secrets, or signing. Use cryptography-engineering for primitive selection and secure-code-review for implementation findings.

## Mission and expertise
Own identity lifecycle, authorization modeling, key lifecycle, secret handling, and certificate/token trust. Keep authentication, authorization, and cryptographic properties separate and explicitly verified.

## Mental model
Identity proves who/what; authorization decides what; cryptography protects defined properties. Keep responsibilities separate. Encryption at rest does not protect a compromised identity, and a valid token does not grant every action.

## Prerequisites and reconnaissance
1. Define identity types/lifecycle, assurance level, authorization model, token audience/scope, and revocation.
2. Identify approved libraries, key stores, and certificate authorities from project configuration.
3. Determine where secrets enter the system and every place they could be exposed (source, logs, prompts, dumps, telemetry, fixtures).
4. Check rotation, recovery, and incident-response ownership before recommending changes.

## Procedure
1. Define identity types/lifecycle, assurance level, authorization model, token audience/scope, and revocation.
2. Use established libraries/protocols; do not design custom cryptography or encodings.
3. Check algorithm agility, nonce/IV uniqueness, authentication-before-decryption, key derivation, rotation, storage, backup, and destruction.
4. Store secrets in approved managers or OS keystores; scope access by workload identity and environment.
5. Prevent credentials from entering source, logs, prompts, crash dumps, telemetry, and test fixtures.
6. Review recovery, service identities, certificate renewal, trust roots, and compromised-key response.

## Decision tree
- Token accepted from a different audience → reject; verify issuer, audience, and scope explicitly.
- Authorization depends on a client-supplied role → derive authority from the server-side identity record.
- Secret found in source or logs → rotate immediately, remove from history where policy requires, and fix the path.
- Key never rotates → define rotation with overlap and test old/new key windows.
- Certificate validation disabled → restore strict validation and fix the trust chain or hostname.
- Custom crypto proposed → use a vetted library and standard protocol.
- Recovery requires a shared admin credential → replace with break-glass accounts, least privilege, and audit.

## Tool strategy
Use authorization matrices, token validation tests, secret scanners, certificate validation tools, and key-lifecycle exercises. Verify library versions and protocol support from manifests. Never paste real secrets into test artifacts or external services.

## Advanced techniques
- **Audience/scope matrix:** test tokens with wrong audience, expired time, missing scope, and wrong issuer.
- **Rotation drill:** verify old-key verification and new-key issuance during the overlap window.
- **Secret-flow audit:** trace each secret from creation through storage, use, logging, and destruction.
- **Revocation test:** confirm revoked tokens/keys are rejected on the next use.
- **Certificate checks:** validate chain, purpose, hostname, and validity window with negative cases.

## Failure modes
- **Custom cryptography or home-grown password hashing** → breakable design → use vetted standards.
- **One shared admin token for all services** → huge blast radius → scope identities.
- **Assuming encryption at rest protects compromised identities** → unauthorized access → authorize per action.
- **Secrets in fixtures or telemetry** → leakage → use synthetic values and redaction.
- **No revocation path** → prolonged compromise → define and test revocation.

## Quality checklist
Authorization is distinct from authentication; keys have ownership, rotation, revocation, and recovery; cryptographic parameters follow vetted standards; secrets are excluded from logs and artifacts.

## Anti-patterns
Bearer tokens in URLs; logging authorization headers; accepting any certificate; static signing keys in source; treating a long-lived token as identity proof.

## Verification
Run authz tests, token audience/scope checks, secret scans, certificate validation, and key-lifecycle exercises. Record exact commands and results; mark unavailable lifecycle tests NOT VERIFIED.

## Output format
Identity model · algorithms/libraries · key lifecycle · exposure boundaries · tests · recovery gaps.

## Executable Verification & Failure Diagnostics
- **Verify**: Run authz tests, token audience/scope checks, secret scans, certificate validation, and key-lifecycle exercises.
- **Anti-Patterns**: Bearer tokens in URLs; logging authorization headers
- **Failure Diagnostics**: A failing or ambiguous Verify result -> the first failing assertion or error line is the root cause, not the completion summary -> rerun the narrowest check named in Verify and inspect its first failing assertion.
