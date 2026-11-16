# Defensive incident response and digital forensics

## Activate when
Suspected compromise, security incidents, malware events, evidence preservation, containment, triage, or post-incident review.

## Mental model
Preserve evidence and safety first. Maintain a timeline and chain of custody; distinguish observation, inference, and hypothesis.

## Procedure
1. Confirm authority, scope, incident owner, safety constraints, and evidence-handling requirements.
2. Record timestamps/timezone, source system, collector, acquisition method, hashes, and chain-of-custody transfers.
3. Preserve volatile evidence when authorized; avoid rebooting, wiping, or modifying suspected systems before triage.
4. Contain using the least disruptive approved action and coordinate with owners/legal/compliance as needed.
5. Analyze logs and artifacts from read-only copies; document observations and uncertainty.
6. Eradicate root cause, rotate exposed credentials, restore trusted sources, validate monitoring, and record lessons.

## Quality checklist
- [ ] Actions are authorized and timestamped.
- [ ] Evidence integrity and custody are preserved.
- [ ] Hypotheses are not presented as facts.
- [ ] Containment and recovery have rollback/validation.

## Anti-patterns
- Executing untrusted samples on production hosts.
- Wiping evidence before acquisition.
- Publishing personal or sensitive indicators unnecessarily.

## Verification
Hash acquired evidence, preserve logs, validate containment, run recovery checks, and seek independent review.

## Output format
Provide timeline, evidence inventory, confirmed observations, confidence, actions, impact, recovery, and unknowns.
