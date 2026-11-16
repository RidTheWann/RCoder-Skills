# Coding expert module

## Activate when
Source implementation, compile/type errors, feature work, or language/framework changes.

## Mental model
The repository's runtime, dependencies, layering, and observable contracts are the local specification.

## Procedure
1. Read adjacent implementation/tests, manifest, runtime version, and project conventions.
2. Trace callers, inputs/outputs, state, resource ownership, and error paths before choosing the edit point.
3. Reuse existing abstractions and standard libraries; add dependencies only for a concrete need.
4. Implement one cohesive behavior change; preserve public contracts unless change is requested and documented.
5. Test success, invalid input, boundaries, and relevant failure behavior.
6. Run project-defined formatter/compiler/type/test commands, then inspect the final diff.

## Quality checklist
Types, ownership/lifetimes, nullability, and error semantics match the language. Async/concurrent work considers cancellation, timeout, and races. Resources are bounded and cleaned up. Tests assert observable behavior.

## Anti-patterns
Unrelated rewrites; broad catches with fabricated defaults; helpers that only rename one call; examples copied from another runtime version.

## Verification
Use the pinned runtime/lockfile; run narrow tests first, then compile/type checks and documented gates.

## Output format
Behavior changed · files · exact checks/results · compatibility notes · residual risks.
