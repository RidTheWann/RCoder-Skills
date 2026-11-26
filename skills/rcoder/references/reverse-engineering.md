# Software reverse engineering and binary analysis

## Activate when
Disassembly, decompilation, undocumented formats/protocols, executable analysis, compatibility, emulation, or binary debugging. Do not activate for ordinary source-level debugging of code you own (use debugging), or for malware classification (use malware-analysis).

## Mission and expertise
Reconstruct behavior from imperfect evidence while preserving provenance and authorization. Own the evidence discipline: observation, interpretation, hypothesis, experiment, and confirmed conclusion must never be conflated. Do not invent missing machine-state behavior, ABI rules, structure layouts, instruction semantics, or undocumented APIs.

## Mental model
Reverse engineering reconstructs behavior from imperfect evidence. Separate observations, inferences, and hypotheses; preserve provenance and authorization. Decompiler output is a hypothesis about source, not the original source. Unknown behavior remains explicitly unresolved until sufficient evidence exists.

## Prerequisites and reconnaissance
1. Confirm authorization and scope: owned software, licensed interoperability, security assessment, research, or permitted preservation. Respect law, contracts, privacy, and anti-circumvention rules.
2. Preserve originals; hash samples; record source, version, architecture, format, build IDs, signatures, and tool versions.
3. Determine available tools and their licensing/versions before relying on any product; do not assume a disassembler is installed.
4. Prepare an isolated environment for any dynamic work, with restricted network and synthetic credentials.

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

## Decision tree
- Static evidence answers the question → stop; avoid dynamic analysis.
- Semantics or runtime state are ambiguous → form competing hypotheses and design a discriminating experiment.
- Tool reports a function name but behavior is unverified → treat the name as a hint, not evidence; load reverse-engineering-architecture.
- Unknown container or serialization format → load reverse-engineering-file-formats.
- Behavior differs across samples or compilers → use differential analysis and record the variables.
- Dynamic analysis would require real credentials or external systems → stop and request authorization or use synthetic fixtures.
- Evidence remains ambiguous after experiments → keep it unresolved; do not guess.

## Tool strategy
Use tools by purpose: format inspectors and hex viewers for headers, disassemblers/decompilers for control flow, Capstone/Keystone for instruction encode/decode checks, Unicorn or QEMU for isolated emulation, GDB/LLDB for debugging, and Frida or tracers for runtime instrumentation. Ghidra, IDA, Binary Ninja, and radare2/Rizin are examples, not assumptions. Verify availability, version, and licensing for each. When a tool is unavailable, record the gap and use an independent alternative rather than inventing results.

## Advanced techniques
- **Evidence taxonomy:** label each statement as Observation, Interpretation, Hypothesis, Experiment, or Confirmed Conclusion.
- **Provenance record:** preserve original hash, tool versions, architecture, endianness, file offsets, virtual addresses, and reproduction commands.
- **Instruction-level testing:** use minimal instruction sequences and emulators to verify semantics independently of a decompiler.
- **Differential analysis:** compare two specimens, versions, or implementations while varying one factor at a time.
- **Cross-tool corroboration:** confirm key findings with a second independent tool or reference implementation.
- **Confidence levels:** attach a level to every conclusion and downgrade when only one source supports it.

## Failure modes
- **Treating pseudocode as exact original source** → false claims → verify through independent evidence.
- **Executing unknown samples on the host** → compromise → use an isolated lab.
- **Assuming similar binaries share ABI/layout** → wrong conclusions → verify each target's ABI and layout.
- **Publishing proprietary code, secrets, or personal data** → harm → sanitize reports and respect scope.
- **One trace treated as universal semantics** → overgeneralization → test multiple states and inputs.

## Quality checklist
Authorization and sample provenance are documented; original artifacts remain immutable and hashed; instruction decoding and ABI assumptions are verified; decompiler hypotheses are independently tested; dynamic analysis is isolated and non-destructive.

## Anti-patterns
Guessing register effects from names; trusting size fields without bounds checks; skipping hashes; reusing a host for dynamic analysis; asserting behavior from a single decompiler view.

## Verification
Repeat key findings with independent tools/reference behavior; use minimal fixtures and differential tests; state unconfirmed claims explicitly. Record exact commands, hashes, addresses, and tool versions.

## Output format
Sample hash · scope · architecture · tools · confirmed behavior · hypotheses/confidence · reproduction · limitations · unresolved items.

## Executable Verification & Failure Diagnostics
- **Verify**: Repeat key findings with independent tools/reference behavior; use minimal fixtures and differential tests; state unconfirmed claims explicitly.
- **Anti-Patterns**: Guessing register effects from names; trusting size fields without bounds checks
- **Failure Diagnostics**: A failing or ambiguous Verify result -> the first failing assertion or error line is the root cause, not the completion summary -> rerun the narrowest check named in Verify and inspect its first failing assertion.
