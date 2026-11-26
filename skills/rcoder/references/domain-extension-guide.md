# Domain extension guide

## Activate when
A project has a domain-specific constraint not sufficiently covered by core experts: mobile, games/emulation, ML/data, embedded, reverse engineering, cybersecurity, i18n, observability, or migrations. Do not create a new module when an existing one already covers the constraint.

## Mission and expertise
Decide whether a project-local domain module is justified and ensure it changes a real decision, constraint, safety boundary, or verification method. Own the guardrails that keep extensions focused, English-only, and subordinate to user and repository policy.

## Mental model
A domain module is useful only when it changes a decision, implementation constraint, safety boundary, or verification method. Keep domain-specific and generic engineering guidance distinct; duplication causes drift.

## Prerequisites and reconnaissance
1. Identify the domain platform, lifecycle, safety, certification, performance, legal, and compatibility constraints.
2. Inspect official platform/specification documentation and project-specific integration points.
3. Search existing built-in references for coverage before proposing a new module.
4. Check whether `.rcoder/references/` already contains project-local guidance.

## Procedure
1. Identify the domain platform, lifecycle, safety, certification, performance, legal, and compatibility constraints.
2. Inspect official platform/specification documentation and project-specific integration points.
3. Route to existing specialist references first: mobile, game-engineering, embedded-engineering, ml-ai-engineering, reverse-engineering, threat-modeling, or the relevant security module.
4. Copy `assets/templates/expert-module-template.md` into project `.rcoder/references/` only when no existing module covers the concrete constraints.
5. Add decisions, thresholds, failure modes, evidence requirements, and domain-specific verification; keep modules at or below 300 lines.
6. Add routing signals and evaluation cases for distinctive risks.

## Decision tree
- Existing module covers the constraint → extend routing signals or evaluation cases, not content duplication.
- Constraint is genuinely domain-specific → create a project-local module from the 13-section template.
- Guidance is generic advice → do not create a module.
- Domain involves security testing or reverse engineering → require authorization and evidence provenance in the module.
- Module would override user or repository policy → reject that content.
- Module needs volatile version claims → cite versioned sources and review on upgrade.

## Tool strategy
Use official versioned documentation, project manifests, and the validation script's required-heading checks. Keep modules within the existing line limit. Use evaluation fixtures to prove the module changes a decision.

## Advanced techniques
- **Decision-impact test:** for each proposed section, name the decision it changes; delete sections that change none.
- **Evidence requirements:** specify what observation or measurement a claim in the domain requires.
- **Routing signals:** add concrete trigger phrases and anti-triggers so the router does not over-activate.
- **Evaluation cases:** add one positive and one negative prompt per distinctive domain risk.

## Failure modes
- **Generic-only modules** → context bloat → require domain-specific decisions.
- **Override attempts** → policy breach → project-local guidance cannot override user/repository policy.
- **Secrets or proprietary samples in modules** → leakage → sanitize before committing.
- **Unbounded growth** → router overload → keep modules at or below 300 lines and load on demand.

## Quality checklist
Module changes a concrete decision; domain-specific constraints and verification are explicit; required headings and line limits are satisfied; routing and evaluation cases exist.

## Anti-patterns
Creating a module to inflate the library; duplicating existing guidance; ignoring authorization boundaries; mixing languages in a repository artifact.

## Verification
Use emulators/simulators, isolated labs, hardware, reference implementations, or scoped staging environments as appropriate; record versions and unverified behaviors. Run the structural validator after adding a module.

## Output format
Domain · decision impact · module path · routing/evaluation additions · verification evidence.

## Executable Verification & Failure Diagnostics
- **Verify**: Use emulators/simulators, isolated labs, hardware, reference implementations, or scoped staging environments as appropriate; record versions and unverified behaviors.
- **Anti-Patterns**: Creating a module to inflate the library; duplicating existing guidance
- **Failure Diagnostics**: A failing or ambiguous Verify result -> the first failing assertion or error line is the root cause, not the completion summary -> rerun the narrowest check named in Verify and inspect its first failing assertion.
