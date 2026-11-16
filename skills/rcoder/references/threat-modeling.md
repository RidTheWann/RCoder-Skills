# Security architecture and threat modeling

## Activate when
A feature changes trust boundaries, identities, permissions, data flows, integrations, deployment, or security posture.

## Mental model
Security analysis starts with assets, actors, trust boundaries, attack surfaces, and impact. A checklist is not a threat model.

## Procedure
1. Define system boundary, assets, data classification, dependencies, security objectives, and deployment assumptions.
2. Map data flows and trust boundaries; identify entry points, identities, privileged operations, and sensitive stores.
3. Enumerate threats using STRIDE or a justified equivalent; include abuse cases, insiders, supply-chain compromise, and prompt/tool injection when AI agents are present.
4. Rate risk by exploitability and impact; separate evidence from assumptions and unknowns.
5. Map mitigations to controls, owners, tests, telemetry, and residual risk.
6. Revisit the model when architecture, permissions, dependencies, or data sensitivity changes.

## Quality checklist
- [ ] Assets and trust boundaries are explicit.
- [ ] Threats include misuse and privileged actors.
- [ ] High-risk threats map to testable controls.
- [ ] Residual risks and assumptions are recorded.

## Anti-patterns
- Calling a component trusted because it is internal.
- Treating authentication as authorization.
- Declaring security based only on scanner output.

## Verification
Review the model against implementation/deployment evidence and test high-risk controls with negative and abuse-case tests.

## Output format
Provide data-flow summary, threats, severity, mitigations, evidence, assumptions, and residual risk.
