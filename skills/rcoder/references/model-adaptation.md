# Model adaptation and agent orchestration

## Activate when
Selecting how to work with the active model or host; beginning a session on an unfamiliar agent; deciding how much context, planning, delegation, or verification is justified; measuring whether RCoder improves outcomes; comparing models or settings; handling long multi-session tasks. Do not activate for a domain implementation decision that already has a selected specialist.

## Mission and expertise
Maximize useful engineering work from the model actually present, without assuming a particular intelligence level, context size, tool schema, reasoning reliability, or execution capability. Produce observable capability evidence, choose the smallest sufficient execution profile, and measure results instead of asserting improvements. This module adapts *how* RCoder is applied; it does not override domain specialists, safety policy, or user instructions.

## Mental model
Three principles govern adaptation:

1. **Observability over introspection.** Ask what the runtime exposes, not what the model thinks it is. A capability is known only when a probe or documented host feature demonstrates it.
2. **Smallest sufficient workflow.** Planning, context loading, delegation, and verification scale with risk and uncertainty. Extra ceremony that does not change an outcome is cost, not quality.
3. **Evidence over reputation.** A model is not "better at coding" because of its name. Differences are measured with identical tasks, tools, permissions, and rubrics.

## Prerequisites and reconnaissance
Before adapting behavior:

1. Record the host, agent version, model label, and session settings that are actually visible. If a version command is unavailable, say so.
2. Probe the tool surface with harmless calls: file read/write in a temporary location, exact search, bounded command execution, and (if claimed) web access. Record the observed argument schema from tool output or host documentation, not memory.
3. Determine permission boundaries: which paths are writable, whether network calls succeed, whether state-changing tools prompt, and whether operations are sandboxed.
4. Determine delegation availability and behavior with one small, independent task before relying on it for real work.
5. Determine continuity features for long tasks (context compaction, session persistence, handoff files). If unknown, use the repository context capsule.
6. Mark every unestablished capability `UNKNOWN`. Do not ask the model to describe its own architecture, training, or context window.

Keep this evidence in `docs/ENVIRONMENT.md` or an equivalent project ledger.

## Procedure
1. Classify the task: discipline, language/runtime, platform, complexity, safety constraints, deliverable, verification needs, and available tools.
2. Select the smallest sufficient profile from the table below; justify any upgrade in one sentence.
3. Load the router first, then only the specialists the classification requires. Do not preload the library.
4. Plan in proportion to risk: a mental outline for focused work, an ordered plan with acceptance criteria for engineering work, a written investigation ledger for research and long tasks.
5. Execute with the narrowest correct change. Delegate only independent, well-scoped work; serialize all writes.
6. Verify with the profile's minimum evidence bar, then inspect the final diff.
7. For long tasks, update the context capsule before compaction or handoff and preserve exact commands, results, decisions, and unresolved hypotheses.
8. After completion, record which profile was used and whether it was sufficient; feed recurring failures into evaluation scenarios.

## Adaptive execution profiles

| Profile | Use when | Context to load | Planning | Specialists | Subagents | Verification bar | Handoff evidence |
|---|---|---|---|---|---|---|---|
| **Focused** | Single file, small bug, bounded question, clear acceptance criteria | Router + at most one specialist | Mental outline | One, or none for pure config | Not worth the overhead | Narrow test or direct readback; final diff | Outcome, changed file, command/result |
| **Engineering** | Normal multi-file change, feature, migration with known steps | Router + relevant domain + testing + verification | Short ordered plan with observable criteria | Two to four, loaded as needed | Only for independent research or parallel test prep | Narrow test first, then lint/type/build and documented gate | Decisions, changed files, exact checks, residual risks |
| **Deep Research** | Ambiguous behavior, architecture tradeoffs, security research, reverse engineering, uncertain tool behavior | Router + domain + verification + token efficiency; add evidence-focused specialists | Written investigation ledger with hypotheses and falsifiers | Domain plus verification/evidence specialists | Useful for parallel, independent evidence gathering with disjoint scopes | Reproducible experiment or independent source per material claim; label confidence | Observation vs interpretation vs hypothesis, provenance, commands, unresolved items |
| **Long-Running Project** | Large repository, multi-session work, complex handoffs, many stakeholders | Router + current domain slice only; capsule carries the rest | Milestone plan with acceptance criteria and explicit next action | One slice at a time, reselected at each milestone | Effective for isolated workstreams with file ownership and written contracts | Milestone gates plus full final gate; re-run affected tests after handoff | Current capsule: objective, branch/status, decisions, changed files, tests, failures, hypotheses, boundaries, next action |

Profiles are guides, not rituals. Downgrade when evidence shows the extra process is not changing outcomes; upgrade when uncertainty or blast radius grows.

## Decision tree
- One file, obvious fix, no cross-module contract? → **Focused**.
- Multiple files with a known integration point and existing tests? → **Engineering**.
- Root cause unknown, evidence conflicting, or claim affects security/semantics? → **Deep Research** and load verification.
- Work spans sessions, or a handoff/compaction is likely? → **Long-Running Project** plus a capsule.
- Context budget tight but correctness gate is mandatory? → Reduce *reading*, not verification; narrow the specialist set before skipping a test.
- Model cannot reliably use a tool after a fair probe? → Switch to an available alternative and record the limitation; do not keep retrying the same broken schema.

## Tool strategy
- Prefer tools already exposed by the host; never assume a skill installation adds an executable. When a shell is available, `python3 skills/rcoder/scripts/tool_probe.py resolve --candidate <name>` verifies discoverability, `version --candidate <name> --strict` detects a version through an ordered fallback list, and `chain` runs an ordered fallback list with a hard timeout, bounded output capture, process-group cleanup on POSIX, and at most one attempt per tool. It does not retry identical commands; a retry requires a changed condition chosen by the caller. A fallback is not assumed to have identical semantics to the preferred tool. Record which tool was actually invoked.
- Match operation to tool: shell for process/version/build tasks, search for symbol location, bounded read for source, structured edit for changes, delegation for independent parallel work.
- Validate a tool's argument schema with a harmless call before depending on it for a state-changing action.
- When web access is unavailable or disallowed, rely on local sources and mark external verification `NOT VERIFIED`.
- Keep network use proportional to uncertainty; prefer official and version-matched sources over search snippets.

## Advanced techniques
- **Ablation design:** run with and without RCoder while holding constant the model, settings, tools, permissions, fixture, prompt, and rubric. Score transcript and test artifacts, not specialist names in prose.
- **Dimension coverage:** evaluate instruction adherence, specialist selection (correct/missing/incorrect/overlapping/ambiguous/cross-disciplinary), tool selection, repository understanding, code correctness, debugging, architecture, multi-step execution, security judgment, reverse-engineering reasoning, context preservation, final verification, failure recovery, and honesty about unverified results.
- **Metrics:** completion rate, test pass rate, tool calls, wrong-tool calls, unsupported assumptions, security-boundary violations, unverified claims, and context consumption where measurable.
- **Regression:** keep a fixed regression set of routing and behavior cases; a specialist improvement must not degrade unrelated disciplines.
- **Comparison:** models may be compared only on an identical suite with pinned settings; publish no fabricated or inherited results.
- **Capability probing:** use minimal fixtures whose expected output is unambiguous, so a tool failure cannot be mistaken for model failure.

## Failure modes
- **Over-delegation:** a model that cannot reliably manage subagents produces conflicting edits. Recover by serializing work in the main session and recording the limitation.
- **Profile inflation:** deep research performed for a one-line fix wastes context. Recover by downgrading and restating acceptance criteria.
- **Schema guessing:** invented tool arguments cause repeated failures. Recover by reading tool help or a known-good example, then mark unknown capabilities explicitly.
- **Reputation bias:** assuming a model is strong or weak by name. Recover by running a small, objective probe.
- **False success:** claiming an improvement without an ablation. Recover by labeling the claim `INFERRED` until evidence exists.
- **Context loss:** compaction discards verified facts. Recover from the capsule; re-verify anything that changed after it was written.

## Quality checklist
- [ ] Host, version, model label, and settings are recorded or explicitly `UNKNOWN`.
- [ ] Capabilities are based on observed probes or documented host features.
- [ ] The selected profile is the smallest sufficient one, with a justification.
- [ ] Only relevant specialists were loaded.
- [ ] Subagents, if used, had disjoint scopes and acceptance criteria.
- [ ] Verification met the profile's evidence bar and the final diff was reviewed.
- [ ] Unmeasured improvements are labeled `INFERRED` or `NOT VERIFIED`.

## Anti-patterns
- Hardcoding "this model needs short prompts" or "that model handles long documents" without a benchmark.
- Treating a high reasoning setting as evidence of a capability.
- Loading every specialist "just in case" or delegating trivial work to look thorough.
- Reporting a skill as activated because its file exists on disk.
- Changing the user's selected model or settings without a reason tied to evidence.

## Verification
Re-run the capability probes after any host or agent upgrade. For performance claims, retain the pinned configuration, the with/without transcript or artifact set, per-criterion scores, and the environment record. Store results in `evals/results.md`; never overwrite a failing result with a narrative success.

## Output format
Profile selected and why · observed capabilities and unknowns · specialists loaded · delegation decisions · exact verification commands/results · evidence labels (VERIFIED / INFERRED / NOT VERIFIED) · residual risks · next action.
