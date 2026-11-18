# Reverse-engineering research workflow

## Activate when
Investigating undocumented executable behavior, CPU/ISA semantics, proprietary file formats, compatibility layers, or emulator/recompiler implementations. Use this module for evidence-led semantic reconstruction; load reverse-engineering for general binary triage and reverse-engineering-file-formats for container/serialization work.

## Mission and expertise
Turn uncertain behavior into a traceable chain from artifact to observation to hypothesis to differential confirmation. Own the research ledger, machine-state documentation, and the rule that unknown ABI, instruction, register, and memory behavior stays unresolved until corroborated.

## Mental model
A reliable conclusion is a traceable chain from artifact to observation to hypothesis to differential confirmation. Do not guess missing ABI or instruction semantics. A conclusion is only as strong as the weakest link in that chain.

## Prerequisites and reconnaissance
1. Set authorization, clean-room/provenance rules, artifact hash, version, architecture, and research question before inspecting.
2. Determine which tools and reference materials are actually available and version-recorded.
3. Establish a disposable analysis environment and a minimal fixture strategy.
4. Define what would count as sufficient evidence to confirm or reject each hypothesis.

## Procedure
1. Set authorization, clean-room/provenance rules, artifact hash, version, architecture, and research question.
2. Create an evidence ledger with confidence levels: observed, cross-validated, inferred, or unknown.
3. Separate static findings (symbols, CFG, data references) from dynamic findings (traces, register/memory changes, syscalls, timing).
4. Document machine state before/after each instruction or function: PC, registers, flags, memory ranges, exceptions, and calling convention.
5. Compare independent specimens/implementations; use differential execution and minimized fixtures where possible.
6. Record negative evidence and alternative hypotheses; keep undecoded/ambiguous behavior explicitly unsupported.
7. Translate confirmed semantics into machine-readable tests before implementation.

## Decision tree
- Question is about a container/serialization layout → load reverse-engineering-file-formats.
- Question is about instruction semantics or calling convention → use instruction-level tests plus authoritative ISA/ABI documentation.
- Static analysis answers the question → stop and record hash, addresses, and tool versions.
- One trace suggests a rule → treat as Hypothesis; design a second test with different inputs or state.
- Two independent tools disagree → mark Unresolved until a third source or direct experiment settles it.
- Hardware behavior is the reference → use hardware observation or a documented reference implementation; do not rely on an emulator alone.
- Clean-room constraints apply → keep proprietary source analysis and implementation notes separated.
- Evidence is insufficient → keep the item unresolved and state what observation would resolve it.

## Tool strategy
Use disassemblers/decompilers for structure, Capstone/Keystone for encode/decode verification, Unicorn/QEMU for isolated execution, GDB/LLDB for state inspection, and tracers for runtime behavior. Verify each tool's availability, version, and license. Prefer authoritative specifications and reference implementations over forum descriptions. When documentation cannot be accessed, record external verification as unavailable.

## Advanced techniques
- **Evidence ledger:** columns for claim type (observation/interpretation/hypothesis/experiment/conclusion), artifact hash, address/RVA, tool version, command, and confidence.
- **Machine-state snapshots:** record PC, registers, flags, stack, and relevant memory before and after each step of interest.
- **Minimal fixtures:** reduce inputs to the smallest sequence that still exhibits the behavior, then test boundary variants.
- **Differential execution:** vary one factor (version, compiler, flags, input) and compare traces to isolate the cause.
- **Negative evidence:** record cases where a hypothesized rule fails; these are often more informative than confirming cases.
- **Test-first semantics:** encode each confirmed rule as a regression test before writing an emulator or recompiler.

## Failure modes
- **Guessing register effects from function names or one caller** → wrong semantics → test with instruction-level fixtures.
- **Treating one trace as universal semantics** → overgeneralization → vary inputs and states.
- **Mixing proprietary source with clean-room implementation notes** → legal and design risk → maintain separate records.
- **Trusting an emulator as ground truth** → circular conclusions → corroborate with hardware or reference behavior.
- **Losing provenance** → unreproducible results → hash and record at every step.

## Quality checklist
Every claim links to a hashed artifact and reproducible observation; static and dynamic evidence are distinguished; ABI and machine-state effects are explicit; ambiguous behavior stays unresolved until evidence supports it.

## Anti-patterns
Inventing undocumented behavior to fill gaps; asserting semantics from decompiler pseudocode; skipping confidence levels; conflating correlation with mechanism; publishing unresolved hypotheses as conclusions.

## Verification
Reproduce traces from clean snapshots, compare against a reference/hardware, and test each inferred rule with minimal cases. Record exact commands, hashes, addresses, tool versions, and confidence.

## Output format
Question · evidence ledger · hypotheses · confirmed semantics · tests · confidence · unresolved issues.
