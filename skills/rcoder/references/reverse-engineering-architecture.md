# Reverse-engineering research workflow

## Activate when
Investigating undocumented executable behavior, CPU/ISA semantics, proprietary file formats, compatibility layers, or emulator/recompiler implementations.

## Mental model
A reliable conclusion is a traceable chain from artifact to observation to hypothesis to differential confirmation. Do not guess missing ABI or instruction semantics.

## Procedure
1. Set authorization, clean-room/provenance rules, artifact hash, version, architecture, and research question.
2. Create an evidence ledger with confidence levels: observed, cross-validated, inferred, or unknown.
3. Separate static findings (symbols, CFG, data references) from dynamic findings (traces, register/memory changes, syscalls, timing).
4. Document machine state before/after each instruction or function: PC, registers, flags, memory ranges, exceptions, and calling convention.
5. Compare independent specimens/implementations; use differential execution and minimized fixtures where possible.
6. Record negative evidence and alternative hypotheses; keep undecoded/ambiguous behavior explicitly unsupported.
7. Translate confirmed semantics into machine-readable tests before implementation.

## Quality checklist
- [ ] Every claim links to a hashed artifact and reproducible observation.
- [ ] Static and dynamic evidence are distinguished.
- [ ] ABI and machine-state effects are explicit.
- [ ] Ambiguous behavior stays unresolved until evidence supports it.

## Anti-patterns
- Guessing register effects from function names or one caller.
- Treating one trace as universal semantics.
- Mixing proprietary source with clean-room implementation notes.

## Verification
Reproduce traces from clean snapshots, compare against a reference/hardware, and test each inferred rule with minimal cases.

## Output format
Output question, evidence ledger, hypotheses, confirmed semantics, tests, confidence, and unresolved issues.
