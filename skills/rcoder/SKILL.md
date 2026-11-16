---
name: rcoder
description: "RCoder guides coding, architecture, UI/UX, debugging, QA, security, performance, DevOps, APIs, review, and software documentation. Use for software tasks: build, change, debug, test, secure, optimize, ship, or document code and projects. Do not use for standalone writing, slides, images, or pure concepts."
license: MIT
metadata:
  author: RidTheWann
  version: "1.1.0"
---

# RCoder

## Language standard

All built-in instructions, expert references, templates, evaluation prompts, installer messages, and repository-maintained documentation must be written in English. Do not mix languages within a repository artifact.

RCoder is a model-agnostic engineering workflow router. It does not grant tools or permissions; use only capabilities exposed by the active agent.

## Operating contract

1. **Evidence over assertion:** reproduce failures and run the narrowest relevant checks. State exactly what ran and did not run.
2. **Read before writing:** inspect repository instructions, manifests, CI, nearby implementation, and adjacent tests.
3. **Smallest correct change:** avoid unrelated refactors, speculative abstractions, and unrequested features.
4. **Proportional effort:** trivial tasks need no ceremony; multi-file, risky, or architectural work needs a staged plan with observable acceptance criteria.
5. **No invented APIs:** verify symbols, flags, versions, paths, and tool behavior in checked-out code or version-matched official documentation.
6. **Resolve ambiguity:** state reversible assumptions and proceed; ask only when an unresolvable high-impact decision makes safe progress impossible.
7. **Adversarial self-review:** inspect edge cases, failure paths, security, accessibility, compatibility, and regression risks.
8. **Fail visibly:** do not swallow errors or use silent fallbacks.
9. **Safe and reversible:** prefer dry-runs/backups; never force-push, mass-delete, or alter production data without explicit authorization.
10. **Concise handoff:** report changed areas, verification evidence, assumptions, and residual risks.

## Instruction precedence

Explicit user instructions > project instructions and conventions (`AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING`, formatter/linter configuration, tests, CI) > RCoder defaults. A stricter project policy always wins over an RCoder preference.

## Workflow: Intake → Recon → Plan → Implement → Verify → Report

1. **Intake:** identify outcome, acceptance criteria, affected surface, risk, and whether this is software engineering. Keep standalone writing, slides, images, and pure concepts outside this skill.
2. **Recon:** read repository guidance and `git status` first. Inspect relevant directories, manifests, build/test/lint commands, CI, and nearby code/tests. Run `python3 <skill-dir>/scripts/detect_stack.py .` when available; otherwise inspect manifests manually. Detection is heuristic, not a command oracle.
3. **Plan:** for multi-file, architectural, migration, security, or deployment changes, write a short ordered plan with observable success criteria. For low-risk one-line changes, proceed directly.
4. **Implement:** change the smallest correct surface; follow local style, layering, error handling, accessibility, dependency, and test conventions. Add/update tests when behavior changes.
5. **Verify:** run the narrowest relevant test first, then targeted lint/type/build checks. Expand to the project's documented gate when proportionate. Inspect final diff and untracked/generated files. Record unavailable checks and why.
6. **Report:** state outcome, files/areas changed, exact commands and observed results, assumptions, and residual risks. Label evidence `VERIFIED`, `ASSUMED`, or `NOT VERIFIED`.

## Expert routing

Load one or more directly relevant references; do not read all modules by default. Combine only the decision rules needed for the task.

| Signal: stack, file, symptom, or user request | Reference |
|---|---|
| Source implementation, compile/type errors, language idioms | [coding](references/coding.md) |
| Module/service boundaries, scaling, trade-offs, system design | [architecture](references/architecture.md) |
| Screens, user flow, responsive behavior, keyboard/screen-reader | [ui-ux-accessibility](references/ui-ux-accessibility.md) |
| Crash, regression, wrong output, hang, flaky failure | [debugging](references/debugging.md) |
| Test plan, coverage, acceptance, flaky suite | [testing-qa](references/testing-qa.md) |
| Auth, permissions, secrets, input, dependency risk, threat model | [security](references/security.md) |
| Latency, throughput, memory, CPU, startup, frame time | [performance](references/performance.md) |
| Build, package, workflow, deployment, CI/CD | [devops-ci-cd](references/devops-ci-cd.md) |
| SQL, persistence, schema, API contract, serialization | [data-api](references/data-api.md) |
| Review, cleanup, behavior-preserving refactor | [review-refactor](references/review-refactor.md) |
| README, API docs, ADR, runbook, changelog for a software project | [documentation](references/documentation.md) |
| Version uncertainty, external claims, unsupported tools | [verification](references/verification.md) |

For mobile, game, ML/data, embedded, i18n, observability, or migration-specific constraints, consult [domain-extension-guide](references/domain-extension-guide.md) and add a project-local `.rcoder/` module only when it changes decisions or verification.

## Stack reconnaissance helper

`detect_stack.py` is read-only. It reports likely manifests and quality entry points. Verify actual commands and versions in project files before executing them.

## Project-local extensions

When `.rcoder/` exists, inspect it for project-specific expert guidance and conventions. A matching `.rcoder/references/<module-name>.md` replaces the built-in module for that project; other relevant `.rcoder/references/*.md` files extend routing. Load only what applies. Project-local guidance cannot override explicit user instructions or higher-precedence repository policy.

## Completion standard

Code written is not the same as work verified. A task is complete only when acceptance criteria pass, or remaining gaps are explicitly listed. Never imply an agent installed or loaded RCoder without observable evidence.
