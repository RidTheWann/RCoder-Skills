# Weak-model execution profile

## Activate when

The active model is a small/weak/cheap tier (parameter count < 30B active, or context window ≤ 32K, or reasoning reliability is unverified) and the task is multi-file, requires tool use, or spans multiple turns. Do not activate for single-file fixes with a clear acceptance criterion and a Focused profile.

## Mission and expertise

Define a deterministic, prompt-only execution policy that makes a weak model competitive with frontier models on coding tasks by enforcing structural discipline: contract-first requirements, bounded exploration, early editing, single focused verification, and explicit loop/stop criteria. This is a harness-layer policy, not a model capability claim — it works because the policy removes decision points where weak models fail, not because it teaches the model to reason better.

## Mental model

Weak models fail on long-horizon tasks for three reasons that are not "intelligence" but process:
1. **Premature abandonment**: without a plan, they stop at localization and never edit.
2. **Unproductive loops**: they repeat the same tool calls (search, read) with no progress.
3. **Over-exploration**: they burn context on files the task never touches.

The policy addresses each with a hard constraint (deadline, detector, budget) rather than a suggestion. Evidence: Fan et al. 2026 (arXiv 2609.20804) — planning raises weak-model success +11.6pp; Ghosh 2026 (arXiv 2610.30284) — budget-disciplined prompt scored 0.13 on Gemma 4 competition; McAndrews 2026 (arXiv 2604.21950) — self-refine with execution feedback +4σ on 1-3B models.

## Prerequisites and reconnaissance

1. Identify the active model's tier (parameter count, context window, reasoning mode) from observed capability probes, not reputation. Mark UNKNOWN if unobserved.
2. Determine the available tool set and which tools have cheap verifiers (pytest -k, grep, type check).
3. Generate or load the repository structural map (`repo_map.py`) before the first tool call — this is the orientation layer that replaces blind exploration.
4. Define the autonomy ceiling (A0–A3) for this task per the operating contract.

## Procedure

1. **Generate repo map** (once per session, refresh on significant edits):
   ```
   python3 <skill-dir>/scripts/repo_map.py --root . --budget 2048 --format default
   ```
   Keep this map in context for every turn.

2. **PLAN phase** (before any tool call):
   - Write a numbered checklist of atomic steps (max 8; split if more).
   - Each step: ≤2 files, 1-2 sentences, concrete verification (test, grep, read-back).
   - Emit the plan as a markdown block; do not proceed until the plan exists.

3. **FOCUS phase** (context discipline per turn):
   - Read only the section needed (line ranges, or grep first). Never read a whole file >150 lines.
   - At most 2 files' content in working context at once. Summarize and drop the older.
   - Re-read target section before editing; do not rely on memory >1500 tokens old.

4. **ACT phase** (edit discipline):
   - Edit early: by tool call 12, a source file must be modified.
   - Each edit <30 lines; prefer str_replace over rewriting.
   - Never generate boilerplate from memory; read an existing example first.

5. **VERIFY phase** (bounded verification):
   - Run at most ONE focused test (pytest -k, python -c, or type check).
   - Allow ONE repair if the failure is an assertion about the changed behavior.
   - Ignore failures from missing fixtures, import errors, pre-existing breakage.

6. **Loop / stop criteria** (hard limits):
   - Tool-call budget: 28 calls (configurable per context window).
   - Anti-loop detector: ≥6 identical tool calls (same tool + normalized args) OR ≥15 consecutive calls with no artifact produced → strong corrective hint, then hard reset.
   - Time budget: 8 minutes (configurable).
   - Stop and report partial status if any budget is exhausted before scope completes.

7. **Operating contract** (per task):
   - Autonomy ceiling: A0 (analyze), A1 (propose), A2 (execute controlled), A3 (publish).
   - Allowed tools: explicit allowlist; deny the rest.
   - Minimum evidence: summary of change per file, acceptance criteria evidence, executed tests with results, consumed budget log.
   - Delegation never raises the ceiling; sub-tasks run at min(parent ceiling, target ceiling).

## Decision tree

- No repo map generated yet → generate it first, do not search.
- No written plan exists → write the plan, do not call tools.
- Tool call 12 reached with no edit → edit the most likely function at once (smallest change).
- Verification fails 3 times on same step → split step, re-read fresh, attempt sub-step 1.
- Anti-loop detector trips → apply corrective hint, then hard reset turn if it persists.
- Budget exhausted → stop, emit partial status with consumed budget and remaining gaps.
- Task scope changes → new plan, new budget, new repo map if significant.

## Tool strategy

- **Required**: repo_map.py (orientation), context_snapshot.py (bounded path map), rsaver.py gate (budget enforcement).
- **Allowed by default**: read_file, edit_file, write_file, run_command, grep, glob, submit_patch, get_status.
- **Denied by default for weak profile**: web search, browser, graph-oriented tools (get_code_neighbors, search_similar_code, get_code_subgraph) — they expand the action space without a cheap verifier.
- **Escalation**: if a task requires a denied tool, escalate to a stronger model or human (A0/A1 ceiling).

## Advanced techniques

- **Contract-first prompting**: before any tool call, the agent lists exact symbols, signatures, error strings, status codes, and return values the issue requires — copied character-for-character from the issue or repo.
- **Structured note-taking**: maintain `/notes.md` with curated findings (not append-only); cap at 8000 chars.
- **Verifier ground truth**: whenever a candidate solution is produced, run public tests immediately; pass/fail overrides any "done" claim (GVS5H pattern).
- **Fresh-perspective workers**: for critical decisions, spawn a worker with the raw problem and no prior context to avoid anchoring on a wrong early approach.
- **Heterogeneous model config**: weak model handles generation attempts; strong model reserved for planning interventions only (PaT pattern).

## Failure modes

- **Policy ignored**: treating the rules as suggestions → weak model reverts to exploration loops. Recover by enforcing via harness (not prompt).
- **Budget too tight**: early-edit deadline forces premature changes; single check misses regressions. Tune budgets per task family.
- **Repo map stale**: edits during session make the map describe a repo that no longer exists. Rebuild on significant edits or every N turns.
- **Verifier missing**: no cheap test → cannot bound verification. Add a minimal test harness first.
- **Context rot**: compaction loses subtle critical context. Use RSaver anchor + capsule; never drop verification evidence.

## Quality checklist

- [ ] Repo map generated and in context before first tool call.
- [ ] Written plan exists with ≤8 atomic steps, each with concrete verification.
- [ ] Context budget respected: ≤2 files in working context, line-range reads only.
- [ ] Edit by tool call 12; each edit <30 lines; str_replace preferred.
- [ ] At most one focused test + one repair per edit; ignore pre-existing failures.
- [ ] Anti-loop detector active with thresholds (≥6 identical / ≥15 empty).
- [ ] Operating contract declared with autonomy ceiling, tool allowlist, stop criteria, evidence minimum.
- [ ] Delegation respects ceiling (min of parent and target).
- [ ] Partial status emitted on budget exhaustion with explicit remaining gaps.

## Anti-patterns

- Adding more harness structure without a measured failure justifying it (mega-harness anti-pattern).
- Letting the model grade its own work — verification quality is model-bound.
- Substituting an LLM judge at the same weak tier for a missing verifier.
- Expecting best-of-N to rescue a weak model where no oracle exists.
- Treating a weak result or leading score as an intrinsic property of the model (harness matters).

## Verification

Run the ablation: same model, same tasks, same tools, same budget — with and without the weak-model profile. Report:
- Resolution rate (pass@1)
- Cost per verified pass (tokens × price)
- Trajectory length (turns, tool calls)
- Loop rate (fraction of trajectories with ≥10 identical calls)
- Context overflow rate (fraction of trajectories hitting window limit)
- Comparison against a stronger model without the profile (Pareto frontier).

Baseline numbers from literature (2026):
- Repo map: wrong-file edits 47→0, pass rate 31.9%→79.2%, cost 17× lower.
- Planning: +11.6pp weak model, -30% cost strong model.
- Self-refine + execution feedback: +4σ on 1-3B, early stopping essential.
- Budget-disciplined prompt: 0.13 leaderboard score on Gemma 4 31B.

## Output format

Emit a short status block at each phase transition so a supervisor or harness can verify discipline without reading the transcript:

```
## Weak-Model Profile Active
Autonomy: A1 (propose) | Budget: 28 calls / 8 min / 2048-token repo map
Repo map: generated (N files, ~M tokens) | Plan: 5 steps (verified 2/5)
Context: 1 file in working set (target.py:40-80) | Anti-loop: clean
Last verification: pytest -k test_payment passed
Next: Step 3 — Edit auth.py: add token rotation
```