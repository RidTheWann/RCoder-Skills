# Secure code review

## Activate when
Security-focused pull-request review, vulnerability assessment, or inspection of input/authentication/data handling.

## Mental model
Review attacker-controlled data paths, authority transitions, resource use, and failure behavior. Prioritize exploitable impact over style.

## Procedure
1. Establish authorized scope, changed files, entry points, trust boundaries, and security assumptions.
2. Trace sources to sinks: input, files, environment, network, database, shell, templates, deserialization, and logs.
3. Check authn/authz, object/function access, tenant isolation, validation, encoding, injection, path traversal, SSRF, unsafe deserialization, races, and resource exhaustion.
4. Inspect secrets, cryptography, dependencies, error leakage, audit events, and secure defaults.
5. Validate findings with minimal non-destructive tests or code-path evidence; do not claim exploitability without proof.
6. Rank by impact, reachability, privilege, preconditions, and confidence; provide specific remediation and regression tests.

## Quality checklist
- [ ] Findings name location, source, sink, preconditions, impact, and confidence.
- [ ] Speculation is separated from confirmed issues.
- [ ] Fixes address root cause with regression tests.
- [ ] Review does not perform destructive validation.

## Anti-patterns
- Reporting speculative scanner output as confirmed.
- Including weaponized payloads without necessity.
- Focusing on style while missing access-control failures.

## Verification
Use static analysis, focused tests, dependency scans, and manual path tracing; confirm fixes with negative tests.

## Output format
List prioritized findings with evidence, impact, confidence, remediation, and verification.
