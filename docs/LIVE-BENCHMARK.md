# Live Intelligence Benchmark

This is the evidence gate that static validation cannot replace. Until it is executed and retained, claims that RCoder improves a specific model are `NOT VERIFIED`.

## Target of the first run

- Host: OpenCode, exact CLI version recorded from `opencode --version` or the installed package.
- Model: Hy4 Flash Free, with the session's selected reasoning variant unchanged.
- Fixture: a clean checkout of `RCoder-Skills` at a pinned commit, plus `evals/triggers.json` and `evals/scenarios.json`.
- Arms: identical prompts, tools, permissions, temperature, and repository state, once without RCoder and once with RCoder loaded.

## Procedure

1. Record the environment: CLI version, model label, settings, tool list, permission boundaries, and the exact commit. Mark anything unobservable as UNKNOWN.
2. For each of the 42 triggers, run the prompt in both arms and capture the agent's predicted trigger flag plus, when applicable, the specialist IDs it loaded.
3. For each of the 19 behavioral scenarios, run both arms against the same fixture and retain the transcript, changed files, and test output.
4. Convert captures to JSON Lines with one object per case, for example:
   `{"id":"trig-01","predicted_trigger":true,"selected_specialists":["data-api"]}`
   and `{"id":"s01-debug-regression","scenario_scores":{"s01-debug-regression":[true,true,true,true]}}`.
5. Score both arms with `python3 scripts/score-eval.py --predictions WITH.jsonl --baseline WITHOUT.jsonl --strict --json > benchmark-result.json`.
6. Score additional dimensions manually from transcripts: completion rate, tool calls, wrong-tool calls, unsupported assumptions, security-boundary violations, unverified claims, and context consumption where exposed.
7. Retain configuration, transcripts, prediction files, scorer output, and environment notes in `evals/results.md` or a linked run directory. Remove secrets and personal data.

## Interpretation

- A delta is a result only for the pinned configuration, model, fixture, and prompt set. Do not generalize to all models or IDEs.
- Report trigger precision/recall/F1, specialist exact-match, scenario pass rate, and the additional dimensions side by side.
- Label every claim `VERIFIED`, `INFERRED`, or `NOT VERIFIED`. A synthetic perfect fixture validates the scorer, not the model.
- Re-run after any routing, specialist, RSaver, or RScan change to detect regression.

## Current status (2026-11-19)

**COMPLETED.** The first attempt (`evals/runs/hy4-flash-free-2026-11-19/`) was stopped by provider free-tier quota after 30 WITH-arm triggers. With user-supplied OpenRouter credentials passed only as a per-process environment variable, the full suite was rerun using `openrouter/tencent/hy4-flash` — the same Hy4 Flash model family, different provider path — with the default reasoning variant unchanged. All 61 cases (42 triggers + 19 scenarios) ran in both isolated arms; four timeout cases were re-run, and the strict scorer exited 0 with no missing predictions.

Retained evidence: `evals/runs/hy4-flash-openrouter-2026-11-19/` (config, isolation hashes, per-case evidence, predictions, judge log, scorer output). Results: WITH trigger F1 0.889 vs WITHOUT 0.000 (delta +0.889); scenarios passed 6/19 vs 4/19; criteria pass rate 0.592 vs 0.500. Specialist exact-match was 4/24, a recorded weakness. Scenario rubric items were scored by the same pinned model as an LLM judge; raw responses and the same-model-bias limitation are retained.

These results are scoped to this exact model, CLI version, prompt set, and fixture. The earlier partial run is retained but not combined with these numbers. See `evals/results.md` for the full table.
