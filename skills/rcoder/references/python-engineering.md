# Python engineering

## Activate when
Python packages, scripts, CLIs, services, data tooling, asyncio, packaging, or Python performance.

## Mental model
Python behavior depends on interpreter version, import resolution, environment isolation, packaging metadata, typing, and sync/async boundaries.

## Procedure
1. Inspect pyproject.toml, lockfiles, supported Python versions, environment instructions, and CI before changing dependencies.
2. Respect package boundaries, import style, public APIs, typing conventions, and pinned formatter/linter/test tooling.
3. Use context managers and explicit cleanup for files, sockets, subprocesses, and temporary paths.
4. Keep async code non-blocking; isolate blocking I/O or CPU-heavy work from the event loop.
5. Validate external data at boundaries; avoid unsafe deserialization, shell interpolation, eval/exec, and broad exception swallowing.
6. Profile before optimizing; understand semantics and memory costs before vectorizing or changing algorithms.

## Quality checklist
- [ ] Supported interpreter versions are explicit and tested.
- [ ] Dependencies follow the existing lock strategy.
- [ ] Public APIs have meaningful types and stable behavior.
- [ ] Resource cleanup and exception paths are covered.

## Anti-patterns
- Catching Exception and continuing with corrupted state.
- Using global mutable state for hidden coordination.
- Adding dependencies for trivial standard-library tasks.

## Verification
Run pinned formatters, linters, type checkers, unit tests, package builds, and project security scans.

## Output format
Report Python/runtime versions, packaging/API changes, exact checks, and dependency risks.
