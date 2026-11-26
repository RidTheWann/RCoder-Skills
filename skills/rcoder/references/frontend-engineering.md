# Frontend and browser engineering

## Activate when
React/Vue/Svelte/Angular, browser interfaces, client state, routing, SSR, accessibility, or frontend architecture. Use web-platform-engineering for browser runtime/cache concerns and ui-ux-accessibility for detailed accessibility review.

## Mission and expertise
Own UI state coherence across URL, server, cache, and local state; implement accessible, secure, and measurable interfaces. Client-side checks are never authorization.

## Mental model
The frontend is a stateful distributed client: URL, server, cache, browser, accessibility tree, and user input must remain coherent. Stale writes and request races are correctness defects, not cosmetic issues.

## Prerequisites and reconnaissance
1. Identify framework/version, routing, state model, rendering mode, CSS system, browser support, and build/test pipeline.
2. Trace loading/error/empty/success states and state ownership before changing UI behavior.
3. Determine how server data is cached and invalidated and how mutations are sequenced.
4. Check accessibility conventions and existing component patterns in the repository.

## Procedure
1. Identify framework/version, routing, state model, rendering mode, CSS system, browser support, and build/test pipeline.
2. Trace loading/error/empty/success states and state ownership before changing UI behavior.
3. Keep URL state, server state, local state, and derived state distinct; prevent stale writes and request races.
4. Use semantic HTML, keyboard-operable controls, focus management, accessible names, contrast, and reduced-motion preferences.
5. Validate forms and sanitize untrusted content; never rely on client-only authorization.
6. Measure bundle size, hydration, layout shift, input latency, and network waterfall before optimizing.

## Decision tree
- Data needed in multiple distant components → define a single owner and explicit cache invalidation.
- Form validation → validate client-side for feedback and server-side for enforcement.
- Request race → cancel stale requests or sequence writes with a clear rule.
- Accessibility issue → fix semantics and keyboard access before adding visual polish.
- Rendering slow → profile before memoizing; identify actual re-render causes.
- SSR/hydration mismatch → verify deterministic initial state and serialization boundaries.
- New dependency → check bundle impact and maintenance cost before adding.

## Tool strategy
Use lint, type checks, component tests, accessibility audits, browser tests, production builds, and visual regression where configured. Verify framework and browser versions from configuration. Use synthetic data and local fixtures.

## Advanced techniques
- **State ownership map:** assign each piece of state to URL, server cache, or local component and document transitions.
- **Request sequencing:** use cancellation tokens or request IDs to discard stale responses.
- **Accessible-first components:** semantic elements, visible focus, labelled controls, and keyboard paths from the start.
- **Performance evidence:** measure input latency, layout shift, and bundle deltas before and after changes.
- **Error-state design:** define explicit loading, empty, error, and retry states for every async view.

## Failure modes
- **Divs as controls without semantics** → inaccessible UI → use native elements.
- **Global state for local concerns** → coupling and stale data → keep state local where possible.
- **Optimizing renders without profiling** → wasted effort → measure first.
- **Client-only authorization** → bypass → enforce server-side.
- **Unbounded client-side state** → memory growth → bound caches and lists.

## Quality checklist
Responsive and keyboard paths are tested; async/error/empty states are implemented; URL and server state remain coherent; security does not depend on client checks.

## Anti-patterns
Hidden focus outlines; infinite scroll without bounds; broad `any` casts on API data; mutating props or shared state; claiming accessibility without an audit.

## Verification
Run lint, type checks, component tests, production build, accessibility audits, browser tests, and visual regression where configured. Record exact versions and results; mark untested browsers NOT VERIFIED.

## Output format
Visible behavior · accessibility · state transitions · browser checks · performance evidence.

## Executable Verification & Failure Diagnostics
- **Verify**: Run lint, type checks, component tests, production build, accessibility audits, browser tests, and visual regression where configured.
- **Anti-Patterns**: Hidden focus outlines; infinite scroll without bounds
- **Failure Diagnostics**: A failing or ambiguous Verify result -> the first failing assertion or error line is the root cause, not the completion summary -> rerun the narrowest check named in Verify and inspect its first failing assertion.
