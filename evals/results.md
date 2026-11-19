# Evaluation results

## Static suite status

`scripts/validate-all` enforces the current dataset contract (see `rubric.md`). The shipped corpus contains 42 trigger prompts — 24 positive and 18 negative — all English-only, plus 19 behavioral scenarios with 4 objective rubric items and a dedicated fixture file each. `evals/routing-expectations.json` records the expected specialist set for every trigger. The validator checks dataset integrity, routing metadata, manifests, host catalog, installers, and selected security patterns. It does not execute a model or a host.

## Executable scoring harness

`scripts/score-eval.py` scores JSON Lines prediction files for trigger precision/recall/F1/accuracy, specialist-selection precision/recall/F1/exact-match, scenario pass counts, and with-minus-without ablation deltas. `scripts/test-score-eval.py` verifies the scorer on synthetic perfect, mixed, and inverted runs plus four rejection paths, and passes. The protocol for producing valid prediction files is in `evals/ABLATION-PROTOCOL.md`.

A synthetic perfect-fixture smoke run scored 24 true positives, 18 true negatives, zero false positives/negatives, specialist F1 1.0, and 19/19 scenarios passed. This validates the harness only; it is not a model result.

## Live behavior

The controlled protocol for the first live run is in `docs/LIVE-BENCHMARK.md`. It pins host, model, settings, tools, permissions, fixture, and prompt set, then scores with `scripts/score-eval.py --strict`.

**NOT VERIFIED.** No controlled model runtime, pinned agent version, or host-native activation gate was available for the recorded runs. A static trigger label is not proof that an agent selects the correct specialist, and a successful file-copy simulation is not proof that a host discovers or invokes the skill.

To produce live results, pin model and tool versions, record permissions, run every trigger and scenario with and without RCoder under identical conditions, score each rubric item against transcript and test evidence, and retain configuration and results without secrets or personal data. Record observed capability discovery separately from assumed capabilities.

## Environment-dependent coverage

- Non-English (for example Indonesian) user-request activation is `NOT VERIFIED`; see the language rule in `rubric.md`.
- Native discovery and skill invocation in the twenty catalog hosts are `NOT VERIFIED`; see `docs/COMPATIBILITY.md`.
- Model-specific performance claims for Hy4 Flash Free or any other model are `NOT VERIFIED` until an ablation is executed and retained here.
- Capability discovery, tool adaptation, context handoff, finding classification, and evidence-led reverse engineering now have dedicated scenarios (s15-s19) but no recorded live runs.
