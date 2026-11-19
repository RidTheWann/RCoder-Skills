# Python engineering

## Activate when
Python packages, scripts, CLIs, services, data tooling, asyncio, packaging, or Python performance. Use systems-programming for native extension/ABI work and ml-ai-engineering for model-training or inference infrastructure.

## Mission and expertise
Own import/environment correctness, packaging metadata, typing, resource cleanup, async boundaries, and safe handling of external data. Preserve the project's lock strategy and supported interpreter matrix.

## Mental model
Python behavior depends on interpreter version, import resolution, environment isolation, packaging metadata, typing, and sync/async boundaries. Dynamic behavior means runtime validation and explicit cleanup matter more than annotation alone.

## Prerequisites and reconnaissance
1. Inspect pyproject.toml, lockfiles, supported Python versions, environment instructions, and CI before changing dependencies.
2. Determine package boundaries, public API, and typing conventions from existing code.
3. Identify async usage, blocking calls, and subprocess/network boundaries.
4. Verify the pinned formatter, linter, type checker, and test runner from configuration.

## Procedure
1. Inspect pyproject.toml, lockfiles, supported Python versions, environment instructions, and CI before changing dependencies.
2. Respect package boundaries, import style, public APIs, typing conventions, and pinned formatter/linter/test tooling.
3. Use context managers and explicit cleanup for files, sockets, subprocesses, and temporary paths.
4. Keep async code non-blocking; isolate blocking I/O or CPU-heavy work from the event loop.
5. Validate external data at boundaries; avoid unsafe deserialization, shell interpolation, eval/exec, and broad exception swallowing.
6. Profile before optimizing; understand semantics and memory costs before vectorizing or changing algorithms.

## Decision tree
- External input → validate and normalize with explicit types or a schema library already in use.
- Blocking call in async function → move to a thread/process executor or use an async library.
- Subprocess → pass argument lists, never shell strings; bound timeouts.
- Resource cleanup → use context managers; do not rely on garbage collection timing.
- New dependency → prove the standard library is insufficient, then pin and review it.
- Performance problem → profile with representative data before changing algorithms.
- Supported versions → test the full declared matrix or mark untested versions NOT VERIFIED.

## Tool strategy
Use pinned formatters, linters, type checkers, unit tests, package builds, and security scanners. Verify interpreter version and environment from CLI output. Prefer virtual environments or the project's declared isolation mechanism.

## Advanced techniques
- **Boundary validation:** normalize external data once at the edge and pass typed values inward.
- **Async isolation:** separate CPU-heavy and blocking I/O work from the event loop with explicit executors.
- **Deterministic resources:** inject paths, clocks, and subprocess runners so tests stay isolated.
- **Typed public API:** annotate public functions and validate types that come from dynamic sources.
- **Profile evidence:** report profiler output and workload characteristics before optimizing.

## Failure modes
- **Catching Exception and continuing** → corrupted state → catch specific errors and fail visibly.
- **Global mutable state** → hidden coupling and test interference → pass dependencies explicitly.
- **Dependencies for trivial tasks** → supply-chain cost → use the standard library when sufficient.
- **Unbounded subprocess output** → memory exhaustion → cap and stream output.
- **Unsafe deserialization** → code execution → use safe formats and validate schemas.

## Quality checklist
Supported interpreter versions are explicit and tested; dependencies follow the existing lock strategy; public APIs have meaningful types and stable behavior; resource cleanup and exception paths are covered.

## Anti-patterns
Mutable default arguments; wildcard imports in libraries; `eval`/`exec` on data; logging secrets; silent broad exception handling.

## Verification
Run pinned formatters, linters, type checkers, unit tests, package builds, and project security scans. Record interpreter version, exact commands, and results.

## Output format
Python/runtime versions · packaging/API changes · exact checks · dependency risks.
