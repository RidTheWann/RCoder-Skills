# Coding expert module

## Activate when
Source implementation, compiler/type errors, feature work, language idioms, or behavior changes in existing code. Do not activate for pure infrastructure configuration (use build/toolchain), security-only review (use security), or an unexplained intermittent failure with no known edit point (start with debugging).

## Mission and expertise
Own the implementation of a single cohesive behavior change in a codebase already understood. The module covers code reading, edit-point selection, contract preservation, language-idiomatic error handling, and failure-path testing. It does not own architecture decisions, threat modeling, or performance budgets; load those specialists when the task crosses into them.

## Mental model
The repository's runtime, dependencies, layering, and observable contracts are the local specification. A change is correct when it preserves existing contracts (unless explicitly changed and documented), handles the failure paths the language makes possible, and is demonstrated by tests that fail before and pass after. "It compiles" is necessary but not sufficient.

## Prerequisites and reconnaissance
1. Read the repository instructions, `git status`, and nearby implementation/tests before editing.
2. Identify the manifest, pinned runtime/compiler version, lockfile, and the project's format/lint/type/test commands from repository files, not from memory.
3. Trace callers, data flow, ownership, state mutation, resource lifetime, and error propagation to choose the smallest correct edit point.
4. Check whether a project-local `.rcoder/references/coding.md` overrides this module.

## Procedure
1. Read adjacent implementation/tests, manifest, runtime version, and project conventions.
2. Trace callers, inputs/outputs, state, resource ownership, and error paths before choosing the edit point.
3. Reuse existing abstractions and standard libraries; add dependencies only for a concrete, stated need.
4. Implement one cohesive behavior change; preserve public contracts unless the change is requested and documented.
5. Test success, invalid input, boundaries, and relevant failure behavior.
6. Run project-defined formatter/compiler/type/test commands, then inspect the final diff and untracked/generated files.
7. For ambiguous behavior, prefer a reversible assumption stated in the handoff over blocking on a question.

## Decision tree
- Error is a compile/type error with a clear local cause → fix the cause at the declaration site, not with casts or suppressions.
- Behavior crosses a module/service boundary → load architecture and treat the contract as part of the change.
- Change adds or accepts untrusted input → load security and treat validation as server-side at the trust boundary.
- Root cause is unknown or the failure is nondeterministic → stop and load debugging before editing.
- No existing test covers the touched behavior → add a focused regression test as part of the change.
- A dependency seems necessary → prove the standard library cannot meet the need with the pinned runtime first.

## Tool strategy
Use repository search to locate exact symbols before opening large files; prefer bounded reads. Use the project's own format/type/test commands from manifests. Use `detect_stack.py` for a heuristic manifest map on unfamiliar repositories. Never assume a formatter, linter, or package is installed; verify with a version/help call first. Use version-matched official documentation when a standard-library behavior is uncertain.

## Advanced techniques
- **Characterization tests:** before changing poorly documented code, capture current observable behavior in tests so unintended changes become visible.
- **Seam identification:** introduce the change at the narrowest interface that already separates responsibilities; avoid adding a new abstraction for a single caller.
- **Error-budget thinking:** decide explicitly which errors are recoverable, which must propagate, and which must abort; do not default everything to a generic catch.
- **Differential equivalence:** for refactors, compare outputs of old and new implementations over representative inputs before removing the old path.
- **Boundary matrices:** enumerate empty, null, maximum, minimum, duplicate, malformed, and concurrent cases for the specific type at the boundary.

## Failure modes
- **Symptom patching** (null guard, retry, sleep) → root cause not established → revert, reproduce, and load debugging.
- **Contract drift** → caller expectations changed silently → search all call sites and restore compatibility or version the interface.
- **Dependency creep** → a small feature adds a package → verify the need, pin the version, and review its supply-chain surface.
- **Version mismatch** → example copied from another runtime version → verify against the pinned version's documentation.
- **Hidden generated files** → edits overwritten by a build step → identify generated sources and change their input.

## Quality checklist
Types, ownership/lifetimes, nullability, and error semantics match the language. Async/concurrent work considers cancellation, timeout, and races. Resources are bounded and cleaned up. Tests assert observable behavior. The final diff contains only the intended change.

## Anti-patterns
Unrelated rewrites; broad catches with fabricated defaults; helpers that only rename one call; examples copied from another runtime version; weakening a failing test to obtain a green run; committing generated artifacts.

## Verification
Use the pinned runtime/lockfile; run the narrowest test first, then compile/type checks and the documented project gate. Verify a regression test fails on the pre-change code when feasible. Inspect the final diff and untracked files. Record any check that could not run and why.

## Output format
Behavior changed · files · exact checks/results · compatibility notes · assumptions · residual risks.

## Executable Verification & Failure Diagnostics
- **Verify**: Use the pinned runtime/lockfile; run the narrowest test first, then compile/type checks and the documented project gate.
- **Anti-Patterns**: Unrelated rewrites; broad catches with fabricated defaults
- **Failure Diagnostics**: A failing or ambiguous Verify result -> the first failing assertion or error line is the root cause, not the completion summary -> rerun the narrowest check named in Verify and inspect its first failing assertion.
