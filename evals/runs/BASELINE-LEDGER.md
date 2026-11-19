# Baseline ledger — RCoder v1.12.0 evolution

This file is the immutable control record for the v1.12 engineering evolution.
It was written BEFORE any routing, specialist, or evaluator content was changed.
The historical control dataset it fingerprints is never overwritten.

## Source baseline (verified on branch `main`)

- Original main SHA: `06ec22c3f051f376a240139f89a459acea622435`
- Pre-work git state: clean working tree, branch `main`, origin in sync (`0 0`)
- PR #8 (`feat/v1.11-live-ablation-complete`) merge commit: the SHA above
- Verified product version on main: `1.11.0` in every manifest, `SKILL.md`,
  `CHANGELOG.md`, `scripts/validate-all`, and `scripts/package`.
- Evidence: the label "v1.11.1" appears only in commit/PR titles, never in a
  product manifest. Reconciliation decision: treat `v1.11.1` as a milestone
  label and advance the product version directly to `1.12.0`.

## Immutable control dataset

Directory: `evals/runs/hy4-flash-openrouter-2026-11-19/`
Do not modify, re-score in place, or overwrite these files. Future comparisons
must write to a NEW run directory and reference these SHA-256 values.

| SHA-256 | File |
|---|---|
| `29be5dd463119deb6e50950d65a73a0a0e46c3afa001750719c404c20b9f0193` | config.json |
| `e63868a74c34e11bbd2835a00f9c3697df0cb0093ef7abf7d9581ddcdebc06d7` | evidence.json |
| `3ec06031b40e3c7c11280d868273181b35332a24f7bcf0605f6846f222ad0751` | invalid-cases.json |
| `e4b2c0e6f840faf0158b3c0f4530cf1c24cb313d2a186c2e7a5053e650cff2ff` | isolation.json |
| `5bb8a7479342a464e8bf4ddff926fb3fb5251138216586dab127a0b2fd79bc3e` | judge-log.json |
| `c61929d90b488048181442e33bea568ed8d3ab37e28d3dc786f858d29ea356e6` | score-final.json |
| `580140129b6f81d09ddd9772de8bd0526d7872810c8b2b903ecc0ebed13f9f91` | SUMMARY.md |
| `8836404f79962571053f0b2cd6620340a03b2a7ed21860c838a6140e3a4ddfb6` | WITH.jsonl |
| `d028e573e4594ad26b825a8c394a29816babeb4078a56d8afe288c2cb8cd9997` | WITHOUT.jsonl |

## Historical control metrics (pinned `openrouter/tencent/hy4-flash`, OpenCode 1.19.6)

Source: `score-final.json` in the control dataset above. These numbers describe
one pinned configuration only and are not generalized.

| Metric | Result |
|---|---|
| Trigger F1 | 0.889 |
| Specialist precision / recall / F1 | 0.524 / 0.386 / 0.444 |
| Specialist exact-match | 0.167 (4/24) |
| Scenario pass rate | 6/19 (0.316) |
| Rubric criteria pass rate | 0.592 |

## Environment capability record (observed, not assumed)

- Host CLI used for this work: `opencode` NOT AVAILABLE in the development shell.
  Live model-dependent ablation and independent-judge runs therefore CANNOT be
  executed here; they are recorded as an external blocker, not fabricated.
- `gh` available and authenticated (scopes include `repo`, `workflow`).
- Python 3.14.10 and Node 24.22.3 available.
- RScan V1 adapter syntax checks are exercised in CI; native runtime is NOT
  re-verified in this environment.

## Integrity check

After all edits, verify with:
`sha256sum -c` against the table above (paths relative to the run directory),
or re-run the exact `find ... | sort | xargs sha256sum` command recorded in the
development transcript.
