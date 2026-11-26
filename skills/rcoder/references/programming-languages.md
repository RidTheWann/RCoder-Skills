# Programming language and runtime routing

## Activate when
A task spans languages or the correct language/runtime specialist is unclear. Do not activate for a single known language with a single known specialist (load that specialist directly), or for non-language disciplines such as threat modeling or binary reverse engineering.

## Mission and expertise
Select the narrowest language/runtime specialist set from repository evidence and define cross-language contracts. Own the routing decision, not the implementation. Treat language choice as concrete compiler, runtime, memory, concurrency, ABI, and deployment constraints rather than syntax preference.

## Mental model
Treat language choice as concrete compiler, runtime, memory, concurrency, ABI, and deployment constraints—not syntax preference. Related languages are different runtimes; a repository may use several. Routing based on file extensions alone is unreliable.

## Prerequisites and reconnaissance
1. Identify exact language versions, compiler/runtime, target triple, package manager, build system, supported platforms, and CI commands from repository evidence.
2. Determine which languages actually execute, which are generated, and which appear only in fixtures or documentation.
3. Locate FFI/ABI or serialization boundaries between languages before selecting more than one specialist.
4. Check for project-local `.rcoder/references/` overrides that replace a built-in module.

## Procedure
1. Identify exact language versions, compiler/runtime, target triple, package manager, build system, supported platforms, and CI commands from repository evidence.
2. Select only the narrowest applicable specialist: systems-programming, python-engineering, javascript-typescript, dotnet-java-engineering, go-engineering, frontend-engineering, backend-api-engineering, database-engineering, mobile-engineering, game-engineering, embedded-engineering, ml-ai-engineering, build-toolchain-engineering, functional-programming, or distributed-systems-engineering. For Swift, Kotlin, PHP, Ruby, Dart/Flutter, Scala, Elixir, Haskell, R/Julia, and similar ecosystems, also consult polyglot-ecosystems.
3. Trace cross-language boundaries: ABI/FFI, serialization, process invocation, IPC, thread ownership, allocator ownership, and error propagation.
4. Verify version-specific behavior against official documentation and the actual toolchain; load only relevant specialists alongside core coding/testing/security guidance.

## Decision tree
- Single language, single known specialist → skip this router and load that specialist.
- Multiple languages in one repository → load this router plus each language's specialist only for the touched components.
- Native code called from managed code → load systems-programming plus the managed-language specialist; define ownership at the boundary.
- Data crosses a process or service boundary → add API/protocol or data/API specialist and define the schema contract.
- Language version is ambiguous → verify with version commands and lockfiles; do not assume the latest version.
- Change requires upgrading the toolchain → load build-toolchain-engineering and treat the upgrade as an explicit decision.
- No repository evidence is available → state the assumption, use the most conservative interpretation, and mark it in the handoff.

## Tool strategy
Use stack detection (`detect_stack.py`) as a heuristic map, manifests and lockfiles as authoritative evidence, version/help commands for actual toolchain behavior, and repository search for symbol usage. Never infer a runtime from a file extension without corroboration. Consult version-matched official documentation when behavior is uncertain.

## Advanced techniques
- **Boundary contract tables:** for each cross-language boundary, record calling convention or schema, allocator ownership, error mapping, and version compatibility.
- **Generated-source tracing:** identify which files are generated from schemas or IDL and change the source of truth, not output.
- **Target-matrix reasoning:** distinguish compile-time targets, runtime platforms, and CI-only platforms; a passing local build does not cover the matrix.
- **Version-skew detection:** compare lockfile, manifest, and installed versions to catch silent drift before debugging behavior.

## Failure modes
- **Guessing runtimes from file extensions alone** → wrong specialist and wrong idioms → verify against manifests.
- **Treating related languages as one runtime** → invalid memory/concurrency assumptions → route each runtime separately.
- **Implicit toolchain upgrade** → unrelated breakage → pin versions and handle upgrades explicitly.
- **Overloaded specialist set** → wasted context and conflicting advice → load only what the touched components require.

## Quality checklist
Language, runtime, compiler, and target versions are evidenced; cross-language contracts and ownership rules are tested; no toolchain upgrade is introduced implicitly; only directly relevant specialist modules are loaded.

## Anti-patterns
"It is all just C-like syntax"; copying an idiom from another runtime; loading every language module for a single-language change; treating a generated file as authoritative.

## Verification
Run pinned formatters, linters, type checkers, unit/integration tests, and supported target builds; mark unavailable platforms NOT VERIFIED. Confirm the selected specialists actually matched the touched files.

## Output format
Versions · selected specialists · boundary contracts · checks · compatibility risks.

## Executable Verification & Failure Diagnostics
- **Verify**: Run pinned formatters, linters, type checkers, unit/integration tests, and supported target builds; mark unavailable platforms NOT VERIFIED.
- **Anti-Patterns**: "It is all just C-like syntax"; copying an idiom from another runtime
- **Failure Diagnostics**: A failing or ambiguous Verify result -> the first failing assertion or error line is the root cause, not the completion summary -> rerun the narrowest check named in Verify and inspect its first failing assertion.
