# Applied cryptography engineering

## Activate when
Implementing or reviewing encryption, hashing, signatures, key exchange, certificates, password storage, or protocol crypto.

## Mental model
Use reviewed libraries and standard protocols. Define the security property and threat model before selecting primitives.

## Procedure
1. Identify assets, attacker capabilities, required property, key lifecycle, and trust model.
2. Select a vetted standard/library appropriate to the platform; do not invent primitives, modes, padding, or protocols.
3. Check nonce uniqueness, randomness, AEAD usage, signature verification, key separation, KDF parameters, and constant-time requirements.
4. Define key generation, storage, rotation, revocation, backup, recovery, and destruction.
5. Validate certificates, names, purpose, validity windows, trust roots, and downgrade resistance.
6. Test tampering, replay, wrong keys, truncation, malformed encodings, and rotation transitions.

## Quality checklist
- [ ] Primitive selection follows vetted standards.
- [ ] Keys/nonces/randomness meet algorithm requirements.
- [ ] Verification is strict and constant-time where required.
- [ ] Lifecycle and recovery are documented.

## Anti-patterns
- Rolling custom crypto.
- Reusing nonces or weak randomness.
- Encrypting data without authentication.
- Accepting invalid certificates or signatures.

## Verification
Use standard test vectors, negative/tamper tests, dependency reviews, and independent cryptographic review for high-risk changes.

## Output format
State property, standard/library, parameters, key lifecycle, test vectors, and residual assumptions.
