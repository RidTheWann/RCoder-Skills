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

**PARTIAL — WITH arm only.** The OpenCode 1.19.6 CLI runs in this shell through the installed glibc loader, so live runs were produced with `opencode run --model opencode/hy4-flash-free --format json` and an unchanged default reasoning variant. Isolated fixtures proved RCoder was present only in the WITH arm (SHA-256 of installed skill recorded; WITHOUT fixture had no `.opencode/skills/rcoder`). Native discovery was directly observed in the WITH arm.

Retained evidence: `evals/runs/hy4-flash-free-2026-11-19/` (config, per-case evidence, predictions, scorer output). Validity filtering kept 30/42 trigger cases with genuine agent text; 12 triggers, 19 scenarios, and the entire WITHOUT arm were not completed because the provider returned `AI_APICallError: Free usage limit reached`. The scorer was run on the valid WITH subset only; its 12 missing predictions are reported, not hidden. No ablation delta is claimed.

External blocker: provider free-tier quota. Minimum action required to finish: rerun `python3 scripts/run-benchmark.py --run-dir <new-dir> --opencode <opencode-command>` with available quota or an authorized provider, then regenerate predictions and score both arms. Do not describe this partial run as a complete benchmark.
