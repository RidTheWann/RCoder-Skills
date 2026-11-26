---
description: Build a passive, evidence-led threat model for a system, feature, or change
argument-hint: [system, feature, or diff to model]
---
Threat-model this target: $ARGUMENTS

1. Load the `security` specialist as the framing owner and keep it alongside `threat-modeling`. Confirm authorization and scope first; if either is unclear, stay passive: source and configuration review plus local fixtures only, with no scanning, exploitation, credential testing, or external probing.
2. Map the assets, actors, trust boundaries, entry points, and data flows from the code and configuration you can read. Mark anything inferred rather than observed.
3. For each trust boundary, enumerate threats (spoofing, tampering, repudiation, information disclosure, denial of service, elevation of privilege) and the existing control that addresses each one, citing the file that implements it.
4. Rank the gaps by impact and likelihood, and propose the smallest control that closes each. Do not write exploit code.
5. Report assumptions, unreviewed areas, and what would need an authorized active test. Label claims VERIFIED, INFERRED, or NOT VERIFIED.
