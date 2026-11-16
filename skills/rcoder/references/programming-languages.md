# Programming language and runtime routing

## Activate when
A task spans languages or the correct language/runtime specialist is unclear.

## Mental model
Treat language choice as concrete compiler, runtime, memory, concurrency, ABI, and deployment constraints—not syntax preference.

## Procedure
1. Identify exact language versions, compiler/runtime, target triple, package manager, build system, supported platforms, and CI commands from repository evidence.
2. Select only the narrowest applicable specialist: systems-programming, python-engineering, javascript-typescript, dotnet-java-engineering, go-engineering, frontend-engineering, backend-api-engineering, database-engineering, mobile-engineering, game-engineering, embedded-engineering, ml-ai-engineering, build-toolchain-engineering, functional-programming, or distributed-systems-engineering.
3. Trace cross-language boundaries: ABI/FFI, serialization, process invocation, IPC, thread ownership, allocator ownership, and error propagation.
4. Verify version-specific behavior against official documentation and the actual toolchain; load only relevant specialists alongside core coding/testing/security guidance.

## Quality checklist
- [ ] Language, runtime, compiler, and target versions are evidenced.
- [ ] Cross-language contracts and ownership rules are tested.
- [ ] No toolchain upgrade is introduced implicitly.
- [ ] Only directly relevant specialist modules are loaded.

## Anti-patterns
- Guessing runtimes from file extensions alone.
- Treating related languages as one runtime.
- Rewriting a component without measurable justification.

## Verification
Run pinned formatters, linters, type checkers, unit/integration tests, and supported target builds; mark unavailable platforms NOT VERIFIED.

## Output format
Report versions, selected specialists, boundary contracts, checks, and compatibility risks.
