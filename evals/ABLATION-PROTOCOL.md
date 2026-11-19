# Ablation protocol

This protocol produces a measurable with/without-RCoder result. It is a procedure, not a claim of improvement. Until it is executed and retained, model performance differences are `NOT VERIFIED`.

## 1. Pin the environment

Record in the run artifact:

- Model label, model revision or API identifier, and all sampling settings.
- Agent/CLI version and the exact tool list exposed to both runs.
- Permission boundaries, network access, working directory, and repository fixture commit.
- The exact prompt text and the rubric version from `evals/rubric.md`.

Do not change the user's selected model or settings as part of the ablation. If a capability cannot be established, record it as UNKNOWN.

## 2. Prepare predictions

Run the 42 trigger prompts and the behavioral scenarios twice under identical conditions: once with RCoder available and once without. For each case, write one JSON Lines record. Example:

```json
{"id":"trig-01","predicted_trigger":true,"selected_specialists":["data-api","application-security","testing-qa"]}
{"id":"s01-debug-regression","scenario_scores":{"s01-debug-regression":[true,true,true,true]}}
```

`selected_specialists` names module files in `skills/rcoder/references/` without the `.md` suffix; expected sets are in `evals/routing-expectations.json`. `scenario_scores` must contain one boolean per rubric item in `evals/scenarios.json`. Keep raw transcripts separately in the retained artifact set, without secrets or personal data.

## 3. Score

```sh
python3 scripts/score-eval.py --predictions WITH_RCODER.jsonl --baseline WITHOUT_RCODER.jsonl --strict
python3 scripts/score-eval.py --predictions WITH_RCODER.jsonl --baseline WITHOUT_RCODER.jsonl --json > results.json
```

The scorer computes trigger precision/recall/F1/accuracy, specialist-selection precision/recall/F1/exact-match rate, scenario pass counts, and the with-minus-without delta. `--strict` fails if any trigger prediction is missing. Invalid JSON, unknown IDs, duplicate IDs, and rubric-length mismatches exit with code 2.

## 4. Interpret

- A positive delta supports a claim only for the pinned configuration and dataset; state the scope.
- A zero or negative delta is a result, not a failure of the harness. Record it.
- Separately score completion rate, tool calls, wrong-tool calls, unsupported assumptions, security-boundary violations, unverified claims, and context consumption where measurable.
- Label every reported claim VERIFIED, INFERRED, or NOT VERIFIED.

## 5. Retain and publish

Store configurations, prediction files, transcripts, scorer output, and environment notes in `evals/results.md` or a linked run directory. Never publish fabricated or inherited model results. Re-run the full suite after any specialist change to detect regression in unrelated disciplines.
