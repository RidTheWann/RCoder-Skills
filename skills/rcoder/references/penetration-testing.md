# Authorized penetration testing

## Activate when
A user explicitly requests an assessment of owned or authorized systems, including scoped web/API/network/mobile/cloud engagements.

## Mental model
Penetration testing is controlled validation. Written scope, rules of engagement, safety controls, and evidence handling take precedence over technical curiosity.

## Procedure
1. Require written scope: targets, ownership/authorization, exclusions, dates, source IPs, accounts, permitted techniques, rate limits, data handling, emergency contacts, and stop conditions.
2. Map the plan to OWASP WSTG/ASVS, MASVS, API Security Top 10, or relevant domain standards.
3. Start with passive reconnaissance and configuration/source review; confirm active-test permission before sending probes.
4. Use non-destructive validation first; avoid persistence, destructive payloads, service disruption, social engineering, credential spraying, or data exfiltration unless explicitly scoped.
5. Use synthetic accounts/data; stop when real customer data, service instability, or an out-of-scope system is encountered.
6. Record timestamps, tools/versions, requests/responses, preconditions, impact, reproducibility, and confidence; redact secrets and PII.
7. Validate fixes with regression tests and retest original conditions; close with limitations and residual findings.

## Quality checklist
- [ ] Written authorization and scope are recorded.
- [ ] Active testing follows allowed techniques and rate limits.
- [ ] Evidence is minimal, redacted, and reproducible.
- [ ] Stop conditions and escalation contacts are defined.

## Anti-patterns
- Scanning public targets without permission.
- Using destructive techniques when non-destructive evidence suffices.
- Exfiltrating real data or maintaining access to prove impact.
- Treating scanner output as verified findings.

## Verification
Run only approved tests inside scope; preserve evidence; retest fixes safely; report untested areas and limitations.

## Output format
Report scope, methodology, findings, evidence, impact, remediation, retest status, and residual risk.
