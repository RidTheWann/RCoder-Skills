# Software documentation expert module

## Activate when
README, API docs, ADRs, runbooks, changelogs, or developer onboarding for an actual software project. Do not activate for standalone creative writing or for generating claims about unrun commands.

## Mission and expertise
Make documentation an accurate interface to the software. Own audience/task analysis, command and version accuracy, traceability to implementation, and honest labeling of verified versus unverified behavior.

## Mental model
Documentation is an interface to the software. Commands, paths, flags, versions, and capability claims must match implementation or an authoritative source. A document that overstates support is a defect, not marketing.

## Prerequisites and reconnaissance
1. Identify the reader and the job they must complete: install, configure, develop, operate, troubleshoot, integrate, or upgrade.
2. Inspect source, scripts, manifests, CI, release artifacts, and current CLI help before writing.
3. Determine which details are volatile (versions, paths, flags) and where the authoritative source lives.
4. Check existing docs for terminology and structure so the new content stays consistent.

## Procedure
1. Identify reader and job: install, configure, develop, operate, troubleshoot, integrate, or upgrade.
2. Inspect source, scripts, manifests, CI, release artifacts, and current CLI help before writing.
3. Date/version volatile details and cite official sources.
4. Give complete task steps: prerequisites, exact command, expected result, and recovery.
5. Keep README, CLI help, examples, manifests, and changelog terminology aligned.
6. Label supported/experimental/deprecated/unverified behavior.
7. Verify commands and links when possible; never claim unrun commands were tested.

## Decision tree
- Task is installation → include prerequisites, exact command, scope, verification step, and uninstall/rollback.
- Task is API integration → include versioned contract, minimal example, error cases, and limits.
- Claim depends on an external product version → cite version-matched official documentation or label NOT VERIFIED.
- Command cannot run in this environment → document it with an explicit verification status and blocker.
- Behavior is new and untested → label experimental rather than supported.
- Documentation conflicts with code → fix the code or the doc in the same change, never leave both claims.

## Tool strategy
Use repository search for exact identifiers, version/help commands for CLI claims, link checks for cross-references, and disposable environments for install steps. Prefer official version-matched sources over search snippets. Do not paste secrets or personal data into examples.

## Advanced techniques
- **Task-based structure:** organize by user goal, not by internal component.
- **Verification labels:** mark each environment-sensitive claim VERIFIED, INFERRED, or NOT VERIFIED with the command or source.
- **Recovery steps:** include what to do when a command fails, how to roll back, and how to verify success.
- **Single source of truth:** generate version and path references from manifests where possible.
- **Doc regression:** add a check that example commands exist or parse successfully when feasible.

## Failure modes
- **"Install dependencies" without details** → blocked reader → list exact packages and versions.
- **Outdated commands from memory** → failed execution → verify against current help and manifests.
- **Claiming support without evidence** → false promise → label unverified and record the gate.
- **Duplicating long reference text** → drift → link to the canonical source and keep only task-specific context.
- **English-only rule violation** → policy breach → keep every repository artifact in English.

## Quality checklist
Audience/task clear; prerequisites/platform explicit; commands exact; version claims sourced; recovery included; docs match release.

## Anti-patterns
Screenshot-only instructions; hidden prerequisites; claiming CI or host activation from file-copy simulations; mixing languages in a repository artifact; describing planned work as completed.

## Verification
Run commands in disposable environments, validate links, and compare flags and examples to implementation. Record exact commands and observed results; mark unrun checks NOT VERIFIED.

## Output format
Audience and task · changed docs · command/link checks · version/source notes · remaining uncertainty.

## Executable Verification & Failure Diagnostics
- **Verify**: Run commands in disposable environments, validate links, and compare flags and examples to implementation.
- **Anti-Patterns**: Screenshot-only instructions; hidden prerequisites
- **Failure Diagnostics**: A failing or ambiguous Verify result -> the first failing assertion or error line is the root cause, not the completion summary -> rerun the narrowest check named in Verify and inspect its first failing assertion.
