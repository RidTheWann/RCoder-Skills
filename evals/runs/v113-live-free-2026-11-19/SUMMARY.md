# Bounded live ablation — v1.11.0 control vs v1.13 treatment, 2026-11-19

This is a NEW run directory. The frozen historical control
`evals/runs/hy4-flash-openrouter-2026-11-19/` was not modified and is never
merged with these results.

## Experiment

| Field | Value |
|---|---|
| Model | `opencode/hy4-flash-free` (same Hy4 Flash family as the historical control, different provider path) |
| Host | OpenCode 1.19.6 through the verified Termux glibc loader, exit 0 on `--version` |
| Harness | `scripts/run-benchmark.py` with `--triggers-only --limit 24 --arm with --parallel 2 --timeout 90` |
| Control skill | v1.11.0 from git commit `06ec22c` (59 references, no `specialist-routing.md`), extracted with `git archive` into an isolated temporary repository |
| Treatment skill | This branch (60 references, staged routing contract and selection gate) |
| Fixtures | Harness-generated `fixture-with` only; identical README; skill present only in the treatment/control WITH arm. The generated fixture directories, including tool-created `node_modules`, were removed after the run to keep the evidence set small; their content hashes remain in each `isolation.json`. |
| Version label during the run | Both arms were executed before the 1.13.0 manifest bump. The treatment fixture carried the routing changes from this branch with the then-current `1.12.0` label; the control fixture carried the unmodified v1.11.0 skill. The version bump happened after live evidence was captured. |
| Dataset | Original `evals/triggers.json`, first 24 IDs; only IDs 01-18 produced comparable valid evidence |
| Invalid handling | Six IDs (trig-19 to trig-24) were invalid in the control arm and were excluded from BOTH arms via `shared-invalid.json` |
| Scoring | `scripts/score-eval.py --json` with the shared invalid map; `scripts/verify-objective.py` for deterministic artifact checks |
| Credentials | No credential was supplied or stored; no paid call was made; no provider or global configuration changed |

## Observed metrics (12 comparable positive triggers, same IDs in both arms)

| Metric | Control v1.11.0 | Treatment v1.13 | Delta |
|---|---|---|---|
| Trigger TP / FP / FN / TN | 11 / 0 / 1 / 6 | 9 / 0 / 3 / 6 | -2 TP |
| Trigger F1 | 0.957 | 0.857 | -0.100 |
| Specialist precision | 0.778 | 0.769 | -0.009 |
| Specialist recall | 0.241 | 0.345 | +0.103 |
| Specialist F1 | 0.368 | 0.476 | +0.107 |
| Specialist exact-match | 0.000 (0/12) | 0.083 (1/12) | +0.083 |
| Empty specialist sets (of 12 scored positives) | 7 | 5 | -2 |
| Recorded tokens on the 12 positives | 311,619 | 313,092 | +1,473 (+0.5%) |
| Tool calls on the 12 positives | 99 | 98 | -1 |
| Tool errors on the 12 positives | 15 | 11 | -4 |

The historical frozen control scored specialist F1 0.444 and exact-match 0.182 on a
different provider path and a full 24-positive set. Those numbers are NOT
comparable to this small free-tier run and are not repeated here as a baseline
for it.

## Interpretation

VERIFIED: the treatment emitted more correct specialist modules (higher recall
and F1), produced one exact-match where the control produced none, reduced empty
positive sets from 7 to 5, and did so with essentially unchanged recorded token
usage and tool-call count. These are deterministic computations over retained
per-case evidence in both arm directories.

VERIFIED: trigger F1 regressed in this sample (11 TP to 9 TP). No claim of an
overall trigger improvement is made.

INFERRED: the reduction in empty sets is consistent with the selection gate and
base-plus-narrow rules, but this sample cannot establish causation.

NOT VERIFIED: statistical significance, full 42-trigger or 19-scenario coverage,
expanded-dataset live behavior, multilingual activation, independent-judge or
human adjudication, and generalization beyond this free-tier configuration.
Two treatment cases (trig-05, trig-12) and several control cases ended in a
harness timeout but still produced agent text; they were scored as valid under
the existing harness rule and the timeouts are retained in the raw artifacts.

A follow-up probe after these runs timed out, indicating the free-tier quota was
exhausted. No paid provider was used as a substitute.

## Evidence

- `control-original/raw/`, `treatment-original/raw/`: retained per-case JSONL, stderr, and metadata.
- `control-original/isolation.json`, `treatment-original/isolation.json`: fixture hashes.
- `control-original/config.json`, `treatment-original/config.json`: pinned settings.
- `control-original/evidence.json`, `treatment-original/evidence.json`: observed tool/skill/specialist events and token fields.
- `shared-invalid.json`: IDs excluded from both arms.
- `comparison.json`: machine-readable metric comparison.
