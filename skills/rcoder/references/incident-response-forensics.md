# Defensive incident response and digital forensics

## Activate when
Suspected compromise, security incidents, malware events, evidence preservation, containment, triage, or post-incident review. Do not activate for proactive hardening (use security) or for malware classification without an active incident (use malware-analysis).

## Mission and expertise
Preserve evidence and safety first, maintain a defensible timeline and chain of custody, and distinguish observation from inference and hypothesis. Own containment authorization, recovery validation, and honest uncertainty.

## Mental model
Preserve evidence and safety first. Maintain a timeline and chain of custody; distinguish observation, inference, and hypothesis. Actions taken during an incident can destroy evidence or worsen impact, so each action needs authority and a rationale.

## Prerequisites and reconnaissance
1. Confirm authority, scope, incident owner, safety constraints, and evidence-handling requirements.
2. Record timezone, collector identity, acquisition method, and available preservation tooling before touching systems.
3. Identify stop conditions and escalation contacts, including legal and compliance where relevant.
4. Determine which systems are in scope and which contain sensitive or regulated data.

## Procedure
1. Confirm authority, scope, incident owner, safety constraints, and evidence-handling requirements.
2. Record timestamps/timezone, source system, collector, acquisition method, hashes, and chain-of-custody transfers.
3. Preserve volatile evidence when authorized; avoid rebooting, wiping, or modifying suspected systems before triage.
4. Contain using the least disruptive approved action and coordinate with owners/legal/compliance as needed.
5. Analyze logs and artifacts from read-only copies; document observations and uncertainty.
6. Eradicate root cause, rotate exposed credentials, restore trusted sources, validate monitoring, and record lessons.

## Decision tree
- Volatile evidence at risk → preserve it within authority before any containment action that would lose it.
- Containment could disrupt service → obtain explicit approval and choose the least disruptive option.
- Evidence integrity uncertain → stop, re-acquire from a read-only copy, and record the discrepancy.
- Hypothesis not supported → mark it unresolved and gather more evidence; do not present it as fact.
- Active malware suspected → load malware-analysis and keep samples out of production hosts.
- Credentials exposed → rotate them after preserving evidence of exposure.
- Recovery complete → validate monitoring and re-examine the system for persistence before declaring closure.

## Tool strategy
Use read-only acquisition, hashing, timeline tools, log analysis, and isolated lab environments. Verify tool versions and record commands. Work on copies, never originals. Avoid uploading evidence to external services.

## Advanced techniques
- **Chain of custody:** record every transfer with collector, time, and hash verification.
- **Timeline correlation:** normalize timestamps across hosts and record clock skew before asserting order.
- **Evidence tiers:** label findings as observation, inference, or hypothesis with confidence.
- **Least-disruptive containment:** prefer isolation of a single identity or segment over broad shutdowns.
- **Recovery validation:** verify the root cause is gone, credentials rotated, and detection covers recurrence.

## Failure modes
- **Executing untrusted samples on production hosts** → reinfection → use isolated labs.
- **Wiping evidence before acquisition** → unrecoverable loss → preserve first.
- **Publishing personal or sensitive indicators unnecessarily** → privacy harm → sanitize reports.
- **Treating a hypothesis as fact** → wrong remediation → label confidence.
- **Declaring recovery without monitoring validation** → recurrence → verify detection.

## Quality checklist
Actions are authorized and timestamped; evidence integrity and custody are preserved; hypotheses are not presented as facts; containment and recovery have rollback/validation.

## Anti-patterns
Rebooting a compromised host "to see if it helps"; sharing raw captures containing personal data; skipping legal coordination; closing an incident without a post-incident review.

## Verification
Hash acquired evidence, preserve logs, validate containment, run recovery checks, and seek independent review. Record exact commands and mark untested paths NOT VERIFIED.

## Output format
Timeline · evidence inventory · confirmed observations · confidence · actions · impact · recovery · unknowns.

## Executable Verification & Failure Diagnostics
- **Verify**: Hash acquired evidence, preserve logs, validate containment, run recovery checks, and seek independent review.
- **Anti-Patterns**: Rebooting a compromised host "to see if it helps"; sharing raw captures containing personal data
- **Failure Diagnostics**: A failing or ambiguous Verify result -> the first failing assertion or error line is the root cause, not the completion summary -> rerun the narrowest check named in Verify and inspect its first failing assertion.
