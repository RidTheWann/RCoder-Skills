# Evaluation contract

This file is the single source of truth for the static evaluation dataset. `scripts/validate-all` enforces the numeric and language rules below; when this file and the validator disagree, the validator is authoritative and this file must be corrected in the same change.

## Dataset integrity gates

- **G2 — triggers:** at least 42 prompts total, at least 24 with `should_trigger: true`, at least 18 with `should_trigger: false`. IDs must be unique, prompts must be non-empty strings, and every prompt must carry `language: "EN"`.
- **G3 — scenarios:** at least 14 behavioral scenarios, unique IDs, at least 4 objective rubric items each, and a separate fixture file at `evals/scenarios/<id>.md` for every scenario. The shipped set has 19 scenarios.
- **Scoring:** `evals/routing-expectations.json` supplies expected specialist sets for trigger IDs; `scripts/score-eval.py` computes trigger, specialist, and scenario metrics and ablation deltas. The scorer is tested by `scripts/test-score-eval.py`; see `evals/ABLATION-PROTOCOL.md`.
- Static labels measure dataset integrity only. They are **not** runtime trigger accuracy, model activation, or behavioral evidence.

## Language rule

All repository-maintained evaluation prompts, fixtures, and rubrics are English-only (decision D-006). The validator rejects non-English `language` labels, and `results.md` must not claim other languages are present. Testing activation on Indonesian or any other non-English user request is a **separate runtime study**: use an English dataset record that describes the non-English request and supply the translated prompt at runtime, keeping the repository artifact English-only. Until such a run is executed, non-English activation is `NOT VERIFIED`.

## Evidence labels

Every result must classify each claim with one of:

- **VERIFIED** — observed directly in this run (command output, test result, file readback, version check).
- **INFERRED** — reasoned from verified facts; plausible but not directly observed.
- **NOT VERIFIED** — no supporting evidence in this environment.

Never downgrade a `NOT VERIFIED` item to a pass, and never describe a planned run as completed.

## Pass rule

A criterion passes only when its observable condition is met. A partial run is never called a full pass. Environment blockers are recorded with the exact command attempted and the reason it could not run.

## Ablation and comparison methodology

To measure the effect of RCoder, hold constant the model, model settings, tools, permissions, repository fixture, user prompt, and rubric. Run each case twice: once with RCoder loaded and once without. Score transcript and test evidence against the scenario rubric. Record configuration and results without secrets or personal data. Model-to-model comparisons require an identical suite and settings; never publish fabricated results.

## Coverage dimensions

The suite should exercise: instruction adherence, specialist selection (correct, incorrect, missing, overlapping, ambiguous, cross-disciplinary), tool selection, repository understanding, code correctness, debugging, architecture decisions, multi-step execution, security judgment, reverse-engineering reasoning, context preservation, final verification, failure recovery, and honesty about unverified results.
