# Web platform, server rendering, and browser runtime engineering

## Activate when
SSR/SSG/ISR, hydration, service workers, Web Workers, browser storage, web components, edge runtimes, or browser compatibility. Use frontend-engineering for component/UI structure and application-security for the broader control review.

## Mission and expertise
Own correctness and trust boundaries across server, browser, worker, edge, and cache contexts. Treat browser APIs, network responses, and persisted client state as untrusted, and make caching and hydration behavior explicit.

## Mental model
Browser and edge code runs across multiple origins, execution contexts, caches, and lifecycle states. Treat browser APIs, network responses, and persisted client state as untrusted. Client-side state is never an authorization decision.

## Prerequisites and reconnaissance
1. Identify browser support matrix, rendering mode, framework/runtime, edge restrictions, service-worker scope, and deployment/CDN behavior.
2. Determine which data is rendered on the server, which is hydrated on the client, and who owns each piece of state.
3. Identify all cross-context channels: postMessage, storage, service-worker messages, URL parameters, and cache keys.
4. Confirm the security headers and CSP policy actually deployed.

## Procedure
1. Identify browser support matrix, rendering mode, framework/runtime, edge restrictions, service-worker scope, and deployment/CDN behavior.
2. Model hydration and server/client data ownership; prevent unsafe serialization and mismatched state.
3. Review CSP, Trusted Types, CORS, cookie SameSite/Secure/HttpOnly, CSRF, origin checks, and content security boundaries.
4. Treat localStorage, IndexedDB, URL parameters, postMessage, service-worker messages, and cache contents as untrusted inputs.
5. For workers, define message schemas, transfer ownership, cancellation, termination, and resource limits.
6. Check cache keys, vary headers, stale data, user-specific response caching, and CDN invalidation.
7. For browser compatibility, feature-detect capabilities and use documented fallbacks without silently weakening security.
8. Measure performance using field metrics and representative throttled conditions; distinguish lab measurements from real-user data.

## Decision tree
- Personalized response caching → include identity-relevant dimensions in the cache key or disable shared caching.
- Hydration mismatch → verify serialization boundaries and deterministic initial state before changing framework code.
- postMessage handler → validate origin and schema; never accept wildcard origin with privileged actions.
- Worker needs large data → transfer ownership where possible; bound message sizes and worker lifetime.
- Service worker must be updated → define versioning, cache invalidation, and rollback of a broken worker.
- Browser lacks a feature → feature-detect and provide a documented fallback; do not weaken security for compatibility.
- Performance claim → use field metrics where available; label lab-only measurements as such.

## Tool strategy
Use browser integration tests, security-header/CSP checks, hydration tests, service-worker update tests, and performance traces on supported engines. Verify browser/engine versions. Use synthetic data and local fixtures; never rely on real user data for cache tests.

## Advanced techniques
- **Context inventory:** list every execution context and the validated schema of messages crossing between them.
- **Cache-key audit:** verify that every user-specific or authorization-dependent response cannot collide in a shared cache.
- **Serialization safety:** encode data for its exact context and avoid injecting structured data into HTML unsafely.
- **Lifecycle tests:** verify worker and service-worker startup, update, termination, and recovery paths.
- **Field vs lab metrics:** report both and state which environments were actually measured.

## Failure modes
- **Secrets or authorization decisions in browser storage** → client-side compromise → keep on server.
- **Wildcard postMessage origins** → cross-origin abuse → validate exact origins and schemas.
- **Caching personalized responses in a shared cache** → data leak → vary keys correctly or disable caching.
- **Unbounded worker messages** → memory exhaustion → bound and validate.
- **Assuming one browser's behavior** → compatibility failures → test the supported matrix.

## Quality checklist
Rendering and hydration state are consistent; cross-origin and browser storage boundaries are defended; worker messages and resource use are bounded; caching cannot leak user-specific data; supported browsers and fallback behavior are tested.

## Anti-patterns
- Trusting client state for authorization; disabling CSP for convenience; unbounded cache lifetimes; using `postMessage('*')` for privileged actions; claiming cross-browser support without tests.

## Verification
Run browser integration tests, CSP/security-header checks, SSR/hydration tests, service-worker update tests, and performance traces on supported engines. Record engine versions and results; mark untested browsers NOT VERIFIED.

## Output format
Rendering/deployment model · trust boundaries · caching rules · browser matrix · performance evidence · risks.

## Executable Verification & Failure Diagnostics
- **Verify**: Run browser integration tests, CSP/security-header checks, SSR/hydration tests, service-worker update tests, and performance traces on supported engines.
- **Anti-Patterns**: Trusting client state for authorization; disabling CSP for convenience
- **Failure Diagnostics**: A failing or ambiguous Verify result -> the first failing assertion or error line is the root cause, not the completion summary -> rerun the narrowest check named in Verify and inspect its first failing assertion.
