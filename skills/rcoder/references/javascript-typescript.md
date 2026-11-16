# JavaScript, TypeScript, and Node.js engineering

## Activate when
JavaScript/TypeScript, Node.js, frontend tooling, browser APIs, package scripts, async flows, or JS runtime integration.

## Mental model
Correctness depends on runtime and module semantics, type boundaries, event-loop scheduling, package resolution, browser compatibility, and supply-chain integrity.

## Procedure
1. Inspect package.json, lockfile, tsconfig, bundler, runtime engines, module type, lint rules, and supported browser/Node versions.
2. Preserve ESM/CommonJS boundaries and avoid ambiguous exports or dual-package hazards.
3. Use strict types at trust boundaries; validate runtime data because TypeScript types do not validate external input.
4. Handle promise rejection, cancellation, stream backpressure, and process shutdown explicitly.
5. Prevent prototype pollution, injection, unsafe HTML, path traversal, SSRF, and shell argument construction.
6. Measure bundle size and runtime before optimizing; avoid unnecessary polyfills and transitive dependencies.

## Quality checklist
- [ ] Runtime targets and module formats are explicit.
- [ ] External data is runtime-validated.
- [ ] Async operations have cancellation and error behavior.
- [ ] Bundle and dependency changes are justified.

## Anti-patterns
- Using any/unknown without narrowing at boundaries.
- Detached promises or swallowed rejections.
- Building shell commands through string concatenation.

## Verification
Run formatter/lint, tsc, tests, package build, lockfile checks, and supported browser/runtime tests.

## Output format
State runtime targets, type/API changes, dependency impact, async semantics, and verification.
