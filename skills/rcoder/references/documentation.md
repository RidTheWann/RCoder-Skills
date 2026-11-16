# Software documentation expert module

## Activate when
README, API docs, ADRs, runbooks, changelogs, or developer onboarding for an actual software project.

## Mental model
Documentation is an interface to the software. Commands, paths, flags, versions, and capability claims must match implementation or an authoritative source.

## Procedure
1. Identify reader and job: install, configure, develop, operate, troubleshoot, integrate, or upgrade.
2. Inspect source, scripts, manifests, CI, release artifacts, and current CLI help before writing.
3. Date/version volatile details and cite official sources.
4. Give complete task steps: prerequisites, exact command, expected result, and recovery.
5. Keep README, CLI help, examples, manifests, and changelog terminology aligned.
6. Label supported/experimental/deprecated/unverified behavior.
7. Verify commands and links when possible; never claim unrun commands were tested.

## Quality checklist
Audience/task clear; prerequisites/platform explicit; commands exact; version claims sourced; recovery included; docs match release.

## Anti-patterns
“Install dependencies” without details; outdated commands from memory; claiming support without evidence; duplicating long reference text.

## Verification
Run commands in disposable environments, validate links, and compare flags and examples to implementation.

## Output format
Audience and task · changed docs · command/link checks · version/source notes · remaining uncertainty.
