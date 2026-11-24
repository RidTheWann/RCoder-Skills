# RCoder project handoff — v1.14.0

## Delivered

RCoder remains one portable Agent Skill with progressive disclosure. The core router selects focused references rather than injecting the entire specialist library into every agent context.

Version 1.14.0 adds:
- A read-only, dependency-free stdio MCP server (`skills/rcoder/scripts/rcoder_mcp.py`) with 21 tools, resources, and workflow prompts; Claude Code plugin slash commands and least-privilege subagents; the `agent-extensions-engineering` specialist; and validator group G8. Details: `CHANGELOG.md` and `docs/MCP.md`.
- A deterministic specialist-routing assistant (`skills/rcoder/scripts/route_predict.py`, MCP tool `rcoder_route_predict`) that proposes a narrow, evidenced candidate set from documented signals plus cross-domain base/narrow composition, with ordinal confidence and scope rejection; reference module `skills/rcoder/references/deterministic-routing.md`; held-out scoring and negative rejection measured by `scripts/test-route-predict.py`. Results are labels from frozen evaluation data, not live host activation.
- A weak-model execution profile (`skills/rcoder/references/weak-model-profile.md`) and a compact repository structural map (`skills/rcoder/scripts/repo_map.py`, MCP tool `rcoder_repo_map`, reference `skills/rcoder/references/repo-map.md`). The profile enforces contract-first bounded exploration, edit-by-call-12, anti-loop thresholds, and an autonomy-ceiling operating contract; the map surfaces PageRank-ranked entry points without source bodies. Design cites published 2025-2026 harness research (planning, repo map, self-refine, operating contracts) as labeled literature evidence, not measurements of this helper.
- Pending in `CHANGELOG.md` under `[Unreleased]` (not yet released): a fix so MCP resources honor project-local overrides, a `query` filter on `rcoder_list_specialists`, `completion/complete`, `rcoder_route` / `rcoder_verify` prompts, the RSaver zero-token duplicate elimination (`dedupe --blocks`, `dedupe --words`, `pack --method dict`), `compact --target-savings`, the seven new RSaver MCP tools, the `saver` slash command and `rcoder-saver` subagent, and a marker-collision fix that restores byte-exact `unpack`. Locally verified only; hosted CI for it is not recorded.

Version 1.13.0 adds:
- An operational selection gate and stronger base-plus-narrow composition in `specialist-routing.md` and SKILL.md, derived from case-level control errors and checked in a fresh, bounded live ablation against the unmodified v1.11.0 skill.
- Three new deterministic routing-semantic checks and `--strict` in `verify-objective.py`; version detection, bounded capture, process-group cleanup, and CLI exit codes in `tool_probe.py`.
- Separate dataset paths and pinned config provenance in the benchmark harness, plus package-checksum verification and CI registration checks.
- Honest reconciliation of the earlier "opencode unavailable" statement: it described an earlier development shell. OpenCode 1.19.6 is executable through the verified glibc loader in the 2026-11-19 session, and the authorized free tier was used for the live ablation. No paid call, credential, or provider change was made.
- Full evidence and classification in `docs/V1.13-DELIVERY.md` and `docs/V1.13-DEV-LEDGER.md`.

Version 1.12.0 adds:
- Evidence-driven routing architecture (`specialist-routing.md`): staged selection, a selection record, primary/supporting/verifier roles, cross-domain base-plus-narrow composition, disambiguation of overlapping specialists, and anti-over-selection rules. Derived from case-level analysis of the v1.11 control run (specialist F1 0.444, exact-match 0.167, 10/24 positive prompts with an empty specialist set).
- Independent evaluation layers: `verify-objective.py` produces deterministic artifact checks with no model judge; `score-eval.py` adds per-specialist confusion, FP/FN rates, negative rejection, cross-domain and ambiguous subsets, objective-check scoring, invalid-case exclusion, and F1 from raw counts. `score-scenarios.py` now blinds arm labels, preserves originals, retains full judge responses, and accepts a separate authorized judge model.
- Additive expanded English-only dataset (18 triggers, 4 scenarios) under `evals/datasets/expanded/`, plus a separately documented multilingual activation policy and dataset. The frozen canonical 42-trigger dataset and its control hashes are unchanged and enforced by `scripts/validate-all`.
- Version reconciliation: `v1.11.1` was a commit/PR label only; the product version on main was 1.11.0. All metadata now consistently reports 1.12.0 (evidence: `evals/runs/BASELINE-LEDGER.md`).

Version 1.11.0 adds:
- A checkpointed, isolated with/without-RCoder benchmark harness and the retained first live partial run (WITH arm only; provider quota blocked the baseline).
- Verified native OpenCode 1.19.6 skill discovery and invocation, plus a corrected RScan V1 adapter validated against the installed plugin API.
- Specialist content assertions in the validator, an installer security review, and documentation reconciled with observed 2026-11-19 evidence.

Version 1.10.0 adds:
- Version-specific OpenCode RScan adapter generator, a written live-benchmark protocol, and a validator that locks all 13 specialist headings.

Version 1.9.0 added:
- RSaver crosscheck for failed or claimed-complete work, with artifact evidence and a documented billing boundary, plus exact-recovery compression accepted only when it saves tokens.

Version 1.8.0 added:
- RScan bounded project scanner with ranked development options, risk signals, and host-specific session-start hook installation for Claude Code and Gemini CLI.
- Installer choice for RSaver and RScan (both/one/neither) in the Node CLI, interactive managers, PowerShell bootstrap, and POSIX helper, saved as a per-target feature manifest.

Version 1.7.0 added:
- RSaver re-anchoring for long contexts: drift signals, dual-end objective/constraint restatement with explicit IDs, source-separated facts, and budget-aware reanchoring.
- Research basis on positional attention bias, structural anchors, and unsupported compaction entries.

Version 1.6.0 added:
- RSaver Gate: a per-step context filter with input/cache/output/reasoning budgeting, required-item protection, deferred recovery pointers, and cache-prefix checks.
- Token economics documentation covering input, cached-input, output, and reasoning tokens with provider usage fields and caching break-even rules.

Version 1.5.0 added:
- RSaver estimator v2 with pre-tokenization-aware content classes, model profiles, a comparison command, and optional exact counts from `tiktoken` or an external tokenizer command.
- A documented tokenization research basis and calibrated error figures from public encoding files.

Version 1.4.0 added:
- RSaver, a dependency-free CLI that measures relative context cost, extracts bounded symbol windows, prunes verbose output without rewriting retained evidence, collapses duplicates only when it saves tokens, and records hash-checked manifests for exact recovery and verification.
- An RSaver specialist module and router entry defining when reduction is safe and when a real tokenizer is required.

Version 1.3.0 added:
- A model-adaptation specialist: observable capability discovery, four adaptive execution profiles, empirical ablation/evaluation methodology, subagent strategy, and long-task continuity.
- A five-tier host compatibility evidence matrix separating file installation from documented discovery, native discovery, invocation, and behavioral evaluation.
- An environment and capability record for the Termux/OpenCode development shell, with observed runtimes and explicitly unknown capabilities.
- A compact router layer map (A-F) and an English-only 13-section specialist authoring template.
- A normalized evaluation contract; `rubric.md` and `results.md` now match the enforced dataset and label non-English activation and model performance claims `NOT VERIFIED`.
- Depth parity across the 54 specialist modules available in v1.3.0 (full 13-section structure) without removing any module. Five modules were added later (`rsaver`, `rsaver-gate`, `rsaver-anchor`, `rsaver-crosscheck`, `rscan`), bringing v1.11 to 59. v1.12 adds `specialist-routing` for the demonstrated routing-coverage gap, so the verified count is 60; `scripts/validate-all` enforces the 13-section structure on all 60.
- An executable evaluation harness: routing expectations, a deterministic scorer with ablation deltas, its self-test, an ablation protocol, and five additional scenarios (s15-s19) for capability discovery, tool adaptation, context handoff, finding classification, and evidence-led reverse engineering.

Version 1.2.0 added:
- A global terminal manager invoked by typing `RCoder`.
- Twenty Agentic AI/CLI integrations with Project/User scopes, multi-selection, shared-root deduplication, update, uninstall, backup, and restore.
- A Windows-native PowerShell launcher installed through the existing `irm` bootstrap; this route does not require Node.js.
- A Node/npm installer that provisions a global launcher on Node-enabled platforms.
- Expanded programming-language, systems, platform, cybersecurity, reverse-engineering, and smart-contract specialists.
- A metadata-only bounded repository snapshot helper and context-capsule template.
- 42 trigger prompts and 14 behavioral evaluation scenarios.

Repository: https://github.com/RidTheWann/RCoder-Skills
Historical baseline (as recorded on 2026-11-19): `main` at `6472c7090e580317b9b26142422455aba5092c7c` (v1.10.0, PR [#6](https://github.com/RidTheWann/RCoder-Skills/pull/6)). PR [#7](https://github.com/RidTheWann/RCoder-Skills/pull/7) merged as `3f1cfc1c46cff2be56c921a09566f0247c8a7a3c`. PR [#9](https://github.com/RidTheWann/RCoder-Skills/pull/9) delivered v1.12.0 and PR [#10](https://github.com/RidTheWann/RCoder-Skills/pull/10) its delivery record.
Verified v1.13 baseline: `main` at `b34aaa0c050be9893d2e97301483af9352ad14df`.
v1.14.0 is described in `CHANGELOG.md`; this file does not record its hosted-CI run. The v1.13.0 release record: v1.13.0, delivered through PR [#11](https://github.com/RidTheWann/RCoder-Skills/pull/11) (MERGED 2026-11-19T12:44:04Z) as main commit `218f7b57f22cdce3394f32b9f58185bc6c12b034`. Linux and Windows matrix [44526085390](https://github.com/RidTheWann/RCoder-Skills/actions/runs/44526085390) PASS. Full provenance is in `docs/V1.13-DELIVERY.md`. The frozen historical control remains `evals/runs/hy4-flash-openrouter-2026-11-19/` (61 cases × 2 arms, strict scorer exit 0).

## Installation

### Windows PowerShell

```powershell
irm https://raw.githubusercontent.com/RidTheWann/RCoder-Skills/main/install.ps1 | iex
```

Supports Windows PowerShell 5.1 and PowerShell 7+. It downloads the repository archive over HTTPS, installs the selected skill, registers `%USERPROFILE%\.rcoder\bin` in the user PATH, and creates `RCoder.cmd`. Node.js is not required for this Windows `irm` route.

### Node.js/npm

```sh
npx -y github:RidTheWann/RCoder-Skills
```

Requires Node.js 18.18+, npm, and Git. It installs the selected skill and provisions `RCoder` under `~/.local/bin` on POSIX or `%USERPROFILE%\.rcoder\bin` on Windows.

After installation, open a new terminal and type `RCoder`.

## Terminal manager

1. Install / Update.
2. Uninstall / restore the latest backup.
3. Show supported agents.
0. Exit.

Choose one or more target indices (comma-separated or `A` for all), then Project or User scope. Shared discovery roots are deduplicated.

## Target catalog

The catalog covers Claude Code, Codex CLI, Cursor, Gemini CLI, GitHub Copilot, generic Agent Skills, Qoder, OpenCode, Antigravity, Amp, Zed, Pi, OpenClaw, Autohand, Warp, Kilo Code, Cline, Roo Code, TRAE, and Factory Droid.

`targets.json` is the canonical label/path matrix. Node CLI and PowerShell terminal manager read the catalog; the PowerShell bootstrap downloads it before resolving the selected target. Offline shell/PowerShell adapters and CI tests validate their path maps.

## Specialist coverage

Programming references cover language/runtime routing, C/C++/Rust, Python, JavaScript/TypeScript, .NET/JVM, Go, polyglot ecosystems, frontend/browser, backend, databases, API protocols, mobile, game/emulation, embedded, ML/AI, distributed systems, functional programming, build systems, and debugging/testing.

Cybersecurity references cover threat modeling, secure review, application/cloud/container/network security, identity/cryptography/secrets, supply chain, vulnerability research, authorized penetration testing, incident response/forensics, defensive malware triage, binary hardening, and smart contracts.

Reverse-engineering references cover executable/binary analysis, evidence-led semantic reconstruction, undocumented file formats, and compatibility/emulator/recompiler research.

## Token-efficiency strategy

- Progressive disclosure: do not load the entire reference library by default.
- Bounded reconnaissance: the context snapshot prints repository metadata and paths only.
- Exact reads: symbol searches, line ranges, and focused diffs.
- Context capsule: preserve decisions, evidence, changed files, verification, and next actions.
- Deduplicated tool calls and non-overlapping subagent scopes.
- No reduction in authorization, security, test, or data-integrity checks to save tokens.

## Local verification for v1.11.0

Run in the Termux development shell on `feat/v1.11-blocker-elimination`:

- `python3 scripts/validate-all` — PASS; check count increases with the new specialist-content assertions.
- `python3 scripts/test-context-snapshot.py` — PASS, including the new bounded-path assertion.
- `python3 scripts/test-score-eval.py` — PASS, scorer verified on synthetic perfect, mixed, inverted, and four rejection paths.
- `python3 scripts/test-rsaver.py` — PASS, reduction, verbatim evidence, recovery, verification, dedupe economics, estimator profiles, and external tokenizer hook.
- `python3 scripts/score-eval.py --predictions <synthetic-fixture> --strict` — PASS on a generated fixture: 24 TP / 18 TN, specialist F1 1.0, 19/19 scenarios (synthetic only, not a model result).
- `node --check scripts/rcoder.mjs` — PASS (exit 0).
- `node scripts/test-node-installer.mjs` — PASS, all 40 target/scope combinations plus backup restore and launcher checks.
- `bash scripts/test-installers.sh` — PASS, all 40 POSIX target/scope combinations.
- `npm pack --dry-run --json` — PASS; see the actual command output for the pinned version and entry count.
- `python3 scripts/package` — PASS; five ZIPs created and `sha256sum -c dist/SHA256SUMS` verified all OK.

**Current release CI:** v1.10.0 merged with a green hosted matrix on `main` — run [44491687529](https://github.com/RidTheWann/RCoder-Skills/actions/runs/44491687529) succeeded on both Linux and Windows for the exact baseline commit `6472c7090e580317b9b26142422455aba5092c7c`. The v1.11.0 feature-branch run is recorded in the PR when created; do not claim it passed before observing it.

## Historical CI evidence (v1.2.0)

**CI status: PASS.** The pre-merge PR matrix passed, and post-merge GitHub Actions run [43940645566](https://github.com/RidTheWann/RCoder-Skills/actions/runs/43940645566) completed successfully on both Linux and Windows for the exact `main` merge commit `7f7c88f2fce5b8b2754d9cc10c65cca69a23f5ed`.

The run verified 644 static checks, context-snapshot regression, Node syntax, 40 Node target/scope cases per OS, launcher and interactive-menu behavior, npm package dry-run, 40 POSIX target/scope cases, 40 Windows PowerShell target/scope cases on both PowerShell 5.1 and 7, and reproducible skill/plugin/source package builds.

Do not claim native model activation in all hosts from path simulations alone. Native discovery and live model triggering remain separate verification gates.

## Safety and maintenance

1. Keep all repository-maintained text in English.
2. Require explicit authorization and written scope for active security testing.
3. Preserve sample provenance and hashes during reverse engineering and forensics.
4. Do not guess undocumented ABI or machine-state semantics.
5. Keep `targets.json`, Node/PowerShell/POSIX adapters, tests, and docs synchronized.
6. Keep package/plugin/skill/changelog versions synchronized.
