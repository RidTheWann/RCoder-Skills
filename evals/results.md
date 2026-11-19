# Evaluation results

## Static suite status

`scripts/validate-all` enforces the current dataset contract (see `rubric.md`). The shipped corpus contains 42 trigger prompts — 24 positive and 18 negative — all English-only, plus 19 behavioral scenarios with 4 objective rubric items and a dedicated fixture file each. `evals/routing-expectations.json` records the expected specialist set for every trigger. The validator checks dataset integrity, routing metadata, manifests, host catalog, installers, and selected security patterns. It does not execute a model or a host.

## Executable scoring harness

`scripts/score-eval.py` scores JSON Lines prediction files for trigger precision/recall/F1/accuracy, specialist-selection precision/recall/F1/exact-match, scenario pass counts, and with-minus-without ablation deltas. `scripts/test-score-eval.py` verifies the scorer on synthetic perfect, mixed, and inverted runs plus four rejection paths, and passes. The protocol for producing valid prediction files is in `evals/ABLATION-PROTOCOL.md`.

A synthetic perfect-fixture smoke run scored 24 true positives, 18 true negatives, zero false positives/negatives, specialist F1 1.0, and 19/19 scenarios passed. This validates the harness only; it is not a model result.

## Live behavior — completed ablation, 2026-11-19

The controlled protocol is in `docs/LIVE-BENCHMARK.md`; retained artifacts for the completed run are in `evals/runs/hy4-flash-openrouter-2026-11-19/`.

**Environment (VERIFIED):** OpenCode CLI 1.19.6 via glibc loader; model `openrouter/tencent/hy4-flash` (same Hy4 Flash family as the quota-blocked `opencode/hy4-flash-free` attempt, different provider path authorized by the user); default reasoning variant unchanged; isolated fixtures with the canonical skill present only in the WITH arm; native skill discovery observed (`skill` tool `name: rcoder`, `SKILL.md` read). `rg` is absent, so OpenCode glob/grep/skill tools report `ripgrep execution failed` in both arms equally. No credential is stored in any artifact.

**Completion (VERIFIED):** all 61 cases (42 triggers + 19 scenarios) × 2 arms completed; four timeout cases were re-run with a longer timeout, so `python3 scripts/score-eval.py --predictions WITH.jsonl --baseline WITHOUT.jsonl --strict --json` exited 0 with zero missing trigger predictions.

| Metric | WITHOUT RCoder | WITH RCoder | Delta |
|---|---|---|---|
| Triggers TP / FP / TN / FN | 0 / 0 / 18 / 24 | 20 / 1 / 17 / 4 | — |
| Trigger precision | 0.000 | 0.952 | +0.952 |
| Trigger recall | 0.000 | 0.833 | +0.833 |
| Trigger F1 | 0.000 | 0.889 | +0.889 |
| Trigger accuracy | 0.429 | 0.881 | +0.452 |
| Specialist F1 / exact-match | — | 0.444 / 4 of 24 (0.167) | — |
| Scenarios passed | 4 / 19 | 6 / 19 | +2 |
| Rubric criteria pass rate | 0.500 | 0.592 | +0.092 |

**Interpretation (VERIFIED for this configuration):** RCoder changed trigger behavior strongly — the baseline never activated, while the WITH arm activated on 20 of 24 positives with one false positive. Specialist selection remains the weak dimension: exact match was only 4/24. Scenario pass rates improved modestly. Scenario rubric items were scored by the same pinned model as an LLM judge over bounded transcripts (same-model bias disclosed; raw responses retained). These numbers apply only to this pinned model, host, prompt set, and fixture; they do not generalise to other models or hosts.

**Earlier partial run:** `evals/runs/hy4-flash-free-2026-11-19/` retains the first attempt, which was stopped by provider free-usage quota after 30 WITH-arm triggers with no baseline arm. It is not combined with the completed numbers above.

## Environment-dependent coverage

- Non-English (for example Indonesian) user-request activation is `NOT VERIFIED`; see the language rule in `rubric.md`.
- Native discovery and skill invocation in the twenty catalog hosts are `NOT VERIFIED`; see `docs/COMPATIBILITY.md`.
- Model-specific results are retained above for `openrouter/tencent/hy4-flash` only. Results for `opencode/hy4-flash-free` remain a partial run, and results for any other model are `NOT VERIFIED`.
- Capability discovery, tool adaptation, context handoff, finding classification, and evidence-led reverse engineering have dedicated scenarios (s15-s19) with live runs; their pass/fail outcomes are in `evals/runs/hy4-flash-openrouter-2026-11-19/score-final.json`.
