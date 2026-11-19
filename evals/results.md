# Evaluation results

## v1.13.0 bounded live ablation (separate from the frozen control)

Retained evidence: `evals/runs/v113-live-free-2026-11-19/`. This is a NEW run on
`opencode/hy4-flash-free` via the verified glibc-loader OpenCode 1.19.6 CLI; it
is not merged with the historical `openrouter/tencent/hy4-flash` control.

Two isolated arms used the same harness, model, prompts, fixtures, timeout, and
scorer. The CONTROL arm used the unmodified v1.11.0 skill from commit `06ec22c`
(59 references); the TREATMENT arm used the v1.13 routing changes (60
references). Twenty-four trigger IDs were executed in each arm; six IDs were
invalid in one or both arms and were excluded from both via `shared-invalid.json`,
leaving 12 comparable positive triggers.

| Metric (12 comparable positives) | CONTROL v1.11.0 | TREATMENT v1.13 |
|---|---|---|
| Trigger TP / FP / FN / TN | 11 / 0 / 1 / 6 | 9 / 0 / 3 / 6 |
| Trigger F1 | 0.957 | 0.857 |
| Specialist precision / recall / F1 | 0.778 / 0.241 / 0.368 | 0.769 / 0.345 / 0.476 |
| Specialist exact-match | 0.000 | 0.083 |
| Empty specialist sets | 7 / 12 | 5 / 12 |
| Recorded tokens (12 positives) | 311,619 | 313,092 |
| Tool calls (12 positives) | 99 | 98 |
| Deterministic objective failures | 6 | 2 |

**Classification:** all table values are VERIFIED deterministic computations over
retained artifacts. The higher specialist recall/F1, one exact-match, fewer empty
sets, and fewer objective failures are genuine observations in this small sample;
the trigger-F1 regression is also a genuine observation and is not hidden.
Causality and statistical significance are INFERRED at most. A post-run free-tier
probe timed out, so full 42-trigger, scenario, expanded, and multilingual live
runs are NOT VERIFIED; no paid provider was used. See the run `SUMMARY.md` for
configuration and limitations.

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

## v1.12.0 case-level analysis and instrumented re-score

The original control artifacts are immutable (hashes in `evals/runs/BASELINE-LEDGER.md`). Re-scoring them with the v1.12 deterministic scorer does NOT produce a new model result; it adds measurements that the older scorer omitted.

Re-score command (read-only; output written outside the run directory):
`python3 scripts/score-eval.py --predictions evals/runs/hy4-flash-openrouter-2026-11-19/WITH.jsonl --baseline evals/runs/hy4-flash-openrouter-2026-11-19/WITHOUT.jsonl --invalid-cases evals/runs/hy4-flash-openrouter-2026-11-19/invalid-cases.json --strict --json`

**Newly exposed evidence (VERIFIED as deterministic re-computation over retained artifacts):**

| Measurement | Value |
|---|---|
| Invalid cases excluded by v1.12 scorer | WITH: `trig-34`, `trig-35`; WITHOUT: `s07-safe-refactor`, `s12-authorized-security-assessment` |
| Trigger F1 after invalid exclusion | 0.878 (old aggregate 0.889) |
| Specialist F1 / exact-match after invalid exclusion | 0.488 / 0.182 (old aggregate 0.444 / 0.167) |
| Positive prompts with an empty specialist set | 10 / 24 = 0.417 |
| Specialist false activations on negative prompts | 0 / 18 = 0.000 |
| Negative prompt rejection rate | 0.944 (one false activation: `trig-24`) |
| Cross-domain subset (8 scored) | F1 0.457, exact-match 0.125 |
| `security` | TP 1, FN 5 |
| `systems-programming` | TP 0, FN 3 |
| `verification` | TP 0, FP 3 |

The old scorer included invalid case `trig-35` because predictions never carried a validity signal; v1.12 excludes it by default. Strict mode now reports missing predictions for the excluded positives, which is the correct behaviour. Primary diagnosed causes: (1) description-matching failures producing empty selections after activation; (2) missing cross-domain base-plus-narrow composition; (3) near-neighbour substitutions (`testing-qa`/`test-engineering`, `debugging`/`debugging-advanced`); (4) helper over-application. Several expectation labels are also arguably ambiguous (for example `trig-35` expecting `model-adaptation`), so exact-match instability is partly a dataset defect, not only a router defect.

**No new model run was executed for v1.12**: `opencode` was unavailable in the development shell and no paid run was authorized. Routing improvements are therefore implemented and structurally tested but their effect on the pinned metrics is INFERRED, NOT VERIFIED.

## Environment-dependent coverage

- Non-English (for example Indonesian) user-request activation is `NOT VERIFIED`; see the language rule in `rubric.md`.
- Native discovery and skill invocation in the twenty catalog hosts are `NOT VERIFIED`; see `docs/COMPATIBILITY.md`.
- Model-specific results are retained above for `openrouter/tencent/hy4-flash` only. Results for `opencode/hy4-flash-free` remain a partial run, and results for any other model are `NOT VERIFIED`.
- Capability discovery, tool adaptation, context handoff, finding classification, and evidence-led reverse engineering have dedicated scenarios (s15-s19) with live runs; their pass/fail outcomes are in `evals/runs/hy4-flash-openrouter-2026-11-19/score-final.json`.
