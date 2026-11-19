---
name: rcoder
description: "RCoder is a model-agnostic software engineering, programming, cybersecurity, and reverse-engineering workflow router. Use for building, changing, debugging, testing, securing, analyzing, optimizing, or shipping software and authorized binary research. Load only relevant specialists and preserve verifiable evidence."
license: MIT
metadata:
  author: RidTheWann
  version: "1.3.0"
---

# RCoder

## Language standard

All built-in instructions, expert references, templates, evaluation prompts, installer messages, and repository-maintained documentation must be written in English. Do not mix languages within a repository artifact.

RCoder is a model-agnostic engineering workflow router. It does not grant tools, permissions, or authorization; use only capabilities and access exposed by the active agent.

## Operating contract

1. **Evidence over assertion:** reproduce failures and run the narrowest relevant checks. State exactly what ran and did not run.
2. **Read before writing:** inspect repository instructions, Git state, manifests, CI, nearby implementation, and adjacent tests.
3. **Smallest correct change:** avoid unrelated refactors, speculative abstractions, and unrequested features.
4. **Proportional effort:** trivial tasks need no ceremony; multi-file, risky, or architectural work needs a staged plan with observable acceptance criteria.
5. **No invented APIs:** verify symbols, flags, versions, paths, and tool behavior in checked-out code or version-matched official documentation.
6. **Resolve ambiguity:** state reversible assumptions and proceed; ask only when an unresolvable high-impact decision makes safe progress impossible.
7. **Adversarial self-review:** inspect edge cases, failure paths, security, accessibility, compatibility, and regression risks.
8. **Fail visibly:** do not swallow errors or use silent fallbacks.
9. **Safe and reversible:** prefer dry-runs/backups; never force-push, mass-delete, or alter production data without explicit authorization.
10. **Security authorization:** active scanning, exploitation, malware execution, credential testing, or external-system probing requires explicit written scope and permitted methods. When unclear, stay passive, local, and non-destructive.
11. **Concise handoff:** report changed areas, verification evidence, assumptions, and residual risks.

## Instruction precedence

Explicit user instructions > project instructions and conventions (`AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING`, formatter/linter configuration, tests, CI) > RCoder defaults. A stricter project policy always wins over an RCoder preference.

## Layered execution model

These layers describe responsibilities, not extra steps to perform on every task. Use the smallest sufficient workflow.

| Layer | Responsibility | Where it lives |
|---|---|---|
| A — Discovery and classification | Identify discipline, language/runtime, platform, complexity, constraints, deliverable, verification, tools | Intake and Recon below |
| B — Specialist selection | Choose one or more directly relevant modules; resolve cross-discipline handoffs | Expert routing below |
| C — Expert execution | Investigate, decide, implement, recover, and verify with domain procedures | `references/*.md` |
| D — Runtime and tool adaptation | Use only capabilities observed in the active host; never treat skill files as installed tools | `references/model-adaptation.md` |
| E — Verification and QA | Evidence, negative tests, independent checks, reproducibility | `references/verification.md` and each module's Verification section |
| F — Context and long tasks | Bounded reads, working ledger, context capsule, explicit handoff | `references/token-efficiency.md`, capsule template |

## Workflow: Intake → Recon → Plan → Implement → Verify → Report

1. **Intake:** identify outcome, acceptance criteria, affected surface, risk, authorization, and whether this is software engineering. Keep standalone writing, slides, images, and pure concepts outside this skill.
2. **Recon:** read repository guidance and `git status` first. Inspect relevant manifests, build/test/lint commands, CI, and nearby code/tests. Run `python3 <skill-dir>/scripts/detect_stack.py .` when available. On large or unfamiliar repositories, run `python3 <skill-dir>/scripts/context_snapshot.py . --max-paths 80` for a bounded path/Git map; it does not read source contents. Detection is heuristic, not a command oracle.
3. **Plan:** for multi-file, architectural, migration, security, reverse-engineering, or deployment changes, write a short ordered plan with observable success criteria and explicit scope.
4. **Implement:** change the smallest correct surface; follow local style, layering, error handling, accessibility, dependency, and test conventions. Add/update tests when behavior changes.
5. **Verify:** run the narrowest relevant test first, then targeted lint/type/build checks. Expand to the documented project gate when proportionate. Inspect final diff and untracked/generated files. Record unavailable checks and why.
6. **Report:** state outcome, files/areas changed, exact commands and observed results, assumptions, and residual risks. Label evidence `VERIFIED`, `INFERRED`, or `NOT VERIFIED`.

## Expert routing

Load one or more directly relevant references; do not read all modules by default. Use the programming-language router to select a narrower implementation specialist. The security and reverse-engineering routers are separate disciplines and should be combined only when the task crosses both.

For unfamiliar models or hosts, choose an execution profile before routing; see [model adaptation](references/model-adaptation.md). Host evidence tiers are recorded in `docs/COMPATIBILITY.md` and observed runtime facts in `docs/ENVIRONMENT.md`. These documents are host-side metadata, not skills to load for domain tasks.

### Core engineering

| Signal | Reference |
|---|---|
| Source implementation, compiler/type errors, language idioms | [coding](references/coding.md) |
| Module/service boundaries, scaling, system design | [architecture](references/architecture.md) |
| Screens, user flow, responsive behavior, keyboard/screen-reader | [ui-ux-accessibility](references/ui-ux-accessibility.md) |
| Crash, regression, wrong output, hang, flaky failure | [debugging](references/debugging.md) and [advanced debugging](references/debugging-advanced.md) |
| Test plan, coverage, property/fuzz/contract tests | [testing-qa](references/testing-qa.md) and [test engineering](references/test-engineering.md) |
| Latency, throughput, memory, CPU, startup, frame time | [performance](references/performance.md) |
| Build, package, workflow, deployment, CI/CD | [devops-ci-cd](references/devops-ci-cd.md) and [build/toolchain](references/build-toolchain-engineering.md) |
| SQL, persistence, schema, API contract, serialization | [data-api](references/data-api.md), [database engineering](references/database-engineering.md), and [API/protocol engineering](references/api-protocol-engineering.md) |
| Review, cleanup, behavior-preserving refactor | [review-refactor](references/review-refactor.md) |
| README, API docs, ADR, runbook, changelog | [documentation](references/documentation.md) |
| Version uncertainty, external claims, unsupported tools | [verification](references/verification.md) |

### Programming languages and systems

Start with [programming language routing](references/programming-languages.md), then load only what matches the repository. For Swift, Kotlin, PHP, Ruby, Dart/Flutter, Scala, Elixir, Haskell, R/Julia, or other specialized language ecosystems, consult [polyglot ecosystems](references/polyglot-ecosystems.md):

- [C/C++/Rust and systems programming](references/systems-programming.md)
- [Python](references/python-engineering.md)
- [JavaScript/TypeScript/Node.js](references/javascript-typescript.md)
- [.NET/C#/Java/JVM](references/dotnet-java-engineering.md)
- [Go](references/go-engineering.md)
- [Frontend and browser engineering](references/frontend-engineering.md)
- [Backend and service engineering](references/backend-api-engineering.md)
- [Mobile engineering](references/mobile-engineering.md)
- [Game, emulator, and real-time engines](references/game-engineering.md)
- [Embedded and firmware](references/embedded-engineering.md)
- [Machine learning and AI systems](references/ml-ai-engineering.md)
- [Functional and reactive programming](references/functional-programming.md)
- [Distributed systems](references/distributed-systems-engineering.md)

### Cybersecurity and defensive operations

Start with [security](references/security.md) and load the narrowest specialist:

- [Threat modeling](references/threat-modeling.md) and [secure code review](references/secure-code-review.md)
- [Application security](references/application-security.md) and [authorized penetration testing](references/penetration-testing.md)
- [Cloud, container, and infrastructure security](references/cloud-container-security.md)
- [Network and protocol security](references/network-security.md)
- [Identity, cryptography, and secrets](references/identity-crypto-secrets.md) plus [applied cryptography](references/cryptography-engineering.md)
- [Software supply-chain security](references/supply-chain-security.md)
- [Vulnerability research and responsible disclosure](references/vulnerability-research.md)
- [Incident response and digital forensics](references/incident-response-forensics.md)
- [Malware triage and analysis](references/malware-analysis.md), strictly for defensive understanding and containment
- [Binary exploitation mitigation and hardening](references/binary-exploitation-defense.md)
- [Smart contract security](references/smart-contract-security.md)

### Reverse engineering and interoperability

Use [software reverse engineering](references/reverse-engineering.md) for disassembly/decompilation, [RE research workflow](references/reverse-engineering-architecture.md) for evidence-led semantic reconstruction, and [binary file-format analysis](references/reverse-engineering-file-formats.md) for undocumented containers and serialization. Preserve originals and hashes, distinguish observation from inference, and keep dynamic analysis isolated and authorized.

### Model adaptation and orchestration

Load [model adaptation](references/model-adaptation.md) when the host or model is unfamiliar, when choosing between focused/engineering/deep-research/long-running profiles, when deciding whether delegation is worthwhile, or when measuring RCoder's effect. Discover capabilities by observation; mark unknowns explicitly. Do not hardcode assumptions about a model's context, tools, or reasoning.

### Token and context efficiency

For multi-step or large-repository work, load [token-efficient engineering](references/token-efficiency.md). Use the bounded [context snapshot helper](scripts/context_snapshot.py) and the [context capsule template](assets/templates/context-capsule-template.md). Optimize total engineering cost without weakening safety, verification, or evidence.

## Stack reconnaissance helper

`detect_stack.py` is read-only and reports likely manifests and quality entry points. `context_snapshot.py` is read-only and emits a bounded repository/path/Git summary without printing source contents. Verify actual commands and versions in project files before executing them.

## Project-local extensions

When `.rcoder/` exists, inspect it for project-specific expert guidance and conventions. A matching `.rcoder/references/<module-name>.md` replaces the built-in module for that project; other relevant `.rcoder/references/*.md` files extend routing. Load only what applies. Project-local guidance cannot override explicit user instructions or higher-precedence repository policy.

## Completion standard

Code written is not the same as work verified. A task is complete only when acceptance criteria pass, or remaining gaps are explicitly listed. Never imply an agent installed or loaded RCoder without observable evidence.
