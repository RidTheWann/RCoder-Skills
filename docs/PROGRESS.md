# RCoder build progress — 2026-11-19

## Release objective

Build v1.12.0 as a safe extension of the verified v1.11.0 product baseline (`06ec22c3f051f376a240139f89a459acea622435`, PR #8). Preserve both installers, the Agent Skill format, plugin manifests, the canonical skill directory, the frozen evaluation control, and all existing specialist capabilities while improving routing intelligence, evaluation independence, and deterministic verification.

## v1.12.0 execution status

- [x] Baseline audit: main SHA, clean tree, origin sync, version inconsistency, 59 specialists, control dataset hashes (`evals/runs/BASELINE-LEDGER.md`).
- [x] Case-level routing diagnosis from the pinned control: 10/24 positive prompts with empty specialist sets, `security` FN=5, `systems-programming` FN=3, `verification` FP=3, wrong-neighbour substitutions.
- [x] Implemented staged routing architecture and selection contract in `specialist-routing.md` and `SKILL.md`.
- [x] Implemented deterministic objective verifier and expanded scorer with regression tests.
- [x] Hardened scenario judging: arm blinding, non-destructive output, separate judge model, full response retention.
- [x] Expanded dataset additively; preserved frozen control and documented multilingual policy.
- [x] Extended `validate-all` with semantic specialist checks, dataset validation, and control-hash integrity enforcement (2936 checks pass locally).
- [ ] Live model-dependent ablation after routing changes: BLOCKED (no `opencode` CLI and no authorized paid run in this environment).
- [ ] Independent judge model / human adjudication run: BLOCKED (no separate authorized model available).

## v1.11.0 execution status

- [x] Re-probed the environment: OpenCode CLI 1.19.6 runs via glibc loader; `gh` and PowerShell 7 are available.
- [x] Built the isolated, checkpointed benchmark harness in `scripts/run-benchmark.py`.
- [x] Executed a genuine partial live run: 30 valid WITH-arm trigger cases; provider quota blocked the baseline and all scenarios.
- [x] Verified native OpenCode skill discovery and invocation; corrected the RScan V1/V2 adapters against the installed API.
- [x] Added specialist-content validator assertions and an installer security review.
- [ ] Complete the with/without ablation when provider quota or an authorized provider is available.

## Implementation checklist

- [x] Audit the repository and preserve PowerShell `irm` and Node/npm installation methods.
- [x] Normalize the evaluation contract across `evals/rubric.md`, `evals/results.md`, and `scripts/validate-all`.
- [x] Add model-adaptation capability discovery, adaptive execution profiles, and evaluation methodology.
- [x] Add a host compatibility evidence matrix and an environment/capability record.
- [x] Deepen all 54 specialists to the full 13-section structure without removing existing modules.
- [x] Add an executable evaluation scorer, routing expectations, self-test, ablation protocol, and five behavioral scenarios (19 total).
- [x] Re-run the full local gate set and installer/packaging regressions for v1.10.0: validator (1376 checks, including all 13 headings per specialist), context snapshot test, evaluation scorer test, RSaver drift/anchor/gate/crosscheck/pack test, RScan scan/hook/adapter test, Node syntax, 40 Node target/scope cases each for Node, POSIX, and PowerShell with optional-tool selection, npm pack dry-run, and five reproducible ZIP packages with verified checksums.
- [x] Add RSaver with hash-checked manifests, dedupe economics, and a deterministic self-test.
- [x] Research tokenization and calibrate a content-class estimator v2 with model profiles and optional exact counting.
- [x] Add RSaver Gate with input/cache/output/reasoning budgeting, priority filtering, and cache-prefix checks.
- [x] Add RSaver drift detection, dual-end anchor blocks with explicit IDs, and budget-aware reanchoring.
- [x] Add RScan bounded scanner, development-option menu, and evidenced session-start hook installers.
- [x] Add RSaver crosscheck and economy-checked exact-recovery compression with a documented billing boundary.
- [x] Add the live benchmark protocol, OpenCode V1/V2 adapter generator, and 13-heading specialist enforcement.
- [x] Add a global terminal manager invoked by typing `RCoder`.
- [x] Add multi-target and Project/User selection, shared-root deduplication, install/update, uninstall, backup, and restore.
- [x] Add a Windows-native PowerShell launcher independent of Node.js.
- [x] Add a Node/npm global launcher and include its runtime files in package metadata.
- [x] Expand the target catalog to twenty hosts.
- [x] Add programming, cybersecurity, reverse-engineering, and smart-contract specialists.
- [x] Add a read-only metadata-only context snapshot helper and context-capsule template.
- [x] Expand trigger evaluations to 42 prompts and behavioral scenarios to 14.
- [x] Run the Linux and Windows GitHub Actions matrix on the feature branch.
- [x] Inspect CI logs and fix the validator, Node test, POSIX test, and PowerShell launcher issues found during CI.
- [x] Merge PR #1 after all required checks passed; verify the resulting `main` commit with a post-merge CI run.

## Verification design

| Area | Required checks |
|---|---|
| Static structure | Skill frontmatter, specialist headings/line limits, links, manifests, versions, target registry, and selected security checks |
| Context helper | Metadata-only output, bounded paths/depth, dependency/build exclusions, and symlink handling |
| Node CLI | Syntax, help/list, 40 target/scope cases, dry-run, backup/restore, idempotence, launcher and interactive menu |
| POSIX adapter | 40 target/scope cases, dry-run, backup/restore, repeated install |
| PowerShell | Parse bootstrap and manager; 40 target/scope cases on Windows PowerShell 5.1 and PowerShell 7 |
| Packaging | `npm pack --dry-run --json`, reproducible ZIP packages, and checksums |
| Live activation | Separate native verification in each host; not inferred from file-copy tests |

## Verified CI evidence

- Workflow run: [43937693813](https://github.com/RidTheWann/RCoder-Skills/actions/runs/43937693813) — **PASS** on both `ubuntu-latest` and `windows-latest` for commit `a19eed4f466d2231779a2c230a364ff773ad4554`.
- Static validator: 644 checks passed.
- Context snapshot regression and Node syntax check passed on both platforms.
- Node installer/launcher matrix: 20 hosts × 2 scopes passed on Linux and Windows, including launcher setup, idempotence, shared-root restore, legacy backup restore, and interactive-menu smoke test.
- npm package dry-run passed on both platforms.
- POSIX adapter: 20 hosts × 2 scopes passed on Linux.
- Windows PowerShell 5.1 and PowerShell 7: parser checks and 20 hosts × 2 scopes passed.
- Reproducible skill/plugin/source package build passed on Linux and Windows.

## Verified merge and CI evidence

- PR [#1](https://github.com/RidTheWann/RCoder-Skills/pull/1) was squash-merged on 2026-11-17 UTC as `7f7c88f2fce5b8b2754d9cc10c65cca69a23f5ed`.
- Post-merge workflow [43940645566](https://github.com/RidTheWann/RCoder-Skills/actions/runs/43940645566) — **PASS** on both `ubuntu-latest` and `windows-latest` for the exact `main` merge commit.
- The post-merge run revalidated static checks, context snapshot, Node/launcher matrix, npm package, POSIX matrix, Windows PowerShell 5.1 and 7 matrices, and reproducible package build.

## Evidence boundary

CI validates static structure, packaging, and simulated file-system behavior. It does not prove that a host model autonomously selects RCoder; native discovery, live activation, and with/without-skill model evaluation remain separate verification tasks.
