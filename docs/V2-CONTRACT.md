# RCoder 2.0 shared contract

This document describes the common contract that binds the portable skill, MCP core, transport adapters, CLI, and host plugins. The machine-readable source of truth is `skills/rcoder/contracts/rcoder-v2.json`; `rcoder_contract.py` is the Python adapter that reads it. Tests must compare implementations against the contract instead of copying protocol constants independently.

## Compatibility policy

- The current product version remains the manifest/package version (1.17.1 in this development branch). The 2.0 contract is a forward-compatible architecture contract, not a claim that the 2.0 release is complete.
- stdio remains the default transport. Existing host configurations are not rewritten to HTTP automatically.
- Legacy MCP clients continue through the existing legacy core. The modern stateless protocol is 2026-07-28.
- The Skills-over-MCP manifest remains inline in `skills/list`: every eligible resource has its exact URI, SHA-256 digest, and byte size. `resources/read` serves the exact bytes represented by that manifest.
- Structured tool results use `structuredContent` when the bounded helper result is a JSON object; text content remains for backwards compatibility.

## Pagination

List methods use an opaque base64url cursor that encodes a versioned offset. Page size is 10. The cursor is stateless and scoped to the method's returned collection; clients must treat it as opaque. Invalid, out-of-range, or unsupported cursors return Invalid params. The first supported collections are tools, resources, resource templates, prompts, and skills.

## Transport adapters

### stdio

- One UTF-8 JSON-RPC message per line.
- stdout contains protocol messages only; diagnostics go to stderr.
- The existing stdio transport remains the default for host installers.

### Streamable HTTP

- One endpoint, `POST /mcp`, implementing the stateless 2026-07-28 request shape.
- Local server binds only to `127.0.0.1`; non-loopback binding is rejected.
- Every request requires `Authorization: Bearer ...`; the token is read from `RCODER_MCP_TOKEN` by default and never printed.
- If `Origin` is present it must exactly match an explicitly allowed origin. Native clients that omit Origin remain supported. Invalid present Origin values receive 403.
- `MCP-Protocol-Version` must match the JSON body metadata. `Mcp-Method` mirrors the JSON-RPC method; `Mcp-Name` mirrors the selected name/URI for tool, prompt, and resource calls.
- This adapter returns JSON responses. It does not claim SSE streaming, protocol sessions, GET streams, or resumable streams.

## Shared adapter invariants

All transports call the same modern JSON-RPC entry point and share:
- protocol/version contract;
- strict input validation in the MCP core;
- output bounding and structured content;
- pagination and cursor validation;
- inline skill manifest computation;
- root confinement and sensitive-file refusal.

Host adapters may add discovery, commands, and UI affordances, but must not silently widen core tool permissions. Host-native discovery and model invocation are measured separately in `docs/COMPATIBILITY.md`.

## Verification gates

`scripts/test-mcp-contract.py` checks version/protocol parity, tool registry parity, cursor pagination, and inline manifest integrity. `scripts/test-mcp-http.py` checks transport authentication and HTTP framing. `scripts/validate-all` and the Ubuntu/Windows CI matrix register all conformance tests. Real host activation and live ablation remain separate evidence and must not be inferred from CI.
