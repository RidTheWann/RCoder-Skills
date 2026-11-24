# Deterministic specialist routing assistant

## Activate when

A request is engineering work and you want a small, visible candidate set of specialist modules with evidence, instead of guessing from keyword co-occurrence. Use this to surface candidates; a model may override the proposal with a stated reason. It is read-only and standard-library only.

## Mission and expertise

Propose a narrow set of valid specialist modules for a natural-language request, grounded in the product router table (`SKILL.md`) and the composition rules (`specialist-routing.md`). Own candidate proposal, evidence, ordinal confidence, and scope rejection — not the final routing decision.

## Mental model

Two errors dominate routing: under-selection (drop a required base such as `security` beside a narrow security module) and over-selection (helpers presented as owners). The assistant returns only high-precision documented signals, deduplicates, applies base+narrow composition, caps the proposal at four modules, and refuses to guess when no signal fires. Confidence is ordinal (`low` / `medium` / `insufficient signal`), never a probability.

## Prerequisites and reconnaissance

1. Read `specialist-routing.md` for the composition rules before trusting any proposal.
2. Confirm candidate module names against `skills/rcoder/references/`; never invent names.
3. For multilingual (Indonesian / mixed) prompts, classify by deliverable and acceptance criteria, not by English keyword matching; keep identifiers verbatim.

## Procedure

1. Call `rcoder_route_predict` with the request text (bounded), or run `skills/rcoder/scripts/route_predict.py --text "<text>" --json`.
2. Read the `proposed` list, `primary`, `confidence`, and per-module `evidence`.
3. Apply composition rules: a security-family module implies `security`; a systems-language task implies `systems-programming`.
4. A model may override with a stated reason; record the reason in the working ledger.
5. When no module is proposed and `in_scope` is false, the request is out of scope — do not load any specialist.
6. Validate the final selection with `rcoder_validate_selection` before execution.

## Decision tree

- Documented high-precision signal fired → at least one domain module proposed; base added by composition.
- No signal fired and engineering intent present → `insufficient signal`, proposal empty; choose manually from the router table.
- No engineering intent at all → out of scope; proposal empty and `in_scope` false.
- Proposal length exceeds four → primary first, helpers last; drop extras with a note.
- Model overrides the proposal → accept only with a stated reason recorded.

## Tool strategy

- `rcoder_route_predict` MCP tool: JSON output, read-only, bounded input (20,000 chars).
- `route_predict.py`: stdlib-only CLI (`--text`, `--file`, `--json`, `--root`).
- `rcoder_validate_selection`: check the final set (one non-helper primary, no helper-only, existing names).
- Never treat a skill filename as an installed executable; probe availability before depending on it.

## Advanced techniques

- Leave-one-out scoring: score each dataset case with the training module list excluding that case, so estimates are not biased by in-sample overlap.
- Held-out cases: write cases that were never in any training signal to measure generalization honestly.
- Rejection metrics: report negative-rejection rate separately from trigger F1; empty-set positive rate must be counted explicitly.

## Failure modes

- Overclaiming the proposal as a routing decision → assistant is a proposal layer; the model owns the decision.
- Word-boundary slips (for example `sli` matching `slide`) → unit-tested regex with boundary checks.
- Loading only the task-facing module and dropping the framing base → composition rules applied after proposal.
- Empty-set positive counted as success → negative rejection and positive-empty metrics tracked separately.

## Quality checklist

- [ ] Candidate names exist in `skills/rcoder/references/` and `.rcoder/references/` overrides.
- [ ] Exactly one primary owns the deliverable; helpers are never primary.
- [ ] Cross-domain base+narrow composition applied where relevant (security, systems).
- [ ] Proposal capped at four modules with evidence per module.
- [ ] Confidence is ordinal, not a numeric probability.
- [ ] Out-of-scope requests produce an empty proposal and `in_scope: false`.
- [ ] Negative rejection measured separately from trigger metrics.
- [ ] Override reason recorded in the working ledger when the model overrides.

## Anti-patterns

- Treating the proposal as the final answer.
- Claiming in-sample accuracy as generalization.
- Numeric confidence for an uncalibrated model.
- Loading every helper "just in case."

## Verification

Run `scripts/test-route-predict.py`, which scores canonical, expanded, and multilingual datasets plus negative rejection, determinism, and boundary regression, and report leave-one-out metrics. Label metric claims with their dataset and never merge held-out results with training signals.

## Output format

```
Proposed specialists: <name>, ...
Primary: <name> | (none)
In scope: true/false | Confidence: low/medium/insufficient signal/n/a (out of scope)
  - <module>: <evidence>
Note: ...
```
