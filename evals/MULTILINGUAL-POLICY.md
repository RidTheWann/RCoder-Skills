# Multilingual activation policy (v1.12.0)

## Scope and non-regression

The canonical evaluation contract is unchanged: `evals/triggers.json`,
`evals/routing-expectations.json`, and `evals/scenarios.json` remain English-only
(`language: "EN"`) and are enforced by `scripts/validate-all`. This policy file
introduces a **separate** research dataset and does not modify, translate, or
relabel any canonical prompt. No canonical score may be recomputed by silently
substituting a translated prompt.

## Rationale

The v1.11 pinned control measured English-only routing. Real users switch
languages and mix technical English with Indonesian prose. A language
comprehension failure and a specialist-routing failure are different defects and
must be distinguishable in the evidence.

## Dataset

`evals/datasets/multilingual.triggers.json` contains prompts tagged `ID`, `EN`,
or `MIXED_ID_EN`, with `expected_specialists`, `identifier_integrity` terms, and
a note per case. Two cases are negative controls that must not activate any
engineering specialist.

## Evaluation rules

1. Send each prompt verbatim; do not translate it before submission.
2. Keep the `language` tag and raw prompt in the retained run artifact.
3. Score routing against `expected_specialists` with the same set-based metrics
   used by `scripts/score-eval.py`, but in a separate run directory. Never merge
   this run with an English control run or report a combined number.
4. Check `identifier_integrity` separately: API names, language names, and
   technical terms must remain unchanged. A translated identifier is a failure
   even if the specialist set is correct.
5. Repository-maintained instructions stay in English (per `SKILL.md`); the user
   receives a coherent response in the language they used. This is a runtime
   behaviour requirement, not a change to repository artifacts.
6. Record which specialist errors are language-independent by comparing the same
   task in English and Indonesian where a paired case exists.

## Status

The dataset and protocol are VERIFIED as files and structure. Runtime routing
accuracy for these prompts is NOT VERIFIED: no live model run was executed in the
v1.12 development environment (`opencode` unavailable). Do not report a
multilingual accuracy number until a pinned run exists.

Update (2026-11-19, v1.13): a live runtime is now available through the verified
glibc loader, but the free-tier quota was exhausted after the bounded English
control/treatment ablation. No multilingual live run was executed. The routing
instructions now classify by deliverable and acceptance criteria rather than
English keywords, which is an INFERRED improvement for these prompts only; it is
not a measured multilingual result. The separate dataset and policy remain
unchanged and must be evaluated as their own experiment.


## RCoder 2.0 authoring and multilingual activation

The runtime routing contract is now explicit in the top-level skill and specialist-routing reference:

- Respond in the user's predominant language while repository-maintained skill instructions remain English.
- Classify by requested deliverable, acceptance criteria, domain, and risk—not English-only keyword matching.
- Preserve API names, commands, file paths, code identifiers, standards, and product names exactly.
- A mixed-language prompt remains one semantic request; language switching alone does not justify additional specialists.
- MCP transport changes route to mcp-transport-engineering; add agent-extensions-engineering only when host plugins, Agent Skills, marketplaces, or installers are also in scope.

The separate multilingual dataset now contains 12 verbatim prompts across Indonesian, English, and mixed Indonesian-English, with explicit specialist expectations, identifier-integrity terms, and negative controls. Run:

```sh
python3 scripts/test-multilingual-data.py
```

This is a static dataset/integrity test only. It does not run an agent model and does not measure routing accuracy. Native multilingual behavior remains NOT VERIFIED until a pinned live run records the raw prompts and observed selected specialist set in a separate multilingual run directory. The English control suite remains English-only and is not translated or relabeled.
