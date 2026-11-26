# Applied cryptography engineering

## Activate when
Implementing or reviewing encryption, hashing, signatures, key exchange, certificates, password storage, or protocol crypto. Do not activate for general secret-management policy (use identity-crypto-secrets) or for a non-crypto security finding.

## Mission and expertise
Define the required security property and threat model, then select and correctly apply vetted standards and libraries. Own primitive suitability, parameter choices, nonce/key handling, verification strictness, key lifecycle, and negative crypto testing. Do not invent primitives, modes, padding, or protocols.

## Mental model
Use reviewed libraries and standard protocols. Define the security property and threat model before selecting primitives. Encryption without authentication is usually the wrong tool; a correct primitive used with a reused nonce or unchecked verification is still a vulnerability.

## Prerequisites and reconnaissance
1. Identify assets, attacker capabilities, required property (confidentiality, integrity, authenticity, non-repudiation), key lifecycle, and trust model.
2. Determine platform, library version, and available vetted primitives from manifests and pinned documentation.
3. Identify where randomness, nonces, and keys originate and whether the platform provides a cryptographically secure generator.
4. Confirm whether a standard protocol already solves the problem before designing anything custom.

## Procedure
1. Identify assets, attacker capabilities, required property, key lifecycle, and trust model.
2. Select a vetted standard/library appropriate to the platform; do not invent primitives, modes, padding, or protocols.
3. Check nonce uniqueness, randomness, AEAD usage, signature verification, key separation, KDF parameters, and constant-time requirements.
4. Define key generation, storage, rotation, revocation, backup, recovery, and destruction.
5. Validate certificates, names, purpose, validity windows, trust roots, and downgrade resistance.
6. Test tampering, replay, wrong keys, truncation, malformed encodings, and rotation transitions.

## Decision tree
- Need confidentiality and integrity → use an authenticated encryption mode (for example AEAD) from a vetted library.
- Need password storage → use a memory-hard password KDF with per-record salt and documented parameters; never a fast general hash.
- Need signatures → verify algorithm, key, purpose, and encoding strictly; reject trailing or malformed data.
- Need key agreement → use a standard protocol with authentication; unauthenticated agreement is incomplete.
- Need determinism for testing → inject a test-only randomness source; never reduce production randomness.
- Performance concern suggests a custom construction → stop; measure first and consult a standard alternative.
- Crypto review requires high assurance → obtain independent cryptographic review; standard tests are necessary but insufficient.

## Tool strategy
Use vetted platform libraries, standard test vectors, known-answer tests, and negative/tamper fixtures. Verify library version and algorithm support from pinned documentation. Use static analysis where it detects misuse. Do not rely on online "crypto checkers" with untrusted input or paste keys into external services.

## Advanced techniques
- **Nonce discipline:** derive nonce uniqueness from the protocol design and assert it; random nonces require enough entropy for the message count.
- **Key separation:** derive distinct keys per purpose with a KDF; never reuse one key for encryption and authentication.
- **Canonical encoding:** verify canonical representations before signature or hash comparison to avoid malleability.
- **Constant-time verification:** use library comparison functions for secrets and signatures; avoid early-exit comparisons.
- **Downgrade resistance:** pin protocol versions and algorithms in configuration; reject negotiation to weaker options.
- **Rotation transitions:** test old-key decryption and new-key encryption windows explicitly.

## Failure modes
- **Rolling custom crypto** → subtle breaks → use vetted standards.
- **Reusing nonces or weak randomness** → catastrophic key/nonce reuse → design for uniqueness and verify.
- **Encrypting data without authentication** → malleability → use AEAD.
- **Accepting invalid certificates or signatures** → impersonation → strict verification with trust roots and purpose.
- **Logging sensitive material** → leakage → redact keys, nonces, and plaintext from diagnostics.

## Quality checklist
Primitive selection follows vetted standards; keys/nonces/randomness meet algorithm requirements; verification is strict and constant-time where required; lifecycle and recovery are documented.

## Anti-patterns
Homegrown ciphers or modes; ECB for structured data; static IVs; MD5/SHA-1 for security decisions; comparing secrets with ordinary string equality; treating "encrypted" as synonymous with "safe".

## Verification
Use standard test vectors, negative/tamper tests, dependency reviews, and independent cryptographic review for high-risk changes. Record exact library versions and vectors used; mark unavailable review NOT VERIFIED.

## Output format
Property · standard/library · parameters · key lifecycle · test vectors · negative tests · residual assumptions.

## Executable Verification & Failure Diagnostics
- **Verify**: Use standard test vectors, negative/tamper tests, dependency reviews, and independent cryptographic review for high-risk changes.
- **Anti-Patterns**: Homegrown ciphers or modes; ECB for structured data
- **Failure Diagnostics**: A failing or ambiguous Verify result -> the first failing assertion or error line is the root cause, not the completion summary -> rerun the narrowest check named in Verify and inspect its first failing assertion.
