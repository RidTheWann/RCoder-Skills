# Domain extension guide

## Activate when
A project has a domain-specific constraint not sufficiently covered by the core experts: mobile, games, ML/data, embedded, i18n, observability, or migrations.

## Mental model
A domain module is useful only when it changes a decision, implementation constraint, or verification method.

## Procedure
1. Identify the domain-specific platform, lifecycle, safety, certification, performance, and compatibility constraints.
2. Inspect official platform documentation and project-specific integration points.
3. Copy `assets/templates/expert-module-template.md` into the project's `.rcoder/references/`.
4. Add only concrete decisions, thresholds, failure modes, and verification steps; keep the module ≤300 lines.
5. Add a routing signal to the project instructions and an evaluation scenario for its distinctive risks.

## Guardrails
Do not create a module containing only generic advice. Do not let a project-local module override explicit user instructions or higher-priority repository policy. Keep credentials and project secrets out of expert modules.

## Verification
Use platform emulators/simulators or target hardware where available; record platform/version and unverified device behaviors.
