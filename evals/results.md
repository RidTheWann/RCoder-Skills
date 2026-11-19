# Evaluation results

## Static suite status

`scripts/validate-all` enforces the current dataset contract (see `rubric.md`). The shipped corpus contains 42 trigger prompts — 24 positive and 18 negative — all English-only, plus 19 behavioral scenarios with 4 objective rubric items and a dedicated fixture file each. `evals/routing-expectations.json` records the expected specialist set for every trigger. The validator checks dataset integrity, routing metadata, manifests, host catalog, installers, and selected security patterns. It does not execute a model or a host.

## Executable scoring harness

`scripts/score-eval.py` scores JSON Lines prediction files for trigger precision/recall/F1/accuracy, specialist-selection precision/recall/F1/exact-match, scenario pass counts, and with-minus-without ablation deltas. `scripts/test-score-eval.py` verifies the scorer on synthetic perfect, mixed, and inverted runs plus four rejection paths, and passes. The protocol for producing valid prediction files is in `evals/ABLATION-PROTOCOL.md`.

A synthetic perfect-fixture smoke run scored 24 true positives, 18 true negatives, zero false positives/negatives, specialist F1 1.0, and 19/19 scenarios passed. This validates the harness only; it is not a model result.

## Live behavior — partial run, 2026-11-19

The controlled protocol is in `docs/LIVE-BENCHMARK.md`; retained artifacts are in `evals/runs/hy4-flash-free-2026-11-19/`.

**Environment (VERIFIED):** OpenCode CLI 1.19.6 via glibc loader; model `opencode/hy4-flash-free`; default reasoning variant unchanged; isolated fixtures with the canonical skill present only in the WITH arm; native skill discovery observed (`skill` tool `name: rcoder`, `SKILL.md` read). `rg` is absent, so OpenCode glob/grep/skill tools report `ripgrep execution failed` in both arms equally.

**Completion counts (VERIFIED):** WITH arm 30/42 triggers valid, 0/19 scenarios, 12 triggers invalid; WITHOUT arm 0/61 cases. The run stopped when the provider returned `AI_APICallError: Free usage limit reached`. Cases without agent text or with provider errors were excluded, not scored.

**WITH-arm trigger metrics on the valid 30-case subset (VERIFIED, scorer output retained):** TP 15, FP 0, TN 12, FN 3, precision 1.000, recall 0.833, F1 0.909, accuracy 0.643 over all 42 (12 predictions missing). Trigger detection was strong on programming/security prompts; the three misses were positive engineering prompts where the agent answered without loading RCoder.

**Specialist selection (VERIFIED):** on the 18 positive cases with expected sets, precision 0.722, recall 0.302, F1 0.426, exact-match 1/18 (0.056). This is a genuine weakness: the agent usually loaded the correct discipline family but not the full expected module set.

**Comparison:** no with-minus-without delta is reported because the baseline arm has zero valid cases. Any ablation claim remains `NOT VERIFIED`. A synthetic perfect fixture still validates only the scorer, not this model.

To finish, rerun the harness with available quota/an authorized provider so both arms complete, add scenario rubric scoring from retained transcripts, and replace this section with the full comparison.

## Environment-dependent coverage

- Non-English (for example Indonesian) user-request activation is `NOT VERIFIED`; see the language rule in `rubric.md`.
- Native discovery and skill invocation in the twenty catalog hosts are `NOT VERIFIED`; see `docs/COMPATIBILITY.md`.
- Model-specific performance claims for Hy4 Flash Free or any other model are `NOT VERIFIED` until an ablation is executed and retained here.
- Capability discovery, tool adaptation, context handoff, finding classification, and evidence-led reverse engineering now have dedicated scenarios (s15-s19) but no recorded live runs.
