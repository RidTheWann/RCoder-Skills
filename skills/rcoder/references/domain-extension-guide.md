# Domain extension guide

## Activate when
A project has a domain-specific constraint not sufficiently covered by core experts: mobile, games/emulation, ML/data, embedded, reverse engineering, cybersecurity, i18n, observability, or migrations.

## Mental model
A domain module is useful only when it changes a decision, implementation constraint, safety boundary, or verification method. Keep domain-specific and generic engineering guidance distinct.

## Procedure
1. Identify the domain platform, lifecycle, safety, certification, performance, legal, and compatibility constraints.
2. Inspect official platform/specification documentation and project-specific integration points.
3. Route to existing specialist references first: mobile, game-engineering, embedded-engineering, ml-ai-engineering, reverse-engineering, threat-modeling, or the relevant security module.
4. Copy `assets/templates/expert-module-template.md` into project `.rcoder/references/` only when no existing module covers the concrete constraints.
5. Add decisions, thresholds, failure modes, evidence requirements, and domain-specific verification; keep modules at or below 300 lines.
6. Add routing signals and evaluation cases for distinctive risks.

## Guardrails
Do not create a module containing only generic advice. Do not let project-local guidance override user instructions or higher-priority repository policy. Keep credentials and proprietary samples out of modules. Reverse engineering and security testing require legal authorization and evidence provenance.

## Verification
Use emulators/simulators, isolated labs, hardware, reference implementations, or scoped staging environments as appropriate; record versions and unverified behaviors.
