# JavaScript, TypeScript, and Node.js engineering

## Activate when
JavaScript/TypeScript, Node.js, frontend tooling, browser APIs, package scripts, async flows, or JS runtime integration. Use web-platform-engineering for browser/cache/SSR concerns and application-security for control review.

## Mission and expertise
Own runtime/module semantics, type-boundary validation, event-loop behavior, package resolution, and supply-chain integrity. Types describe intent; they do not validate external input.

## Mental model
Correctness depends on runtime and module semantics, type boundaries, event-loop scheduling, package resolution, browser compatibility, and supply-chain integrity. A green type check is not evidence that runtime data is safe.

## Prerequisites and reconnaissance
1. Inspect package.json, lockfile, tsconfig, bundler, runtime engines, module type, lint rules, and supported browser/Node versions.
2. Determine ESM/CommonJS boundaries and whether dual-package hazards are possible.
3. Identify runtime validation at external boundaries and how async errors are handled.
4. Check lifecycle scripts and dependency provenance before adding packages.

## Procedure
1. Inspect package.json, lockfile, tsconfig, bundler, runtime engines, module type, lint rules, and supported browser/Node versions.
2. Preserve ESM/CommonJS boundaries and avoid ambiguous exports or dual-package hazards.
3. Use strict types at trust boundaries; validate runtime data because TypeScript types do not validate external input.
4. Handle promise rejection, cancellation, stream backpressure, and process shutdown explicitly.
5. Prevent prototype pollution, injection, unsafe HTML, path traversal, SSRF, and shell argument construction.
6. Measure bundle size and runtime before optimizing; avoid unnecessary polyfills and transitive dependencies.

## Decision tree
- External JSON or request body → validate at runtime with a schema; do not cast to a type.
- Async task may be abandoned → provide cancellation and handle rejection explicitly.
- Streams → respect backpressure; unbounded buffers exhaust memory.
- Module format mismatch → verify package exports and runtime resolution before changing imports.
- New dependency → justify it, pin it, and review lifecycle scripts.
- Bundle grew → inspect the dependency graph before changing build flags.
- Shell invocation → use argument arrays, never string concatenation.

## Tool strategy
Use the project's formatter, linter, type checker, test runner, and package tools. Verify Node and TypeScript versions from manifests and CLI output. Prefer local fixtures over external services. Check license and installation scripts of new dependencies.

## Advanced techniques
- **Runtime schema validation:** validate and normalize untrusted data at every external boundary.
- **Async lifecycle:** attach rejection handlers, bound concurrency, and define shutdown behavior.
- **Module boundary maps:** document which packages are ESM, CJS, or dual and how they are consumed.
- **Prototype-pollution defenses:** reject `__proto__`/constructor keys from untrusted objects and use safe merge utilities.
- **Bundle evidence:** compare measured sizes and dependency deltas rather than guessing impact.

## Failure modes
- **Using any/unknown without narrowing** → unsafe assumptions → validate at the boundary.
- **Detached promises or swallowed rejections** → silent failures → await or handle explicitly.
- **Shell commands through string concatenation** → injection → use argument arrays.
- **Unbounded streams/queues** → memory exhaustion → apply backpressure and limits.
- **Unreviewed transitive dependencies** → supply-chain risk → pin and inspect.

## Quality checklist
Runtime targets and module formats are explicit; external data is runtime-validated; async operations have cancellation and error behavior; bundle and dependency changes are justified.

## Anti-patterns
`eval` on untrusted input; disabling strict mode; global mutable singletons for request state; `process.env` secrets in logs; treating a passing type check as security validation.

## Verification
Run formatter/lint, tsc, tests, package build, lockfile checks, and supported browser/runtime tests. Record exact runtime versions and results; mark untested targets NOT VERIFIED.

## Output format
Runtime targets · type/API changes · dependency impact · async semantics · verification.
