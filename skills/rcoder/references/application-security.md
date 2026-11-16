# Application security engineering

## Activate when
Web/mobile security, OWASP-style assessment, sessions/auth flows, API security, browser security, or secure design.

## Mental model
Protect identities, sessions, data, business logic, and user-controlled interfaces across the request lifecycle.

## Procedure
1. Map authentication, authorization, session lifecycle, privilege transitions, routes, file handling, and sensitive data.
2. Check object/function access, tenant isolation, IDOR, CSRF, CORS, clickjacking, CSP, security headers, and origin validation.
3. Validate input at boundaries and encode output for its exact context; avoid string-built SQL, shell, HTML, LDAP, and templates.
4. Review password reset, MFA, recovery, rate limits, session rotation, cookie flags, and token revocation.
5. Assess uploads, archives, parsers, redirects, SSRF, webhook callbacks, and outbound request controls.
6. Use OWASP ASVS 5.0.0 as a requirements baseline when appropriate; map controls to evidence without claiming blanket compliance.

## Quality checklist
- [ ] Authorization is tested across users/tenants.
- [ ] Session and recovery flows resist takeover.
- [ ] Contextual encoding and CSRF defenses exist.
- [ ] Uploads and outbound requests are constrained.

## Anti-patterns
- Relying on hidden UI controls for access control.
- Wildcard CORS with credentials.
- Storing bearer tokens in insecure persistent storage.

## Verification
Run security regression tests, authorized SAST/DAST, authorization matrices, dependency scans, and platform-specific checks.

## Output format
Summarize scope, controls assessed, confirmed findings, standards mapping, and gaps.
