# Specialist routing and orchestration

## Activate when
A request spans more than one discipline, the correct module set is ambiguous, a previous routing attempt produced an empty or bloated specialist list, a cross-language or cross-domain boundary is involved, or a task requires sequencing specialists with independent verification. Do NOT activate for a single-file fix whose single specialist is obvious from the core engineering table; use the narrowest module directly.

## Mission and expertise
This module owns the quality of specialist *selection* and *orchestration*, not domain implementation. Its authority ends once a primary, supporting, and verifier set with explicit responsibilities is chosen and handed off. It exists because the v1.11 pinned control run showed activation without correct selection: specialist F1 0.444, exact-match 0.167, and five cases where the skill was invoked yet the specialist list was empty. A later deterministic recomputation of the same frozen control found nine of 24 positive triggers with an empty set. The goal is the narrowest correct set: no missing required module, no unjustified module.

## Mental model
Two errors dominate routing and they pull in opposite directions. Under-selection drops a required module (for example a base `security` module alongside a narrow `smart-contract-security`, or `systems-programming` alongside `performance`); this dominates the control run's false negatives. Over-selection adds always-on helpers (`verification`, `rsaver`, `model-adaptation`) or substitutes a near-neighbour (`test-engineering` for `testing-qa`); this dominates control cases such as the nine-module token-budget selection. Micro-specialist F1 is `2*matched/(selected+relevant)`, so every extra module and every missing module lowers the same score. Exact-match requires the set to be exactly right, which is why ambiguous "X and Y" routing hints are harmful: a hint that lists two interchangeable modules makes exact-match unstable across otherwise identical requests. Composition rules, not keyword co-occurrence, decide the set.

## Prerequisites and reconnaissance
Before selecting modules, classify the request along: outcome and acceptance criteria; technical domain and sub-domains; language, runtime, and platform; complexity and blast radius; safety and authorization constraints; deliverable; and verification needs. Inspect repository signals (manifests, CI, nearby code) with bounded reads; do not infer stack from the prompt alone. Confirm which specialist names actually exist in `skills/rcoder/references/` and reject invented names. Treat the active model's self-report about its tools or context as UNKNOWN; only observed capabilities count.

## Procedure
1. **Request understanding.** Restate the outcome and acceptance criteria in one sentence. Separate explicit requirements from inferred ones.
2. **Domain classification.** Assign one primary domain (coding, security, reverse engineering, data, performance, etc.) and list secondary domains only when the task genuinely crosses a boundary.
3. **Language/runtime/platform identification.** From repository evidence, identify the primary language/runtime and any ABI, serialization, or deployment boundary. Load the matching language specialist, not a generic substitute. Interpret multilingual and mixed-language prompts as one semantic request: classify the deliverable, not the language switch; keep API names, identifiers, commands, file paths, and product names verbatim. Respond in the user's predominant language, but keep repository artifacts in English.
4. **Complexity and risk classification.** Label focused, engineering, deep-research, or long-running, and note whether the change is security-sensitive, destructive, or reversible.
5. **Candidate generation.** List every plausible specialist from the router plus cross-domain requirements. Do not filter yet.
6. **Selection and prioritization.** Apply the composition rules below. Choose one primary specialist that owns the deliverable. Add supporting specialists only where they own a distinct responsibility. Add a verifier only when the risk warrants an independent check.
   **Selection gate:** before any execution, write the selection record and check it. Reject and re-select when the fired trigger has an empty set, when every selected module is a helper, or when any name is absent from the on-disk reference listing. Do not hand off an invalid set. Treat this gate as a hard precondition, not a stylistic preference.
7. **Cross-specialist dependency resolution.** Order handoffs so prerequisites run first (recon before refactor, reproduction before fix, measurement before optimization, preservation before analysis).
8. **Execution-profile selection.** Choose the smallest sufficient profile from `model-adaptation.md`; justify any upgrade in one sentence.
9. **Tool discovery and capability matching.** For each required operation, verify the tool exists and its invocation, then choose a documented fallback if unavailable; record which tool was actually used.
10. **Execution and verification.** Execute with the primary owner driving, collect evidence from each specialist, resolve conflicts against the task's acceptance criteria, and run the final verification before handoff.

Composition rules (derived from control-run false negatives):
- A narrow defensive-security specialist implies its `security` base whenever the task requires a threat model, scope, authorization, or risk classification. Select both, with `security` as the framing owner and the narrow module as the technical owner. The base is additive: a near-neighbour such as `incident-response-forensics` or `identity-crypto-secrets` cannot replace `security` when the request asks for a security assessment, classification, or review.
- A systems-language task implies `systems-programming` alongside the task-facing module (`performance`, `test-engineering`, `verification`, or `debugging-advanced`) when the task depends on ABI, memory, or compiler behaviour. Keep the base when adding the narrow module; dropping it is a substitution error.
- A user-interface task with accessibility or responsive requirements adds `ui-ux-accessibility` to the platform specialist; it does not replace it.
- A cross-language or serialization-boundary task adds `polyglot-ecosystems` or `api-protocol-engineering` in addition to each language specialist.
- A reverse-engineering task that produces or consumes file formats adds `reverse-engineering-file-formats` in addition to the core `reverse-engineering` and evidence-led `reverse-engineering-architecture` modules.
- A long-running task that needs durable context across fresh model requests selects `context-fabric`; add `token-efficiency` only when measurement or reduction is part of the deliverable.
- An MCP wire-protocol or transport change selects `mcp-transport-engineering` as the protocol owner; add `agent-extensions-engineering` when a host plugin, Agent Skill, marketplace, or installer is also being changed. Add `security` plus the narrowest security module when the task changes authentication, authorization, or an externally reachable trust boundary.
- Helpers (`verification`, `rsaver`, `rsaver-gate`, `token-efficiency`, `model-adaptation`) are supporting modules, never primary. Add one only when its responsibility is explicitly required by the task; never activate it merely because the skill mentions it. A set made only of helpers is invalid for a domain task: re-select a domain owner. A helper does not substitute for a missing domain module, and a token-budget request does not imply loading every helper at once.
- Selection is driven by the deliverable and its acceptance criteria, not by keyword co-occurrence. Restate the required artifact and the check that will accept it, then choose the modules that own that artifact and that check. This keeps routing stable for paraphrased, mixed-language, and unfamiliar technical prompts.

Orchestration patterns:
- **Single:** one specialist owns the whole task; no handoff.
- **Primary/supporting:** one owner plus modules with disjoint responsibilities; the primary integrates.
- **Sequential handoff:** output of one module is the input of the next (reproduction → fix → regression test).
- **Parallel investigation:** independent evidence gathering with non-overlapping scopes; the coordinator merges results.
- **Independent verification:** the verifier did not produce the change and uses separate checks; a PASS from an implementation agent is not proof.
- **Conflict resolution:** when modules disagree, prefer the one whose evidence is reproducible and whose scope matches the acceptance criteria; record the rejected recommendation.
- **Evidence aggregation:** attach commands, outputs, hashes, and file references to each selection record entry.

## Decision tree
- One domain, one language, bounded change → single specialist; skip this module.
- Defensive security task with a named area (cloud, malware, contracts, app) → `security` + that named specialist.
- Compiler, memory, ABI, or ISA behaviour → `systems-programming` + the task-facing specialist.
- "Debug vs advanced debug": use `debugging` for reproduction, regression, and wrong-output isolation; add `debugging-advanced` for non-deterministic, concurrent, toolchain-level, or root-cause-unknown failures.
- "testing-qa vs test-engineering": use `testing-qa` for test strategy, coverage, and acceptance criteria; use `test-engineering` for test implementation, property/fuzz/contract harnesses, and fixture mechanics. A request for a test plan is not a request for a harness.
- "data-api vs database-engineering vs api-protocol-engineering vs backend-api-engineering": use `data-api` for persistence/serialization contracts, `database-engineering` for schema and query behaviour, `api-protocol-engineering` for wire-format contracts, and `backend-api-engineering` for service structure and endpoint implementation. A persistence-contract task does not become a service task merely because an API is mentioned.
- "application-security vs identity-crypto-secrets": use `application-security` for application-layer threat and control assessment; use `identity-crypto-secrets` only when identity, key management, or secret handling is the artifact. Both keep the `security` base on an assessment request.
- "mobile-engineering vs frontend-engineering vs polyglot-ecosystems": use the platform owner first; add `polyglot-ecosystems` only for a real cross-runtime boundary.
- "reverse-engineering vs reverse-engineering-architecture vs verification": use the reverse-engineering modules for observation and semantic reconstruction; `verification` verifies a stated claim and never substitutes for evidence-led reconstruction.
- Router rows that name two modules are a disambiguation branch, not a co-activation instruction: select the first module unless the row's stated condition for the second is met, and record the rejected alternative.
- Evidence insufficient to distinguish two modules → state the ambiguity, gather one bounded piece of evidence, then re-select; do not load both speculatively.
- Unfamiliar phrasing or a language other than English → classify by outcome, artifact, and acceptance criteria; preserve technical identifiers verbatim and do not require an English keyword to match. A failure to recognise a signal is a classification failure, not a reason to emit an empty set.

## Tool strategy
Confirm specialist names against the on-disk reference set before emitting them. Use exact symbol search and bounded reads to classify stack. Prefer already-exposed tools; verify invocation with a harmless call before state-changing use. When a specialist depends on an uninstalled tool, keep the specialist but record the tool as UNKNOWN and choose the documented fallback from `model-adaptation.md`. Never treat a skill filename as an installed executable.

## Advanced techniques
- **Confusion analysis:** for each specialist, track expected vs selected as TP/FP/FN across cases; a specialist with high FN and zero FP is under-selected, high FP with low FN is over-selected, and near-equal FP/FN of two names indicates a substitution pair.
- **Empty-set detection:** a fired trigger with an empty specialist list is a routing failure even when the aggregate trigger metric improves; count it explicitly.
- **Negative rejection:** measure specialist activations on prompts that should not trigger at all; these are invisible to set-based specialist F1 and must be reported separately.
- **Heuristic confidence:** report confidence only as an ordinal (low/medium/high) tied to evidence strength; a numeric score is valid only for a model whose probability calibration has been empirically measured on this suite.
- **Ablation discipline:** compare routing changes only with model, host, provider, settings, tools, permissions, fixture, prompts, and rubric pinned; write results to a new run directory.

## Failure modes
- Empty specialist list after activation → cause: description-matching failure; diagnostic: inspect which router row should have matched; recovery: apply composition rules and re-select before execution.
- Bloated selection (>3 modules for a bounded task) → cause: helper over-application; diagnostic: identify modules with no distinct responsibility; recovery: demote or drop them, keeping one primary.
- Wrong near-neighbour → cause: overlapping descriptions; diagnostic: apply the decision tree disambiguation; recovery: replace and record the rejected alternative.
- Missing cross-domain base → cause: task-facing module selected alone; diagnostic: check composition rules; recovery: add the base module as framing owner.
- Invented module name → cause: recall from memory; diagnostic: validate against reference listing; recovery: replace with the real filename before handoff.
- Helper-only selection → cause: always-on helper habit; diagnostic: check whether any selected module owns the deliverable; recovery: select a domain owner first and keep helpers subordinate.
- Framing base replaced by a near-neighbour → cause: similarity matching on the narrow domain; diagnostic: check the composition rules for security and systems-language tasks; recovery: restore the base and keep the narrow module beside it.
- Unrecognised paraphrase or non-English prompt → cause: keyword-shaped matching; diagnostic: restate the deliverable and acceptance criteria; recovery: re-select from that restatement before concluding the prompt is out of scope.

## Quality checklist
- [ ] Exactly one primary specialist owns the deliverable.
- [ ] Every supporting specialist has a distinct, stated responsibility.
- [ ] Cross-domain base+narrow composition rules were applied where relevant.
- [ ] No fired trigger produced an empty specialist list.
- [ ] The selection record was validated against the on-disk reference set before execution.
- [ ] No selection is composed only of helpers; a domain owner is present.
- [ ] Framing bases were not substituted by a near-neighbour module.
- [ ] Helpers are supporting only and individually justified.
- [ ] Selection follows the deliverable and acceptance criteria, not English keyword matching.
- [ ] No module name was invented; all exist in the reference set.
- [ ] Sequential dependencies and verifier independence are explicit.
- [ ] Confidence is ordinal unless empirically calibrated.

## Anti-patterns
- Loading every specialist "just in case" or listing a module merely because the router mentions it.
- Selecting only the task-facing module for a cross-domain task and dropping the framing base.
- Treating "X and Y" router hints as a mandate to load both.
- Using a numeric confidence score for an uncalibrated model.
- Scoring the tested model's own prose as proof that it selected correctly; use observed tool evidence.

## Verification
For a concrete run, assert: the selection record names only existing modules; every scored positive trigger has a non-empty set; the primary is unique; helper modules are not primary; no selection is helper-only; the cross-domain composition rules match the request; and the independent verifier is distinct from implementers. Use `python3 scripts/verify-objective.py --predictions <run>/WITH.jsonl --output <run>/OBJECTIVE.jsonl --definitions <run>/definitions.json` for deterministic artifact checks, then `python3 scripts/score-eval.py --predictions <run>/WITH.jsonl --objective <run>/OBJECTIVE.jsonl --baseline <run>/WITHOUT.jsonl --strict --json` for metrics and the per-specialist confusion block. An artifact check is not proof of semantic correctness, and model-dependent improvements remain INFERRED without a pinned live ablation.

## Output format
Selection record: task classification · candidate modules · selected modules · primary specialist · supporting specialists with responsibilities · verifier · reason per selection · ordinal confidence with evidence · unselected alternatives and why · required verification · handoff dependencies · detected tool fallbacks.

## Executable Verification & Failure Diagnostics
- **Verify**: For a concrete run, assert: the selection record names only existing modules; every scored positive trigger has a non-empty set; the primary is unique; helper modules are not primary; no selection is helper-only; the cross-domain composition rules match the request; and the independent verifier i...
- **Anti-Patterns**: Loading every specialist "just in case" or listing a module merely because the router mentions it.; Selecting only the task-facing module for a cross-domain task and dropping the framing base.
- **Failure Diagnostics**: A failing or ambiguous Verify result -> the first failing assertion or error line is the root cause, not the completion summary -> python3 scripts/verify-objective.py --predictions <run>/WITH.jsonl --output <run>/OBJECTIVE.jsonl --definitions <run>/definitions.json.
