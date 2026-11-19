# Language-specific implementation playbook

## Activate when
A high-impact change needs language-specific correctness beyond generic coding guidance. Use programming-languages to choose the ecosystem and a dedicated language module when one exists.

## Mission and expertise
Apply correct, version-matched language idioms without overriding repository conventions, runtime constraints, or evidence. Own the identification of language-specific footguns and their focused tests.

## Mental model
Language idioms must never override repository conventions, type/runtime constraints, or evidence. The pinned toolchain defines which syntax and APIs exist; memory of another version is not a specification.

## Prerequisites and reconnaissance
1. Read the target language's official versioned reference and project style before using new syntax or APIs.
2. Identify the exact compiler/runtime version, target platform, and dependency constraints.
3. Determine public API and error-semantics expectations from existing code and tests.
4. Check whether the repository has local guidance that replaces built-in modules.

## Procedure
1. Read the target language's official versioned reference and project style before using new syntax or APIs.
2. Preserve public API, error semantics, concurrency guarantees, and dependency policy.
3. Prefer standard library and existing abstractions when they satisfy the requirement.
4. Review language-specific footguns: lifetime/ownership, nullability, implicit conversions, exceptions, panic, reflection, macro expansion, and async cancellation.
5. Add focused tests for boundary values, invalid states, and cross-platform behavior.

## Decision tree
- Syntax may be unsupported → verify against the pinned toolchain before using it.
- Compiler warning appears → understand and fix it; do not silence it generically.
- Abstraction improves nothing → avoid it; prefer explicit code.
- Error semantics would change → treat as a contract change and update callers/tests.
- Cross-platform behavior differs → test each declared target or mark it NOT VERIFIED.
- Language guidance conflicts with repository convention → follow the repository convention, unless it is unsafe.

## Tool strategy
Use the pinned compiler, formatter, linter, static analyzer, and test runner. Verify versions from CLI output and manifests. Consult version-matched official documentation; mark external verification unavailable when documentation cannot be accessed.

## Advanced techniques
- **Footgun checklist:** enumerate the language's undefined/implementation-defined behaviors relevant to the change.
- **Contract preservation:** compare public signatures and error behavior before and after the change.
- **Boundary-value tests:** exercise minimum, maximum, empty, null, and malformed inputs specific to the type system.
- **Toolchain matrix:** build and test all declared targets; record which are unavailable.

## Failure modes
- **Using syntax unsupported by the toolchain** → build failure → verify version support.
- **Silencing compiler warnings** → hidden defects → fix the cause.
- **Adding abstractions without a concrete invariant** → complexity → keep it explicit.
- **Porting idioms blindly** → semantic drift → verify equivalence in the target language.

## Quality checklist
Language/runtime assumptions are explicit; idioms match the declared version; public behavior and error semantics are preserved; tests exercise language-specific failure modes.

## Anti-patterns
Copying examples from a different language version; treating a linter pass as correctness; using unsafe features without justification; changing error types without updating callers.

## Verification
Run the pinned compiler, formatter, linter, static analysis, unit/integration tests, and target builds. Record exact versions and results.

## Output format
Language version · idioms chosen · compatibility risks · verification evidence.
