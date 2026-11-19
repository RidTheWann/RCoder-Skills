# Complete live ablation — Hy4 Flash via OpenRouter, 2026-11-19

## Verdict

**Full suite completed and reproducible.** All 61 cases (42 triggers + 19 scenarios) ran in both arms with the model, CLI, prompts, fixture, tools, permissions, and rubric held constant. Four timeout cases were re-run with a longer timeout, so `--strict` passes with zero missing trigger predictions in either arm.

## Configuration

- CLI: OpenCode 1.19.6 via glibc loader on Termux aarch64.
- Model: `openrouter/tencent/hy4-flash` — the same Hy4 Flash family as the earlier quota-blocked `opencode/hy4-flash-free` run; only the provider path changed, using user-supplied OpenRouter credentials passed as a per-process environment variable. No credential appears in any retained artifact. The reasoning variant was left at the default.
- Fixtures: isolated temporary projects. WITH arm alone received the canonical v1.11.0 skill at `.opencode/skills/rcoder`; isolation hashes are in `isolation.json`.
- Tool limitation: `rg` is absent, so OpenCode glob/grep/skill tools report `ripgrep execution failed` in both arms equally.
- Scenario rubric scoring used the same pinned model as an LLM judge over bounded transcript summaries; raw judge responses are in `judge-log.json`. Same-model bias is disclosed.

## Results (scorer: `score-final.json`, `--strict`, exit 0)

| Metric | WITHOUT RCoder | WITH RCoder | Delta |
|---|---|---|---|
| Triggers TP / FP / TN / FN | 0 / 0 / 18 / 24 | 20 / 1 / 17 / 4 | — |
| Trigger precision | 0.000 | 0.952 | +0.952 |
| Trigger recall | 0.000 | 0.833 | +0.833 |
| Trigger F1 | 0.000 | 0.889 | +0.889 |
| Trigger accuracy | 0.429 | 0.881 | +0.452 |
| Specialist F1 | — | 0.444 (P 0.524, R 0.386, EM 4/24 = 0.167) | — |
| Scenarios passed | 4 / 19 | 6 / 19 | +2 |
| Rubric criteria pass rate | 0.500 | 0.592 | +0.092 |

## Interpretation

RCoder changed trigger behavior substantially: the baseline never activated on any engineering prompt, while the WITH arm activated on 20 of 24 positives with one false positive on a non-engineering prompt. Specialist selection remains the weak dimension — exact match was 4/24, so activation alone does not guarantee the expected module set. Scenario pass rates improved modestly (4 → 6 of 19), with most criteria still unmet under the judge's evidence-only rule.

These results apply only to this pinned configuration. They do not generalise to other models, hosts, or prompt sets, and the same-model judge is a bias to account for. The earlier `hy4-flash-free-2026-11-19` run remains retained as a documented partial run with a different provider path; it is not combined with these numbers.
