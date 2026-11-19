# Live benchmark run — hy4-flash-free, 2026-11-19 (PARTIAL)

## Verdict

WITH-arm only. The baseline arm and all scenarios could not run because the provider returned `AI_APICallError: Free usage limit reached`. This is not a complete benchmark and no ablation delta is claimed.

## Pinned configuration

- CLI: OpenCode 1.19.6 (`opencode-linux-arm64` via glibc loader on Termux aarch64).
- Model: `opencode/hy4-flash-free`; reasoning variant left at the session default (unchanged).
- Fixture: isolated temp projects. WITH arm received the canonical skill at `.opencode/skills/rcoder` (SHA-256 `3876bae1d01b6527d117aa3f50ceb704703a20e6779d2f32f69e4b1169b7f46a`); WITHOUT arm had no RCoder skill.
- Isolation: verified by fixture state and by tool events in WITH transcripts (skill tool invocation, SKILL.md read, specialist reads). The WITHOUT arm has no transcripts.
- Tool limitation: `rg` is absent, so OpenCode glob/grep/skill tools report `ripgrep execution failed` in both setups; the agent recovered via `bash`/`read`.

## Completion counts (VERIFIED)

| Arm | Triggers valid | Triggers invalid/not run | Scenarios valid |
|---|---|---|---|
| WITH RCoder | 30 / 42 | 12 | 0 / 19 |
| WITHOUT RCoder | 0 / 42 | 42 | 0 / 19 |

## WITH-arm trigger results on the valid subset (VERIFIED)

Scorer command: `python3 scripts/score-eval.py --predictions evals/runs/hy4-flash-free-2026-11-19/WITH.jsonl --json`

- TP 15, FP 0, TN 12, FN 3
- precision 1.000, recall 0.833, F1 0.909, accuracy 0.643 over all 42 (12 predictions missing)
- Specialist selection over 18 expected-set positives: precision 0.722, recall 0.302, F1 0.426, exact-match 1/18 (0.056)

Trigger detection was strong when the agent recognised a software-engineering task. The three misses were positive prompts answered without loading RCoder. Specialist selection was the weak dimension: the agent typically loaded the correct discipline family but not the full expected module set.

## Files

- `config.json` — pinned environment and stop reason.
- `case-summary.json` — per-case detection, tool, token, and timing evidence.
- `WITH.jsonl` — only valid WITH-arm records; derived from JSON events, never synthesised.
- `WITHOUT.jsonl` — empty (no valid baseline cases).
- `invalid-cases.json` — excluded cases and reasons.
- `score-with.json` / `score-with.err` — actual scorer output.

## Reproduce

With provider quota available:

```sh
python3 scripts/run-benchmark.py --run-dir <new-dir> --opencode <opencode-command> --parallel 4 --timeout 120
python3 scripts/score-eval.py --predictions <new-dir>/WITH.jsonl --baseline <new-dir>/WITHOUT.jsonl --strict --json
```

Raw transcripts were retained locally in the runner's run directory; only sanitised summaries and predictions are committed here.
