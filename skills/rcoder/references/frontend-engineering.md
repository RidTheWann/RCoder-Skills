# Frontend and browser engineering

## Activate when
React/Vue/Svelte/Angular, browser interfaces, client state, routing, SSR, accessibility, or frontend architecture.

## Mental model
The frontend is a stateful distributed client: URL, server, cache, browser, accessibility tree, and user input must remain coherent.

## Procedure
1. Identify framework/version, routing, state model, rendering mode, CSS system, browser support, and build/test pipeline.
2. Trace loading/error/empty/success states and state ownership before changing UI behavior.
3. Keep URL state, server state, local state, and derived state distinct; prevent stale writes and request races.
4. Use semantic HTML, keyboard-operable controls, focus management, accessible names, contrast, and reduced-motion preferences.
5. Validate forms and sanitize untrusted content; never rely on client-only authorization.
6. Measure bundle size, hydration, layout shift, input latency, and network waterfall before optimizing.

## Quality checklist
- [ ] Responsive and keyboard paths are tested.
- [ ] Async/error/empty states are implemented.
- [ ] URL and server state remain coherent.
- [ ] Security does not depend on client checks.

## Anti-patterns
- Using divs as controls without semantics.
- Global state for local concerns.
- Optimizing renders without profiling.

## Verification
Run lint, type checks, component tests, production build, accessibility audits, browser tests, and visual regression where configured.

## Output format
Summarize visible behavior, accessibility, state transitions, browser checks, and performance evidence.
