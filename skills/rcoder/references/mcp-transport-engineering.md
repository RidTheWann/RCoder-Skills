# MCP transport engineering

## Activate when
Designing, implementing, securing, or debugging an MCP server transport or protocol adapter: stdio framing, Streamable HTTP, SSE compatibility, protocol version negotiation, request lifecycle, authentication, Origin validation, sessions, structured tool results, pagination, cancellation, or transport conformance. Do not activate for a host-only plugin manifest or Agent Skill discovery task that does not change MCP wire behavior; use agent-extensions-engineering. Do not activate for a generic REST endpoint without MCP semantics; use api-protocol-engineering.

## Mission and expertise
Own the wire-level behavior and transport security of MCP servers and adapters. Define a transport-independent protocol contract, ensure all transports reach the same core semantics, and prove behavior with protocol-level tests. Host-specific discovery and user interface packaging remain the responsibility of agent-extensions-engineering. Authentication design that is broader than MCP belongs with security and the relevant narrow security specialist.

## Mental model
MCP has two coupled but distinct layers: a protocol lifecycle and a transport. A transport moves JSON-RPC messages; it must not silently redefine tool semantics, permissions, output structure, or resource confinement. A successful local stdio test proves neither Streamable HTTP security nor native-host invocation. A valid HTTP response proves neither that the host discovered the server nor that its model called the tool.

Treat every transport as a trust boundary. Request headers, Origin, JSON-RPC bodies, cursor values, resource URIs, and tool output are untrusted input. The MCP method name and JSON-RPC body must agree with transport headers. Tool annotations are declarations, not enforcement. A read-only tool must remain read-only in every adapter.

## Prerequisites and reconnaissance
1. Record the exact MCP protocol revision(s), host/client versions, transport(s), and compatibility promises.
2. Inspect the existing JSON-RPC dispatcher, schemas, method registry, output clipping, root-confinement logic, and test fixtures before introducing an adapter.
3. Identify whether the server is stateful or stateless, whether a session ID is required, and how protocol-version negotiation is represented.
4. Define bind interfaces, authentication, Origin policy, CORS headers, request/response size bounds, timeout behavior, and secret redaction.
5. Check whether a formal protocol specification or host implementation has changed; do not infer support for SSE, sessions, resumability, or extensions from a generic HTTP example.

## Procedure
1. Write a transport-neutral contract for protocol revisions, JSON-RPC methods, list result envelopes, errors, structured output, cursor shape, and security invariants.
2. Keep stdio as a separate adapter: one valid UTF-8 JSON-RPC message per line, protocol-only stdout, diagnostics on stderr, notifications without responses, and deterministic process exit behavior.
3. For Streamable HTTP, implement only the documented endpoint and methods. Validate Content-Type, Accept, request body size, JSON-RPC envelope, protocol version, method header, and any required name/URI header before invoking the core.
4. Bind local-only services to loopback. Never silently expose a development MCP server on LAN or wildcard interfaces. Require a high-entropy bearer token, compare it in constant time, avoid logging it, and do not copy it into generated diagnostics.
5. If Origin is present, compare it to an exact configured allowlist. Reject hostile values; do not use substring, suffix, wildcard, or reflected-origin matching. Handle preflight with the same policy. Native clients that omit Origin may be accepted only when the authentication boundary remains explicit.
6. Share the same method dispatcher and strict schemas across transports. Avoid duplicating tool logic or creating transport-specific permission differences. Isolate request state so concurrent requests cannot leak a negotiated protocol version or selected root between clients.
7. Bound pagination, cursor length/offset, tool runtime, payload sizes, and output size. Cursor values are opaque to clients, versioned by the server, and validated against the correct collection.
8. Return structuredContent when a bounded typed result is available, while retaining compatible text content when the protocol requires it. Never mislabel free-form text as machine-readable structured data.
9. For resources and inline skill manifests, compute digests and sizes from the exact bytes served. Reject path traversal, symlink escapes, credential paths, and unlisted resources.
10. Build conformance tests for valid and invalid requests, notification behavior, wrong headers, bad Origin, missing/invalid tokens, unsupported versions, malformed cursors, resource confinement, concurrency, and legacy compatibility.
11. Verify the server with a scripted client, then test the exact host/client version. Report protocol conformance and native host invocation as separate evidence tiers.
12. Preserve raw, sanitized request/response artifacts and record the exact commit, protocol revision, command, exit status, and test environment.

## Decision tree
- Local process launch with line-framed JSON-RPC → stdio adapter.
- Browser/local HTTP client requiring MCP HTTP transport → Streamable HTTP only with loopback, token, exact Origin policy, bounds, and protocol-header checks.
- Client requires long-lived event streams, resumability, or session semantics → implement only when the selected MCP revision and host explicitly support it; do not pretend a JSON POST adapter is fully streaming.
- Tool list or resource catalogue exceeds a safe response size → bounded pagination with opaque cursors.
- Tool result is a bounded typed object → structuredContent plus compatible text; otherwise return text only.
- Host cannot launch local servers or expects a plugin extension → hand off the host manifest and installer to agent-extensions-engineering.

## Tool strategy
Use the protocol's official versioned specification, exact host/client documentation, JSON Schema validation, a loopback HTTP client, and deterministic stdio fixtures. Use subprocesses with argument arrays, fixed working roots, timeouts, and bounded captured output. Prefer Python standard-library HTTP servers only for deliberately small local adapters; choose a production-grade server framework when the deployment requirements justify it. Never claim the adapter is production-ready solely because it passed a localhost test.

## Advanced techniques
- **Shared dispatcher:** give every transport a single request entrypoint that validates and dispatches methods without maintaining duplicate tool registries.
- **Protocol-state isolation:** use immutable request context or isolated workers; if a core has mutable negotiation state, prove that parallel clients cannot cross-contaminate it.
- **Cursor integrity:** use opaque, versioned cursors with strict decoding, bounded offsets, collection scoping, and invalid-cursor tests. If source data can change between pages, document snapshot or weak-consistency semantics.
- **Header/body binding:** compare transport-level method/name/version headers with the JSON-RPC body. Reject disagreements before dispatch.
- **Loopback browser boundary:** combine loopback binding, bearer authentication, exact Origin checks, and no-store responses. CORS is not authentication.
- **Capability conformance:** test every advertised capability with an actual method call; do not advertise SSE, tasks, sampling, progress, or subscriptions because a schema field merely exists.
- **Version parity:** derive protocol constants, limits, and feature claims from one shared contract and test every adapter against it.

## Failure modes
- Shared mutable protocol state across threads → one client's version leaks into another request → isolate each request or dispatcher state and add concurrency tests.
- Bind to 0.0.0.0 for convenience → unauthenticated LAN exposure → refuse non-loopback bind by default and require a separately reviewed remote deployment design.
- Wildcard or reflected Origin → hostile web page can make local requests → exact allowlist and negative-origin tests.
- Cursor accepted without bounds → oversized scan or cross-collection confusion → strict opaque cursor parser with a maximum encoded length and offset.
- Different schemas in stdio and HTTP → permissions or validation drift → share the core dispatcher and compare registry/schema hashes in conformance tests.
- Claim SSE or sessions from a JSON POST-only adapter → client incompatibility → explicitly document the implemented subset and test the unsupported methods.
- structuredContent omitted or malformed → clients cannot reliably consume results → assert schema shape and retain a text representation.
- Live evidence from an earlier commit → false release confidence → record commit/protocol/version for every run and rerun after material changes.

## Quality checklist
- [ ] All transports call the same method registry and authorization boundary.
- [ ] Stdio stdout is protocol-only; notifications are not answered.
- [ ] HTTP binds only to the intended interfaces and enforces authentication and exact Origin policy.
- [ ] Content-Type, Accept, method/name/version headers, JSON-RPC body, size, and timeout are validated.
- [ ] Protocol state cannot leak across concurrent requests or roots.
- [ ] Cursor encoding, decoding, bounds, and collection scoping are tested.
- [ ] Structured results and inline resource digests describe the exact payload.
- [ ] Legacy protocol behavior is tested and remains intentional.
- [ ] Native host discovery and invocation are reported separately from local conformance.

## Anti-patterns
- Treating CORS as authentication.
- Exposing a development endpoint on all network interfaces.
- Duplicating MCP tool logic in every transport adapter.
- Accepting unknown headers or protocol revisions by silent downgrade.
- Treating cursor data as user-facing pagination state.
- Claiming full Streamable HTTP support from JSON POST tests alone.
- Reporting a green local test as proof of native host discovery or model behavior.

## Verification
Run the stdio and HTTP conformance suites against the same commit. Include valid requests, notifications, malformed JSON, unknown methods, invalid schemas, wrong protocol/method/name headers, missing and wrong bearer tokens, absent and hostile Origin, preflight, request-size/time limits, valid and invalid cursors, structuredContent, resource digests, traversal and symlink attempts, and parallel requests. Run legacy tests and verify the product-version and protocol-version parity. Then connect a native host using the exact documented version and retain sanitized tool-list and tool-call evidence; otherwise mark host discovery and invocation NOT VERIFIED.

## Output format
Protocol revisions and supported subset · transport architecture · shared tool contract · security boundaries and limits · conformance tests with exact results · host/client version and evidence tier · unsupported features · residual risks.

## Executable Verification & Failure Diagnostics
- **Verify**: Run the stdio and HTTP conformance suites against the same commit.
- **Anti-Patterns**: Treating CORS as authentication.; Exposing a development endpoint on all network interfaces.
- **Failure Diagnostics**: A failing or ambiguous Verify result -> the first failing assertion or error line is the root cause, not the completion summary -> rerun the narrowest check named in Verify and inspect its first failing assertion.
