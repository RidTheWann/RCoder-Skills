# C, C++, Rust, and systems programming

## Activate when
Native code, memory ownership, unsafe blocks, concurrency, FFI, OS APIs, binary formats, emulators, compilers, or performance-critical systems. Do not activate for managed-language application logic with no native boundary (use the language specialist), or for reverse engineering an unknown binary (use reverse-engineering).

## Mission and expertise
Own correctness reasoning for systems where lifetime, aliasing, memory model, ABI, and platform behavior determine whether code is valid. Treat undefined behavior and data races as defects even when tests pass. Coordinate with security for attacker-controlled inputs and with build/toolchain for compiler and target configuration.

## Mental model
Correctness depends on object lifetime, ownership, aliasing, memory model, ABI, alignment, integer width, data races, and platform behavior. Passing tests does not excuse undefined behavior. The compiler and target triple are part of the specification: behavior that is defined on one platform may be implementation-defined or undefined on another.

## Prerequisites and reconnaissance
1. Inspect language standard, compiler version, target triple, flags, build system, dependency locks, and sanitizer configuration.
2. Identify allocator ownership across every boundary, including FFI and plugin interfaces.
3. Determine the exact platform guarantees available (endianness, word size, alignment, atomics support).
4. Verify tool availability for sanitizers, fuzzers, debuggers, and cross-target builds before relying on them.

## Procedure
1. Inspect language standard, compiler version, target triple, flags, build system, dependency locks, and sanitizer configuration.
2. Trace ownership and lifetime. In Rust, justify every unsafe block with preconditions, invariants, aliasing rules, and safety comments. In C/C++, trace initialization, ownership, destruction, exception paths, and RAII.
3. Check overflow, signedness, narrowing, pointer provenance, bounds, alignment, endianness, and untrusted lengths.
4. For concurrency, define happens-before relationships, synchronization ownership, cancellation, shutdown, lock ordering, and race freedom; volatile is not thread synchronization.
5. For FFI/ABI, verify calling convention, struct/enum layout, symbol visibility, allocator ownership, panic/exception boundaries, and version compatibility.
6. Prefer safe APIs; isolate unavoidable unsafe code behind narrow wrappers and add property tests, fuzzing, sanitizers, or differential tests as appropriate.

## Decision tree
- Ownership is unclear → stop and map it before editing; unclear ownership is the root of most native defects.
- Unsafe block is proposed → require written preconditions and invariants; if they cannot be stated, redesign the interface.
- Input length or integer range is attacker-influenced → load security and bound it at the boundary with checked arithmetic.
- Cross-language struct crosses a boundary → verify layout with static assertions or generated bindings; never assume compiler defaults.
- Concurrency bug → identify happens-before and lock order before adding synchronization.
- Behavior differs across targets → record the target triple and consult the standard/compiler documentation; do not generalize from one platform.
- Compiler warnings appear → treat them as potential defects, not noise.

## Tool strategy
Use compiler warnings at the project's strict level, static analyzers, sanitizers (ASan/UBSan/TSan/MSan), Miri for Rust unsafe code, fuzzers for parsers and input surfaces, debuggers with symbol support, and cross-target builds. Verify version compatibility between sanitizer runtime and compiler. When a sanitizer is unavailable in the environment, record the gap rather than inferring correctness.

## Advanced techniques
- **Safety invariants as contracts:** document why an unsafe operation is valid and which subsequent code must preserve the invariant.
- **Layout verification:** use static assertions, generated bindings, and ABI dumps to prove struct/enum layout across compilers.
- **Provenance-aware pointer reasoning:** track where a pointer came from and what object it may address; do not infer validity from a nonzero value.
- **Concurrency model checks:** enumerate lock order, cancellation points, and shutdown paths; test with race detectors and stress loops.
- **Differential compilation:** compare behavior across optimization levels and compilers to expose UB-sensitive code.
- **Fuzz with oracles:** pair fuzzing with invariants or reference implementations, not just crash detection.

## Failure modes
- **Casts/transmute to silence type or layout errors** → hidden UB → remove the cast and fix the representation.
- **Assuming layouts are stable** → ABI break → verify with assertions and versioned bindings.
- **Adding locks without ownership and ordering rules** → deadlock or races → define the lock hierarchy first.
- **Ignoring overflow/signedness** → exploitable boundary bugs → use checked arithmetic on untrusted values.
- **Exception/panic across FFI** → undefined behavior or process abort → contain it at the boundary.

## Quality checklist
No new undefined behavior, data races, or unchecked bounds; unsafe code has minimal scope and explicit safety invariants; FFI ownership and ABI contracts are explicit; overflow, alignment, failure, and concurrency edges are tested.

## Anti-patterns
Relying on implementation-defined behavior without documentation; treating `volatile` as synchronization; raw pointer arithmetic on untrusted lengths; unchecked allocator/free pairs across module boundaries; disabling sanitizers to make a build pass.

## Verification
Run compiler warnings, format/lint, unit tests, ASan/UBSan/TSan or Miri as applicable, fuzz/property tests, and all supported target builds. Report which sanitizers and targets actually ran; mark others NOT VERIFIED.

## Output format
Invariants · ownership changes · ABI effects · unsafe surface · flags · tests · platform risks.

## Executable Verification & Failure Diagnostics
- **Verify**: Run compiler warnings, format/lint, unit tests, ASan/UBSan/TSan or Miri as applicable, fuzz/property tests, and all supported target builds.
- **Anti-Patterns**: Relying on implementation-defined behavior without documentation; treating `volatile` as synchronization
- **Failure Diagnostics**: A failing or ambiguous Verify result -> the first failing assertion or error line is the root cause, not the completion summary -> rerun the narrowest check named in Verify and inspect its first failing assertion.
