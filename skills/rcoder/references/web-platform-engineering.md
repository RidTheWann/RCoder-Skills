# Web platform, server rendering, and browser runtime engineering

## Activate when
SSR/SSG/ISR, hydration, service workers, Web Workers, browser storage, web components, edge runtimes, or browser compatibility.

## Mental model
Browser and edge code runs across multiple origins, execution contexts, caches, and lifecycle states. Treat browser APIs, network responses, and persisted client state as untrusted.

## Procedure
1. Identify browser support matrix, rendering mode, framework/runtime, edge restrictions, service-worker scope, and deployment/CDN behavior.
2. Model hydration and server/client data ownership; prevent unsafe serialization and mismatched state.
3. Review CSP, Trusted Types, CORS, cookie SameSite/Secure/HttpOnly, CSRF, origin checks, and content security boundaries.
4. Treat localStorage, IndexedDB, URL parameters, postMessage, service-worker messages, and cache contents as untrusted inputs.
5. For workers, define message schemas, transfer ownership, cancellation, termination, and resource limits.
6. Check cache keys, vary headers, stale data, user-specific response caching, and CDN invalidation.
7. For browser compatibility, feature-detect capabilities and use documented fallbacks without silently weakening security.
8. Measure performance using field metrics and representative throttled conditions; distinguish lab measurements from real-user data.

## Quality checklist
- [ ] Rendering and hydration state are consistent.
- [ ] Cross-origin and browser storage boundaries are defended.
- [ ] Worker messages and resource use are bounded.
- [ ] Caching cannot leak user-specific data.
- [ ] Supported browsers and fallback behavior are tested.

## Anti-patterns
- Putting secrets or authorization decisions in browser storage.
- Using wildcard postMessage origins.
- Caching personalized responses in a shared cache without safe variation.

## Verification
Run browser integration tests, CSP/security-header checks, SSR/hydration tests, service-worker update tests, and performance traces on supported engines.

## Output format
State rendering/deployment model, trust boundaries, caching rules, browser matrix, performance evidence, and risks.
