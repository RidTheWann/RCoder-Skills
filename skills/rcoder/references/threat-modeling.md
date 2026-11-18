# Security architecture and threat modeling

## Activate when
A feature changes trust boundaries, identities, permissions, data flows, integrations, deployment, or security posture. Do not activate for a single local bug with no boundary change (use secure-code-review) or for an active assessment without a model (load this first).

## Mission and expertise
Produce a threat model that connects assets, actors, trust boundaries, and abuse cases to testable controls and residual risk. Own the system-level view of security; defer concrete code findings to secure-code-review and active validation to penetration-testing.

## Mental model
Security analysis starts with assets, actors, trust boundaries, attack surfaces, and impact. A checklist is not a threat model. A threat model is useful only when each high-risk threat maps to an owner, a control, a test, telemetry, and a stated residual risk.

## Prerequisites and reconnaissance
1. Define system boundary, assets, data classification, dependencies, security objectives, and deployment assumptions.
2. Gather architecture diagrams, deployment configuration, identity/permission matrices, and data-flow evidence from the repository.
3. Identify which components are attacker-reachable and which hold privileged authority.
4. Confirm whether AI agents or automated tools are in the system; include prompt/tool injection as a threat when present.

## Procedure
1. Define system boundary, assets, data classification, dependencies, security objectives, and deployment assumptions.
2. Map data flows and trust boundaries; identify entry points, identities, privileged operations, and sensitive stores.
3. Enumerate threats using STRIDE or a justified equivalent; include abuse cases, insiders, supply-chain compromise, and prompt/tool injection when AI agents are present.
4. Rate risk by exploitability and impact; separate evidence from assumptions and unknowns.
5. Map mitigations to controls, owners, tests, telemetry, and residual risk.
6. Revisit the model when architecture, permissions, dependencies, or data sensitivity changes.

## Decision tree
- New external entry point → add it to the data-flow map and enumerate threats crossing that boundary.
- Component is "internal" but attacker-influenced data reaches it → treat the boundary as crossed.
- Threat impact is high but exploitability is unknown → record as Unverified Hypothesis and define a safe validation experiment.
- Control exists only in the client → treat as absent; require server-side enforcement.
- Two components share a privilege domain → evaluate insider and confused-deputy abuse cases.
- Model is too large → decompose by trust boundary, not by feature list.
- System uses generated/AI components → add data poisoning, tool misuse, and output-handling threats.

## Tool strategy
Use data-flow diagrams, dependency graphs, IAM/permission configuration, deployment manifests, and existing ADRs as evidence. Use STRIDE, attack trees, or kill chains as structured elicitation aids. No active tooling is required for a threat model; if dynamic validation is needed, hand off to authorized testing. Verify that stated controls exist in code/config rather than documentation.

## Advanced techniques
- **Trust-boundary inventory:** list every point where data crosses ownership or privilege, including build/deploy pipelines.
- **Abuse cases:** describe legitimate features used maliciously (export, search, sharing, automation).
- **Control testing intent:** write the negative test the control must pass before implementation begins.
- **Telemetry mapping:** for each high-risk threat, define what observation would detect exploitation.
- **Risk scoring with evidence:** rate exploitability and impact separately, and attach the evidence or assumption behind each rating.
- **Model maintenance:** trigger a review on permission, dependency, or data-sensitivity changes.

## Failure modes
- **Calling a component trusted because it is internal** → missed boundary → trace actual data origin.
- **Treating authentication as authorization** → privilege escalation → model both separately.
- **Declaring security based only on scanner output** → false assurance → require control evidence and tests.
- **Checklist without flows** → shallow model → start from assets and data flows.
- **Stale model** → controls drift → attach review triggers to architecture changes.

## Quality checklist
Assets and trust boundaries are explicit; threats include misuse and privileged actors; high-risk threats map to testable controls; residual risks and assumptions are recorded; telemetry and owners are named.

## Anti-patterns
Trusting network location as a control; rating risk without evidence; omitting supply-chain and insider threats; writing a model that no implementation artifact can satisfy.

## Verification
Review the model against implementation and deployment evidence. Test high-risk controls with negative and abuse-case tests. Mark each control as VERIFIED, INFERRED, or NOT VERIFIED against observed evidence.

## Output format
Data-flow summary · threats · severity with evidence · mitigations and owners · tests/telemetry · assumptions · residual risk.
