# Language-specific implementation playbook

## Activate when
A high-impact change needs language-specific correctness beyond generic coding guidance.

## Mental model
Language idioms must never override repository conventions, type/runtime constraints, or evidence.

## Procedure
1. Read the target language's official versioned reference and project style before using new syntax or APIs.
2. Preserve public API, error semantics, concurrency guarantees, and dependency policy.
3. Prefer standard library and existing abstractions when they satisfy the requirement.
4. Review language-specific footguns: lifetime/ownership, nullability, implicit conversions, exceptions, panic, reflection, macro expansion, and async cancellation.
5. Add focused tests for boundary values, invalid states, and cross-platform behavior.

## Quality checklist
- [ ] Language/runtime assumptions are explicit.
- [ ] Idioms match the declared version.
- [ ] Public behavior and error semantics are preserved.
- [ ] Tests exercise language-specific failure modes.

## Anti-patterns
- Using syntax unsupported by the toolchain.
- Silencing compiler warnings instead of understanding them.
- Adding abstractions without a concrete invariant.

## Verification
Run the pinned compiler, formatter, linter, static analysis, unit/integration tests, and target builds.

## Output format
State language version, idioms chosen, compatibility risks, and verification evidence.
