# C, C++, Rust, and systems programming

## Activate when
Native code, memory ownership, unsafe blocks, concurrency, FFI, OS APIs, binary formats, emulators, compilers, or performance-critical systems.

## Mental model
Correctness depends on object lifetime, ownership, aliasing, memory model, ABI, alignment, integer width, data races, and platform behavior. Passing tests does not excuse undefined behavior.

## Procedure
1. Inspect language standard, compiler version, target triple, flags, build system, dependency locks, and sanitizer configuration.
2. Trace ownership and lifetime. In Rust, justify every unsafe block with preconditions, invariants, aliasing rules, and safety comments. In C/C++, trace initialization, ownership, destruction, exception paths, and RAII.
3. Check overflow, signedness, narrowing, pointer provenance, bounds, alignment, endianness, and untrusted lengths.
4. For concurrency, define happens-before relationships, synchronization ownership, cancellation, shutdown, lock ordering, and race freedom; volatile is not thread synchronization.
5. For FFI/ABI, verify calling convention, struct/enum layout, symbol visibility, allocator ownership, panic/exception boundaries, and version compatibility.
6. Prefer safe APIs; isolate unavoidable unsafe code behind narrow wrappers and add property tests, fuzzing, sanitizers, or differential tests as appropriate.

## Quality checklist
- [ ] No new undefined behavior, data races, or unchecked bounds.
- [ ] Unsafe code has minimal scope and explicit safety invariants.
- [ ] FFI ownership and ABI contracts are explicit.
- [ ] Overflow, alignment, failure, and concurrency edges are tested.

## Anti-patterns
- Using casts/transmute to silence type or layout errors.
- Assuming layouts are stable without proof.
- Adding locks without ownership and ordering rules.

## Verification
Run compiler warnings, format/lint, unit tests, ASan/UBSan/TSan or Miri as applicable, fuzz/property tests, and all supported target builds.

## Output format
Describe invariants, ownership changes, ABI effects, unsafe surface, flags, tests, and platform risks.
