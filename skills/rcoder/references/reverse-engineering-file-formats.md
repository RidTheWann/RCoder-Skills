# Binary file-format reverse engineering

## Activate when
An undocumented binary/container format, save file, asset archive, memory image, or serialization must be understood for authorized interoperability or research. Do not activate for executable code semantics (use reverse-engineering or reverse-engineering-architecture).

## Mission and expertise
Reconstruct a format map from systematic observations and build a safe, validating reader. Own specimen provenance, offset/length evidence, bounds and overflow safety, versioning, and the preservation of unknown fields. Do not treat a single sample as proof of a layout.

## Mental model
Treat unknown bytes as untrusted. Infer structure from repeated observations and preserve exact sample provenance. A size field is a claim by the file, not a fact; validate it before allocation. Unknown fields must be preserved, not silently discarded.

## Prerequisites and reconnaissance
1. Hash and preserve original specimens; record source, software version, architecture, and acquisition conditions.
2. Collect several valid and invalid samples with controlled differences before proposing structure.
3. Determine available format inspectors, hex viewers, and scripting runtimes; verify versions before use.
4. Define the interoperability goal and which fields must be written versus only read.

## Procedure
1. Hash and preserve original specimens; record source, software version, architecture, and acquisition conditions.
2. Collect several valid/invalid samples with controlled differences; map offsets, lengths, magic values, checksums, and repeated structures.
3. Test endianness, alignment, integer widths, compression, encryption, padding, and nested-container hypotheses.
4. Build a read-only parser that validates bounds, integer overflow, recursion depth, and resource limits before allocation.
5. Use differential fixtures and round-trip invariants; preserve unknown fields rather than silently discarding them.
6. Fuzz parser boundaries and malformed lengths; isolate proprietary or sensitive artifacts.

## Decision tree
- Only one specimen is available → mark all layout claims as Hypothesis and seek more samples before writing.
- Magic/version fields change across samples → treat versioning explicitly and branch the parser.
- Size fields disagree with actual data → Potential corruption or misunderstood layout; do not allocate from the field alone.
- Data appears compressed or encrypted → identify signatures and entropy first; do not treat it as plain text.
- Checksum covers a region → verify the algorithm with controlled single-byte changes before trusting it.
- Round-trip is not byte-identical → determine whether differences are padding, ordering, or unknown fields; preserve them.
- Writer is required → build and test the reader first, then add a writer that preserves unknowns and validated invariants.

## Tool strategy
Use hex viewers, file-type detectors, entropy analysis, binary diff tools, and a scripting runtime for fixture generation. Verify tool versions and availability. Use fuzzing and sanitizers for the parser. Keep proprietary or sensitive artifacts isolated and avoid uploading them to external services.

## Advanced techniques
- **Controlled-difference samples:** change one field or one input property at a time and diff the bytes to locate encoding.
- **Field invariants:** derive valid ranges and relationships from multiple samples, then encode them as parser assertions.
- **Bounded parsing:** validate offsets and lengths with checked arithmetic before any allocation or recursion.
- **Round-trip invariants:** for a reader/writer pair, verify that parsed structures re-serialize to equivalent bytes and that unknown regions survive.
- **Grammar-based fuzzing:** generate structured but malformed inputs targeting length, offset, and nesting fields.
- **Cross-version fixtures:** test samples from multiple producer versions to detect layout drift.

## Failure modes
- **Assuming structure from one sample** → wrong layout → gather varied specimens and lower confidence.
- **Trusting size fields before bounds checks** → crashes or memory exhaustion → validate with checked arithmetic first.
- **Treating compressed/encrypted data as plain text** → nonsense conclusions → identify encoding by signature and entropy.
- **Discarding unknown fields** → data loss on round-trip → preserve opaque regions byte-for-byte.
- **Unbounded recursion on nested containers** → denial of service → set explicit depth and size limits.

## Quality checklist
Specimens are hashed and varied systematically; offset/length claims are evidence-backed; parser rejects overflow and malformed bounds; unknown fields and versioning are considered.

## Anti-patterns
Guessing checksums without controlled experiments; writing a parser before collecting samples; allocating from untrusted length fields; deleting fields that are not understood; publishing specimen contents without provenance and redaction.

## Verification
Run parser fuzzing, differential tests, round-trip checks, and cross-version fixture tests. Record exact sample hashes, tool versions, and commands; mark untested cases NOT VERIFIED.

## Output format
Format map · evidence samples and hashes · parser assumptions · malformed cases · confidence · unresolved fields.

## Executable Verification & Failure Diagnostics
- **Verify**: Run parser fuzzing, differential tests, round-trip checks, and cross-version fixture tests.
- **Anti-Patterns**: Guessing checksums without controlled experiments; writing a parser before collecting samples
- **Failure Diagnostics**: A failing or ambiguous Verify result -> the first failing assertion or error line is the root cause, not the completion summary -> rerun the narrowest check named in Verify and inspect its first failing assertion.
