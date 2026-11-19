# Independent evaluation methodology (v1.12.0)

## Problem

The v1.11 pinned control used `openrouter/tencent/hy4-flash` both as the tested
agent and as the scenario rubric judge (`score-scenarios.py`). That is a
same-model judge: it can reward its own phrasing, and it was not blind to which
arm produced a transcript. Disclosed in the control summary, but still a bias.

## Layered evidence model

| Layer | Source | Model used as judge | Status |
|---|---|---|---|
| A. Deterministic objective checks | `scripts/verify-objective.py` over retained artifacts | None | Implemented; VERIFIED by self-test |
| B. Test/artifact verification | Project test commands, hashes, file existence, `score-eval.py --objective` | None | Implemented; VERIFIED by self-test |
| C. Rubric transcript review | `scripts/score-scenarios.py` | Tested model by default; separate model via `--judge-model` | Implemented; runtime NOT VERIFIED here |
| D. Independent model judgment | `--judge-model` with an authorized distinct model | Separate model | Supported, NOT VERIFIED (no model available) |
| E. Human adjudication | Manual review of ambiguous/high-impact cases | Human | Not automated; required for disputes |

Layers A and B are necessary evidence; a Pass in layer C alone is not proof.
A completion claim without layers A/B remains explicitly UNVERIFIED.

## Blinding and repeatability in layer C

- `blind_summary()` removes `fixture-with`/`fixture-without`, `WITH.jsonl`/
  `WITHOUT.jsonl`, and `with arm`/`without arm` labels before judging. Genuine
  evidence of skill loading is preserved, because that is a legitimate rubric
  target; only the arm label is hidden.
- `--blind-order` with a recorded `--seed` shuffles judge calls so arms are not
  judged in contiguous blocks.
- Judged predictions are written to `run_dir/judged/` and the original
  `WITH.jsonl`/`WITHOUT.jsonl` are preserved. `--overwrite` restores legacy
  behaviour and should be avoided for retained controls.
- `judge-log.json` records `tested_model`, `judge_model`, `same_model_judge`,
  blinding state, seed, and the full (untruncated) judge response.
- `parse_flags()` accepts only a JSON list of the exact rubric length containing
  real booleans; the string `"false"` is rejected rather than coerced.

## Deterministic checks (layer A)

`verify-objective.py` emits one record per case with named boolean checks:

- `prediction_shape`: predicted flag and specialist list have the expected types.
- `specialists_are_known`: every emitted module name exists in the reference set.
- `activation_has_specialists`: a fired positive trigger is not left with an
  empty specialist list.
- `negative_not_activated`: a negative prompt is not activated.
- `raw_transcript_present`: the retained transcript artifact exists and is
  non-empty (when `--run-dir` is supplied).

These are artifact facts, not behavioural opinions, and never call the model
under test.

## Pinning requirements for any future live comparison

Model identifier, provider, host version, settings, tools, permissions, fixture,
prompts, rubric, scorer version, and dataset directory must be recorded in the
run `config.json`. Multiple runs must be retained; report variation, not only
the best result. Never merge runs from different providers or models.

## v1.13 status update (2026-11-19)

The five-layer architecture is unchanged. For the v1.13 bounded live ablation
(`evals/runs/v113-live-free-2026-11-19/`), layers A and B were executed on both
arms: `verify-objective.py` is now also run in CI on the frozen control and
produced six failures for the v1.11 control arm versus two for the v1.13
treatment arm on the live predictions. Layer C was not run for this new
comparison, so no rubric judgment, same-model or otherwise, is claimed for it.
Layers D and E remain NOT VERIFIED: no separate authorized judge model or human
adjudicator was available. The historical control's same-model judge bias is
still disclosed and was not retroactively removed.

## Known limitations

- No independent judge model or human adjudicator was available in this
  development environment, so layers D and E are NOT VERIFIED.
- Run order randomization reduces but does not eliminate judge style bias.
- `EVIDENCE_LIMIT = 9000` still bounds the transcript shown to layer C; rubric
  items requiring later evidence may be judged false. Layers A/B mitigate this
  for artifact-checkable items only.
- The control dataset's own `score-final.json` was produced by the older scorer;
  re-scoring it with v1.12 adds metrics but does not retroactively make its
  judge independent.
