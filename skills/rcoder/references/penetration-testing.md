# Authorized penetration testing

## Activate when
A user explicitly requests an assessment of owned or authorized systems, including scoped web/API/network/mobile/cloud engagements. Do not activate when authorization or scope is missing; fall back to passive source/configuration review and synthetic fixtures.

## Mission and expertise
Perform controlled validation of security controls inside a defined scope. Written scope, rules of engagement, safety controls, and evidence handling take precedence over technical curiosity. Own the engagement discipline: authorization, boundaries, rate limits, stop conditions, evidence, and retest.

## Mental model
Penetration testing is controlled validation, not unrestricted attack. Non-destructive proof is preferred; persistence, lateral movement, data exfiltration, and disruption are excluded unless explicitly authorized. A finding requires reproducibility, impact, and confidence, not just a tool output.

## Prerequisites and reconnaissance
1. Require written scope: targets, ownership/authorization, exclusions, dates, source IPs, accounts, permitted techniques, rate limits, data handling, emergency contacts, and stop conditions.
2. Verify the requester's authority to approve testing of the named assets; do not rely on an informal claim.
3. Prepare synthetic accounts and data; confirm monitoring and rollback paths exist.
4. Record tool versions and confirm they are permitted by the rules of engagement.

## Procedure
1. Require written scope: targets, ownership/authorization, exclusions, dates, source IPs, accounts, permitted techniques, rate limits, data handling, emergency contacts, and stop conditions.
2. Map the plan to OWASP WSTG/ASVS, MASVS, API Security Top 10, or relevant domain standards.
3. Start with passive reconnaissance and configuration/source review; confirm active-test permission before sending probes.
4. Use non-destructive validation first; avoid persistence, destructive payloads, service disruption, social engineering, credential spraying, or data exfiltration unless explicitly scoped.
5. Use synthetic accounts/data; stop when real customer data, service instability, or an out-of-scope system is encountered.
6. Record timestamps, tools/versions, requests/responses, preconditions, impact, reproducibility, and confidence; redact secrets and PII.
7. Validate fixes with regression tests and retest original conditions; close with limitations and residual findings.

## Decision tree
- No written authorization → no active testing; passive review only and label active checks NOT VERIFIED.
- Target is outside the listed scope or ownership is unclear → stop and escalate.
- Non-destructive evidence suffices → stop there; do not escalate to exploitation.
- Real user data or an out-of-scope system appears → invoke stop conditions and notify the contact.
- Finding requires destructive proof → report as Unverified Hypothesis with prerequisites; request explicit authorization.
- Service becomes unstable → stop active tests, preserve evidence, and escalate immediately.
- Retest after remediation → reproduce the original condition with the same safe method; confirm the fix and add a regression test.

## Tool strategy
Use passive information sources and authorized scanners first, then manual validation with synthetic data. Bound request rates and concurrency. Use isolated labs for any sample execution. Verify each tool is permitted and version-recorded. Redact all sensitive values from captures and reports.

## Advanced techniques
- **Rules-of-engagement checklist:** turn scope into an explicit machine-checkable list of targets, methods, exclusions, and limits.
- **Non-destructive proof:** demonstrate impact with a benign marker on a synthetic resource rather than real data.
- **Evidence chain:** preserve timestamps, tool versions, exact requests/responses, and hashes of captured artifacts.
- **Rate and blast-radius control:** cap concurrency and total requests; monitor for availability impact.
- **Finding classification:** Confirmed, Potential, Informational, False Positive, or Unverified Hypothesis with confidence.
- **Retest protocol:** re-run the original safe reproduction after the fix and confirm negative behavior is enforced.

## Failure modes
- **Scanning public targets without permission** → legal and policy harm → require written scope.
- **Using destructive techniques when non-destructive evidence suffices** → damage → use minimal proof.
- **Exfiltrating real data or maintaining access** → harm and trust loss → synthetic data only, no persistence.
- **Treating scanner output as verified findings** → false positives → manually validate reachability and impact.
- **Ignoring stop conditions** → uncontrolled impact → define and rehearse escalation before starting.

## Quality checklist
Written authorization and scope are recorded; active testing follows allowed techniques and rate limits; evidence is minimal, redacted, and reproducible; stop conditions and escalation contacts are defined.

## Anti-patterns
Credential spraying, social engineering, denial-of-service testing, installing persistence, accessing unrelated tenants, or publishing raw sensitive captures without explicit approval.

## Verification
Run only approved tests inside scope; preserve evidence; retest fixes safely; report untested areas and limitations with exact commands and observed results.

## Output format
Scope and authorization · methodology · findings with classification/confidence · evidence · impact · remediation · retest status · residual risk.

## Executable Verification & Failure Diagnostics
- **Verify**: Run only approved tests inside scope; preserve evidence; retest fixes safely; report untested areas and limitations with exact commands and observed results.
- **Anti-Patterns**: Credential spraying, social engineering, denial-of-service testing, installing persistence, accessing unrelated tenants, or publishing raw sensitive captures without explicit approval.
- **Failure Diagnostics**: A failing or ambiguous Verify result -> the first failing assertion or error line is the root cause, not the completion summary -> rerun the narrowest check named in Verify and inspect its first failing assertion.
