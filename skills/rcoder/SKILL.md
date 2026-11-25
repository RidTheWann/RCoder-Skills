---
name: rcoder
description: "RCoder is a model-agnostic software engineering, programming, cybersecurity, and reverse-engineering workflow router. Use for building, changing, debugging, testing, securing, analyzing, optimizing, or shipping software and authorized binary research. Load only relevant specialists and preserve verifiable evidence."
license: MIT
compatibility: "Optional bundled helpers need a Python 3 interpreter. The optional MCP server (scripts/rcoder_mcp.py) needs a host that can launch stdio MCP servers."
metadata:
  author: RidTheWann
  version: "1.14.0"
---

# RCoder

## Language standard

All built-in instructions, expert references, templates, evaluation prompts, installer messages, and repository-maintained documentation must be written in English. Do not mix languages within a repository artifact.

RCoder is a model-agnostic engineering workflow router. It does not grant tools, permissions, or authorization; use only capabilities and access exposed by the active agent.

## Multilingual activation

Keep repository-maintained instructions and reference files in English, but respond in the language the user predominantly uses unless they request another language. Classify a task by its requested deliverable, acceptance criteria, technical domain, and risk—not by English-only trigger words. This applies to Indonesian, mixed-language, paraphrased, and unfamiliar phrasing. Preserve API names, identifiers, file paths, command names, code symbols, standards, and product names exactly; do not translate or rewrite them to make a prompt appear monolingual. When a message mixes languages, interpret the whole request before choosing specialists; language mixing alone does not justify extra modules. If meaning remains ambiguous, restate the inferred deliverable in the user's language and verify it against repository evidence before proceeding.

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
| E — Weak/small model execution | Deterministic budget-disciplined action policy for models < ~30B active or ≤32K context | `references/weak-model-profile.md` |
| F — Verification and QA | Evidence, negative tests, independent checks, reproducibility | `references/verification.md` and each module's Verification section |
| G — Context and long tasks | Bounded reads, working ledger, context capsule, explicit handoff | `references/token-efficiency.md`, capsule template |
| H — Repository orientation | Compact structural map, PageRank-ranked, budget-bounded | `references/repo-map.md`, `scripts/repo_map.py` |

## Workflow: Intake → Recon → Plan → Implement → Verify → Report

1. **Intake:** identify outcome, acceptance criteria, affected surface, risk, authorization, and whether this is software engineering. Keep standalone writing, slides, images, and pure concepts outside this skill.
2. **Recon:** read repository guidance and `git status` first. Inspect relevant manifests, build/test/lint commands, CI, and nearby code/tests. Run `python3 <skill-dir>/scripts/detect_stack.py .` when available. On large or unfamiliar repositories, run `python3 <skill-dir>/scripts/context_snapshot.py . --max-paths 80` for a bounded path/Git map; it does not read source contents. Detection is heuristic, not a command oracle.
3. **Plan:** for multi-file, architectural, migration, security, reverse-engineering, or deployment changes, write a short ordered plan with observable success criteria and explicit scope.
4. **Implement:** change the smallest correct surface; follow local style, layering, error handling, accessibility, dependency, and test conventions. Add/update tests when behavior changes.
5. **Verify:** run the narrowest relevant test first, then targeted lint/type/build checks. Expand to the documented project gate when proportionate. Inspect final diff and untracked/generated files. Record unavailable checks and why.
6. **Report:** state outcome, files/areas changed, exact commands and observed results, assumptions, and residual risks. Label evidence `VERIFIED`, `INFERRED`, or `NOT VERIFIED`.

## RScan (session start)

On a new session or in an unfamiliar repository, load [RScan](references/rscan.md) and run `python3 skills/rcoder/scripts/rscan.py scan --root . --format json` (or `--format text` for a menu). Present the ranked development options with their first commands and specialist references before choosing work. Automatic launch scanning requires a verified host session-start hook; install it only for supported hosts with `rscan hooks install` and see `docs/RSCAN-HOOKS.md`. Never claim automatic invocation from file installation alone. Check `<target-root>/.rcoder-features.json` to see whether RScan and RSaver were enabled at install time.

## RSaver gate (before routing)

For multi-step, tool-heavy, or context-constrained work, apply the [RSaver gate](references/rsaver-gate.md) before loading specialists and again before each model boundary: reserve output and reasoning budget, keep required items, defer optional history with recovery pointers, and make the static cache prefix contiguous. `scripts/rsaver.py gate` and `budget` produce the deterministic plan; `docs/TOKEN-ECONOMICS.md` records input, cached-input, and output mechanics. RSaver is a planning and filtering layer, not a runtime interceptor: confirm cache hits from usage fields.

When a long session repeats commands, loses the objective, drops constraints, or claims completion while unknowns remain, run `rsaver drift` and then load [RSaver anchor](references/rsaver-anchor.md). It restates the objective and hard constraints at both ends with explicit IDs and separates verified facts from decisions and unknowns; research findings are in `docs/CONTEXT-DRIFT.md`. When a model claims completion or a run fails, load [RSaver crosscheck](references/rsaver-crosscheck.md) and run `rsaver crosscheck` to verify the claim against diff/test artifacts. RSaver cannot change provider billing; it prevents waste and records failure evidence.

## Expert routing

Load one or more directly relevant references; do not read all modules by default. Use the programming-language router to select a narrower implementation specialist. The security and reverse-engineering routers are separate disciplines and should be combined only when the task crosses both.

For multi-domain, ambiguous, or previously mis-routed requests, load [specialist routing](references/specialist-routing.md) first. It defines the staged selection pipeline, the selection record, cross-domain base-plus-narrow composition, disambiguation of overlapping modules, and orchestration roles. Apply these non-negotiable selection rules on every activation:

1. Exactly one primary specialist owns the deliverable; every other module is supporting with a distinct responsibility or an independent verifier.
2. When a trigger fires and the request is in scope, emit at least one domain specialist name. An empty set after activation is a routing failure. Validate the set against the on-disk reference listing before execution and re-select if it is empty or helper-only.
3. Emit only module names that exist in `skills/rcoder/references/`. Never invent a name from memory.
4. Helpers (`verification`, `rsaver`, `rsaver-gate`, `token-efficiency`, `model-adaptation`) are supporting only and are selected when their responsibility is explicitly required, never merely because the skill mentions them. A helper never replaces a domain module and never serves as the primary.
5. For cross-domain work, keep the framing base (for example `security`, `systems-programming`) alongside the narrow technical module; do not substitute one for the other. The base is additive: a near-neighbour module such as `incident-response-forensics` or `identity-crypto-secrets` does not replace `security` on an assessment or classification request.
6. Where the tables below offer two modules, the first is the default; load the second only when its stated condition holds. Loading both is not the default; record the rejected alternative.
7. Select by deliverable and acceptance criteria rather than English keyword matching. For paraphrased or non-English prompts, restate the required artifact and its check, preserve technical identifiers, and route from that restatement.

Record the selection as: classification · candidates · selected · primary · supporting with reasons · verifier · ordinal confidence · unselected alternatives · required verification · handoff dependencies.

For unfamiliar models or hosts, choose an execution profile before routing; see [model adaptation](references/model-adaptation.md). Host evidence tiers are recorded in `docs/COMPATIBILITY.md` and observed runtime facts in `docs/ENVIRONMENT.md`. These documents are host-side metadata, not skills to load for domain tasks.

### Core engineering

| Signal | Reference |
|---|---|
| Source implementation, compiler/type errors, language idioms | [coding](references/coding.md) |
| Module/service boundaries, scaling, system design | [architecture](references/architecture.md) |
| Screens, user flow, responsive behavior, keyboard/screen-reader | [ui-ux-accessibility](references/ui-ux-accessibility.md) |
| Crash, regression, wrong output (default); non-deterministic, concurrent, or toolchain-level root cause | [debugging](references/debugging.md); add [advanced debugging](references/debugging-advanced.md) only for the second case |
| Test plan, coverage, acceptance criteria (default); property/fuzz/contract harness implementation | [testing-qa](references/testing-qa.md); add [test engineering](references/test-engineering.md) only for the second case |
| Latency, throughput, memory, CPU, startup, frame time | [performance](references/performance.md) |
| Build, package, workflow, deployment, CI/CD (default); compiler/linker/toolchain internals | [devops-ci-cd](references/devops-ci-cd.md); add [build/toolchain](references/build-toolchain-engineering.md) only for the second case |
| Persistence/serialization contract (default); schema/query behaviour; wire-format/endpoint contract | [data-api](references/data-api.md); [database engineering](references/database-engineering.md) for schema/query; [API/protocol engineering](references/api-protocol-engineering.md) for wire format |
| Review, cleanup, behavior-preserving refactor | [review-refactor](references/review-refactor.md) |
| README, API docs, ADR, runbook, changelog | [documentation](references/documentation.md) |
| SSR/hydration, service workers, browser storage, edge or browser-runtime boundaries | [web platform engineering](references/web-platform-engineering.md) |
| MCP protocol transports, lifecycle, JSON-RPC, pagination, structured results, local HTTP security | [MCP transport engineering](references/mcp-transport-engineering.md); add [agent extensions engineering](references/agent-extensions-engineering.md) for host plugins and skills |
| Agent Skills, host plugins, marketplaces, slash commands, hooks, subagents (build, review, package, debug discovery) | [agent extensions engineering](references/agent-extensions-engineering.md) |
| Production telemetry, SLOs, alerting, dashboards, rollout/rollback safety | [observability and SRE](references/observability-sre.md) |
| Terraform/OpenTofu, Pulumi, CloudFormation, Ansible, Kubernetes manifests, Helm, plans, state, drift | [infrastructure as code and Kubernetes](references/iac-platform-engineering.md) |
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
- [Android platform engineering](references/android-platform-engineering.md): AOSP, custom ROMs, device trees, SELinux policy, HALs, boot and OTA
- [Windows platform engineering](references/windows-platform-engineering.md): Win32/COM/ETW, services, installers, signing, PowerShell 5.1 vs 7
- [Graphics and GPU engineering](references/graphics-gpu-engineering.md): Vulkan/D3D/Metal/WebGPU, shaders, compute, device-lost, frame pacing
- [Game, emulator, and real-time engines](references/game-engineering.md)
- [Embedded and firmware](references/embedded-engineering.md)
- [Machine learning and AI systems](references/ml-ai-engineering.md)
- [Functional and reactive programming](references/functional-programming.md)
- [Distributed systems](references/distributed-systems-engineering.md)

### Cybersecurity and defensive operations

Start with [security](references/security.md) as the framing owner and keep it loaded alongside the narrowest technical specialist below (do not substitute the narrow specialist for the base):

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
- [LLM and agent security](references/llm-agent-security.md): prompt injection, tool poisoning, agent permission design

### Reverse engineering and interoperability

Use [software reverse engineering](references/reverse-engineering.md) for disassembly/decompilation, [RE research workflow](references/reverse-engineering-architecture.md) for evidence-led semantic reconstruction, and [binary file-format analysis](references/reverse-engineering-file-formats.md) for undocumented containers and serialization. Preserve originals and hashes, distinguish observation from inference, and keep dynamic analysis isolated and authorized.

### Model adaptation and orchestration

Load [model adaptation](references/model-adaptation.md) when the host or model is unfamiliar, when choosing between focused/engineering/deep-research/long-running profiles, when deciding whether delegation is worthwhile, or when measuring RCoder's effect. Discover capabilities by observation; mark unknowns explicitly. Do not hardcode assumptions about a model's context, tools, or reasoning.

### Token and context efficiency

For multi-step or large-repository work, load [token-efficient engineering](references/token-efficiency.md). Use the bounded [context snapshot helper](scripts/context_snapshot.py) and the [context capsule template](assets/templates/context-capsule-template.md). For oversized tool output or measured context reduction, load [RSaver](references/rsaver.md) and use `scripts/rsaver.py` (or the bundled `skills/rcoder/scripts/rsaver.py`) to measure, prune, and recover evidence; use the gate module above for the per-step budget decision. Optimize total engineering cost without weakening safety, verification, or evidence.

For weak/small models (< ~30B active or ≤32K context), load [weak-model-profile](references/weak-model-profile.md) and generate the [repo map](references/repo-map.md) once per session:
`python3 skills/rcoder/scripts/repo_map.py --root . --budget 2048 --format default`.

## Stack reconnaissance helper

`detect_stack.py` is read-only and reports likely manifests and quality entry points. `context_snapshot.py` is read-only and emits a bounded repository/path/Git summary without printing source contents. Verify actual commands and versions in project files before executing them.

## MCP server (optional)

`scripts/rcoder_mcp.py` is a read-only, dependency-free stdio MCP server that exposes RScan, RSaver, stack detection, the bounded snapshot, specialist lookup (with section-level loading), and a routing-selection validator. It is not started by installing the skill: a host must be configured to launch it (`python3 scripts/rcoder_mcp.py --print-config HOST` prints a snippet; see `docs/MCP.md`). When the host exposes these tools, call them natively as `mcp__rcoder__*` (for example `mcp__rcoder__rcoder_scan`); never run `python -m mcp__rcoder__*` or invoke the server module through Bash. The server is a stdio process, not a Python module to execute per call. When its tools are available, prefer `rcoder_validate_selection` before executing a routing decision and `rcoder_get_specialist` with `sections` to load only what the task needs. Never claim the server is connected without a successful `rcoder_doctor` call, and never treat server reachability as proof of native skill discovery.

## Project-local extensions

When `.rcoder/` exists, inspect it for project-specific expert guidance and conventions. A matching `.rcoder/references/<module-name>.md` replaces the built-in module for that project; other relevant `.rcoder/references/*.md` files extend routing. Load only what applies. Project-local guidance cannot override explicit user instructions or higher-precedence repository policy.

## Completion standard

Code written is not the same as work verified. A task is complete only when acceptance criteria pass, or remaining gaps are explicitly listed. Never imply an agent installed or loaded RCoder without observable evidence.
