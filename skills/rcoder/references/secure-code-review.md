# Secure code review

## Activate when
Security-focused pull-request review, vulnerability assessment, or inspection of input/authentication/data handling. Do not activate for general style review (use review-refactor) or for active testing without written scope (use penetration-testing).

## Mission and expertise
Review attacker-controlled data paths, authority transitions, resource use, and failure behavior. Prioritize exploitable impact over style. Own source-level finding quality: location, source, sink, preconditions, impact, confidence, and remediation.

## Mental model
Review attacker-controlled data paths, authority transitions, resource use, and failure behavior. Prioritize exploitable impact over style. A finding is a claim that must survive scrutiny: show the path, the violated invariant, and the smallest safe evidence.

## Prerequisites and reconnaissance
1. Establish authorized scope, changed files, entry points, trust boundaries, and security assumptions.
2. Identify the data sources an attacker can influence and the privileged sinks they can reach.
3. Confirm the runtime, framework version, and framework-provided defenses before assuming a control exists.
4. Decide the validation boundary: passive source analysis only, or local synthetic fixtures when permitted.

## Procedure
1. Establish authorized scope, changed files, entry points, trust boundaries, and security assumptions.
2. Trace sources to sinks: input, files, environment, network, database, shell, templates, deserialization, and logs.
3. Check authn/authz, object/function access, tenant isolation, validation, encoding, injection, path traversal, SSRF, unsafe deserialization, races, and resource exhaustion.
4. Inspect secrets, cryptography, dependencies, error leakage, audit events, and secure defaults.
5. Validate findings with minimal non-destructive tests or code-path evidence; do not claim exploitability without proof.
6. Rank by impact, reachability, privilege, preconditions, and confidence; provide specific remediation and regression tests.

## Decision tree
- Source-to-sink path with attacker control and no defense → Confirmed finding if safely validated, otherwise Potential with explicit unknowns.
- Control exists but is applied after use or on the wrong context → order/context bug, usually Confirmed.
- Authorization checked in UI or client only → Confirmed missing server-side enforcement.
- Scanner flag with no reachable path → investigate; likely False Positive if disproved.
- Crypto or secret handling involved → load cryptography-engineering or identity-crypto-secrets.
- Dependency or build-time issue → load supply-chain-security.
- Requires active probing outside scope → Unverified Hypothesis; request authorization.

## Tool strategy
Use repository search and manual path tracing as the primary method; static analysis and dependency scanning as coverage aids. Use local synthetic fixtures for non-destructive confirmation. Verify analyzer versions and rule sets; do not paste untrusted code or secrets into external services. Mark unavailable tooling explicitly.

## Advanced techniques
- **Source/sink tables:** enumerate each attacker-controlled source and every sink it reaches, with the defense at the boundary.
- **Authority transition review:** check every point where identity or tenant context changes, including async jobs and background tasks.
- **Canonicalization checks:** verify validation occurs after decoding, normalization, and path resolution.
- **Failure-path review:** examine error handling for information disclosure, fail-open behavior, and partial state.
- **Regression test design:** write the negative test that would have caught the finding before it shipped.
- **Confidence labeling:** use Confirmed, Potential, Informational, False Positive, or Unverified Hypothesis.

## Failure modes
- **Reporting speculative scanner output as confirmed** → false positives → trace the path and validate safely.
- **Including weaponized payloads without necessity** → harm and leakage → use minimal synthetic proof.
- **Focusing on style while missing access-control failures** → missed critical issues → review authority transitions first.
- **Ignoring framework defaults** → wrong assumptions → verify version-matched documentation.
- **Reviewing only changed lines** → missed context → trace callers and callees around the diff.

## Quality checklist
Findings name location, source, sink, preconditions, impact, and confidence; speculation is separated from confirmed issues; fixes address root cause with regression tests; review does not perform destructive validation.

## Anti-patterns
Treating a clean scan as a clean review; assuming internal helpers are safe; accepting client-side checks as authorization; disclosing real secrets or personal data in findings.

## Verification
Use static analysis, focused tests, dependency scans, and manual path tracing. Confirm fixes with negative tests on the original path. Record exact commands and results; mark untested areas NOT VERIFIED.

## Output format
Prioritized findings with classification and confidence · evidence · impact · remediation · regression tests · residual risk.

## Executable Verification & Failure Diagnostics
- **Verify**: Use static analysis, focused tests, dependency scans, and manual path tracing.
- **Anti-Patterns**: Treating a clean scan as a clean review; assuming internal helpers are safe
- **Failure Diagnostics**: A failing or ambiguous Verify result -> the first failing assertion or error line is the root cause, not the completion summary -> rerun the narrowest check named in Verify and inspect its first failing assertion.
