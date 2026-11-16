# Binary file-format reverse engineering

## Activate when
An undocumented binary/container format, save file, asset archive, memory image, or serialization must be understood for authorized interoperability/research.

## Mental model
Treat unknown bytes as untrusted. Infer structure from repeated observations and preserve exact sample provenance.

## Procedure
1. Hash and preserve original specimens; record source, software version, architecture, and acquisition conditions.
2. Collect several valid/invalid samples with controlled differences; map offsets, lengths, magic values, checksums, and repeated structures.
3. Test endianness, alignment, integer widths, compression, encryption, padding, and nested-container hypotheses.
4. Build a read-only parser that validates bounds, integer overflow, recursion depth, and resource limits before allocation.
5. Use differential fixtures and round-trip invariants; preserve unknown fields rather than silently discarding them.
6. Fuzz parser boundaries and malformed lengths; isolate proprietary or sensitive artifacts.

## Quality checklist
- [ ] Specimens are hashed and varied systematically.
- [ ] Offset/length claims are evidence-backed.
- [ ] Parser rejects overflow and malformed bounds.
- [ ] Unknown fields and versioning are considered.

## Anti-patterns
- Assuming structure from one sample.
- Trusting size fields before bounds checks.
- Treating compressed/encrypted data as plain text.

## Verification
Run parser fuzzing, differential tests, round-trip checks, and cross-version fixture tests.

## Output format
Provide format map, evidence samples, parser assumptions, malformed cases, and confidence.
