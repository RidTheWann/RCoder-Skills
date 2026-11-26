# Application security engineering

## Activate when
Web/mobile security, OWASP-style assessment, sessions/auth flows, API security, browser security, or secure design. Do not activate for network/cloud infrastructure (use cloud-container-security or network-security) or for uncoordinated active probing (use authorized penetration-testing).

## Mission and expertise
Protect identities, sessions, data, business logic, and user-controlled interfaces across the request lifecycle. Own application-layer control review and defense design. Map controls to recognized standards without claiming blanket compliance.

## Mental model
Protect identities, sessions, data, business logic, and user-controlled interfaces across the request lifecycle. Authorization is per resource and per action, enforced server-side. Output encoding is context-specific; validation is about allowed shapes, not blocklists.

## Prerequisites and reconnaissance
1. Map authentication, authorization, session lifecycle, privilege transitions, routes, file handling, and sensitive data.
2. Identify the framework version and its built-in defenses (CSRF, escaping, session handling) from manifests and code.
3. Determine deployment context: browser, mobile client, API consumer, or embedded web view.
4. Confirm authorization scope before any active test; otherwise use source review and local fixtures.

## Procedure
1. Map authentication, authorization, session lifecycle, privilege transitions, routes, file handling, and sensitive data.
2. Check object/function access, tenant isolation, IDOR, CSRF, CORS, clickjacking, CSP, security headers, and origin validation.
3. Validate input at boundaries and encode output for its exact context; avoid string-built SQL, shell, HTML, LDAP, and templates.
4. Review password reset, MFA, recovery, rate limits, session rotation, cookie flags, and token revocation.
5. Assess uploads, archives, parsers, redirects, SSRF, webhook callbacks, and outbound request controls.
6. Use OWASP ASVS 5.0.0 as a requirements baseline when appropriate; map controls to evidence without claiming blanket compliance.

## Decision tree
- Missing per-object authorization → Confirmed access-control finding; add cross-user/tenant negative tests.
- Input reaches a templating, shell, or query sink via string concatenation → Confirmed injection class; parameterize or use safe APIs.
- CSRF defense relies on a custom header without origin checks → Potential; verify with a controlled local test.
- CORS allows wildcard origins with credentials → Confirmed misconfiguration; restrict origins explicitly.
- Upload handling accepts archives or active content → Potential; test decompression bounds and content handling locally.
- Token stored in insecure persistent client storage → Confirmed design weakness; define secure storage and revocation.
- Framework version is unverified → treat defense assumptions as unknown and verify from pinned docs.

## Tool strategy
Use route maps, framework configuration, dependency manifests, SAST, and local synthetic fixtures. Prefer static evidence and non-destructive local tests. Verify tool and framework versions before relying on default behaviors. Never send real user data to external scanners or services.

## Advanced techniques
- **Authorization matrix:** enumerate roles x actions x resources, including cross-tenant and unauthenticated rows, and test each.
- **Context-specific encoding:** distinguish HTML body, attribute, JavaScript, URL, and CSS contexts; one encoder does not fit all.
- **Session lifecycle tests:** verify rotation on privilege change, revocation on logout, idle/absolute expiry, and cookie flags.
- **SSRF controls:** enforce allowlists, block link-local/metadata addresses, and disable redirects to untrusted hosts.
- **Business logic abuse:** test negative amounts, replay, race on balances, and out-of-order state transitions.
- **Standards mapping:** map each control to ASVS or the OWASP Top 10 category with evidence, not to a compliance claim.

## Failure modes
- **Relying on hidden UI controls for access control** → bypass → enforce server-side per-resource authorization.
- **Wildcard CORS with credentials** → cross-origin data theft → explicit origin allowlist.
- **Storing bearer tokens in insecure persistent storage** → token theft → use platform-secure storage and short lifetimes.
- **Trusting client-side validation** → malformed data reaches sinks → validate again at the boundary.
- **Assuming framework defaults are enabled** → unprotected surface → verify configuration.

## Quality checklist
Authorization is tested across users/tenants; session and recovery flows resist takeover; contextual encoding and CSRF defenses exist; uploads and outbound requests are constrained; findings carry classification and confidence.

## Anti-patterns
Blocklist-only filters; disabling TLS verification for convenience; logging tokens or full request bodies; exposing stack traces; treating a passing scan as evidence of secure design.

## Verification
Run security regression tests, authorized SAST/DAST, authorization matrices, dependency scans, and platform-specific checks. Record exact commands, versions, and results; mark untested areas NOT VERIFIED.

## Output format
Scope · controls assessed · confirmed/potential findings with evidence · standards mapping · gaps · residual risk.

## Executable Verification & Failure Diagnostics
- **Verify**: Run security regression tests, authorized SAST/DAST, authorization matrices, dependency scans, and platform-specific checks.
- **Anti-Patterns**: Blocklist-only filters; disabling TLS verification for convenience
- **Failure Diagnostics**: A failing or ambiguous Verify result -> the first failing assertion or error line is the root cause, not the completion summary -> rerun the narrowest check named in Verify and inspect its first failing assertion.
