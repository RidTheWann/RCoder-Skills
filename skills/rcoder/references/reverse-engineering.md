# Software reverse engineering and binary analysis

## Activate when
Disassembly, decompilation, undocumented formats/protocols, executable analysis, compatibility, emulation, or binary debugging.

## Mental model
Reverse engineering reconstructs behavior from imperfect evidence. Separate observations, inferences, and hypotheses; preserve provenance and authorization.

## Procedure
1. Confirm authorization and scope: owned software, licensed interoperability, security assessment, research, or permitted preservation. Respect law, contracts, privacy, and anti-circumvention rules.
2. Preserve originals; hash samples; record source, version, architecture, format, build IDs, signatures, and tool versions.
3. Start with static triage: headers, sections, imports/exports, symbols, strings, relocations, metadata, resources, and entropy. Do not execute unknown binaries.
4. Load into a disassembler/decompiler; verify processor mode, ABI, endianness, calling convention, memory map, and symbol assumptions.
5. Build control-flow/data-flow hypotheses; trace callers, callees, state mutation, error paths, and external interactions. Decompiler output is not original source.
6. Use dynamic debugging only in a disposable isolated environment with synthetic credentials and restricted network. Capture inputs, outputs, syscalls, memory changes, and traces.
7. For undocumented formats/protocols, build minimal fixtures, parsers, differential tests, fuzz harnesses, and round-trip invariants.
8. Validate inferred behavior against references, authoritative documentation, hardware, multiple samples, or independent observations.
9. Keep reproducible notes: file hash, address/RVA, tool/version, command, offsets, trace references, and confidence.

## Quality checklist
- [ ] Authorization and sample provenance are documented.
- [ ] Original artifacts remain immutable and hashed.
- [ ] Instruction decoding and ABI assumptions are verified.
- [ ] Decompiler hypotheses are independently tested.
- [ ] Dynamic analysis is isolated and non-destructive.

## Anti-patterns
- Treating pseudocode as exact original source.
- Executing unknown samples on the host.
- Publishing proprietary code, secrets, or personal data recovered in analysis.
- Assuming similar binaries share ABI/layout.

## Verification
Repeat key findings with independent tools/reference behavior; use minimal fixtures and differential tests; state unconfirmed claims.

## Output format
Report sample hash, scope, architecture, tools, confirmed behavior, hypotheses/confidence, reproduction, and limitations.
