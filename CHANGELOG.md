# Changelog

RCoder follows Semantic Versioning.

## [1.11.0] - 2026-11-19

### Added
- `scripts/run-benchmark.py`: a checkpointed, isolated with/without-RCoder ablation harness that derives predictions only from observable OpenCode JSON events and records provider usage.
- `evals/runs/hy4-flash-free-2026-11-19/`: retained configuration, per-case evidence summary, predictions, and scorer output for the first live partial run.
- `docs/INSTALLER-SECURITY-REVIEW.md`: independent installer security review.
- Validator assertions requiring substantive specialist section content and rejecting unfilled placeholders.

### Changed
- OpenCode RScan adapter V1 pushes a plain string into `experimental.chat.system.transform`, executes RScan through `node:child_process` with a timeout, and deduplicates by injected content rather than session ID. V2 uses the same safe execution path and per-context content guard.
- Benchmark runner interleaves arms and marks provider-quota failures invalid instead of scoring them.
- Synchronized version 1.11.0 across skill metadata, package/plugin manifests, changelog, package builder, and validator.

## [1.10.0] - 2026-11-19

### Added
- OpenCode RScan adapter generator (`rscan hooks adapter --host opencode --api v1|v2`) with version-specific V1/V2 templates and an explicit NOT VERIFIED gate.
- `docs/LIVE-BENCHMARK.md` defining the controlled with/without-RCoder evaluation protocol for Hy4 Flash Free on OpenCode.

### Changed
- Validator now enforces all 13 specialist headings, not only three.
- Environment, compatibility, research TODO, and handoff records reconciled with merged PRs #3-#5 and the observed OpenCode 1.19.6 package/binary status.
- Synchronized version 1.10.0 across skill metadata, package/plugin manifests, changelog, package builder, and validator.

## [1.9.0] - 2026-11-19

### Added
- RSaver `crosscheck`: verifies completion claims against diff/test artifacts, checks scope boundaries, copies provider usage without altering it, and emits a line-referenced failure evidence pack.
- RSaver `pack`/`unpack`: zlib-based exact-recovery compression accepted only when the estimated token count decreases, with SHA-256 verification.
- `rsaver-crosscheck.md` and `docs/BILLING-AND-CROSSCHECK.md` documenting the provider billing boundary explicitly.

### Changed
- Router invokes crosscheck after failed or claimed-complete work.
- Synchronized version 1.9.0 across skill metadata, package/plugin manifests, changelog, package builder, and validator.

## [1.8.0] - 2026-11-19

### Added
- RScan, a read-only bounded project scanner that reports stacks, quality entry points, risk signals, and a ranked menu of development options with first commands and specialist references.
- Host session-start adapters for Claude Code and Gemini CLI (`rscan hooks preview|install`) with idempotent merging, backups, and dry-run; unsupported hosts are documented rather than guessed.
- Installer optional tool selection for RSaver and RScan across the Node CLI, interactive managers, PowerShell bootstrap, and POSIX helper, recorded in a per-target feature manifest.
- `rscan.md` specialist and `docs/RSCAN-HOOKS.md` evidence table.

### Changed
- Router starts unfamiliar sessions with RScan before specialist selection.
- Synchronized version 1.8.0 across skill metadata, package/plugin manifests, changelog, package builder, and validator.

## [1.7.0] - 2026-11-19

### Added
- RSaver re-anchoring: `drift` scans a transcript for objective/constraint loss, repeated commands, and completion claims with open unknowns; `anchor` builds a dual-end block with explicit IDs and source-separated facts; `reanchor` inserts both blocks and re-runs the gate budget.
- `rsaver-anchor.md` specialist and `docs/CONTEXT-DRIFT.md` research basis covering positional attention bias, structural anchors, and compaction source discipline.
- RSaver self-test coverage for drift signals, dual-end structure, ID references, budget warnings, and rejection paths.

### Changed
- Router applies re-anchoring when drift signals appear in a long session.
- Synchronized version 1.7.0 across skill metadata, package/plugin manifests, changelog, package builder, and validator.

## [1.6.0] - 2026-11-19

### Added
- RSaver Gate: a pre-routing process filter with a `gate` subcommand for context envelopes and a `budget` subcommand for window allocation across input, cached prefix, output, and reasoning reserves.
- `rsaver-gate.md` documenting the prompt -> gate -> model -> skills/reasoning/search -> gate -> response pipeline and its runtime limits.
- `docs/TOKEN-ECONOMICS.md` documenting input, cached-input, output, and reasoning tokens, caching prefixes/TTL/minimums, usage fields, and break-even arithmetic with source links.

### Changed
- Router applies the gate before specialist selection and again at each model boundary for multi-step or context-constrained work.
- RSaver self-test now covers budget arithmetic, required/deferred decisions, cache eligibility and fragmentation, and invalid envelopes.
- Synchronized version 1.6.0 across skill metadata, package/plugin manifests, changelog, package builder, and validator.

## [1.5.0] - 2026-11-19

### Added
- RSaver estimator v2 with GPT-style pre-tokenization, content-class rates (prose, non-ASCII Latin, CJK, emoji, symbols, digits), model profiles, a `compare` subcommand, optional exact counting via `tiktoken` or an external tokenizer command, and no new required dependencies.
- Deep tokenization research section in the RSaver specialist with calibrated error figures from a public-tiktoken oracle.

### Changed
- Token figures in RSaver manifests now report v2 as primary and retain v1 for reproducibility.
- Synchronized version 1.5.0 across skill metadata, package/plugin manifests, changelog, package builder, and validator.

## [1.4.0] - 2026-11-19

### Added
- RSaver, a dependency-free context-reduction CLI: relative token measurement, bounded symbol selection, structure-preserving pruning, economics-checked duplicate collapsing, exact range recovery, and hash-verified manifests.
- RSaver specialist module with evidence-preserving methodology, explicit estimator limitations, and recovery/verification requirements.
- RSaver self-test integrated into local checks and CI.

### Changed
- Synchronized version 1.4.0 across skill metadata, package/plugin manifests, changelog, package builder, and validator.
- Router and README now document when to use RSaver and when not to (source code, billing, hard context limits).

## [1.3.0] - 2026-11-18

### Added
- Model-adaptation specialist with observable capability discovery, four adaptive execution profiles (Focused, Engineering, Deep Research, Long-Running Project), an empirical evaluation and ablation methodology, subagent strategy, and long-task continuity guidance.
- Host compatibility evidence matrix with five evidence tiers (T0-T4), recording file-install support separately from documented discovery, native discovery, invocation, and behavioral effectiveness.
- Environment and capability record for the Termux/OpenCode development shell, including observed runtimes, absent `opencode` CLI, and explicitly unknown capabilities.
- Router layer map (A-F) connecting discovery, selection, execution, tool adaptation, verification, and context management to existing artifacts.
- Full 13-section specialist authoring template covering mission, reconnaissance, decision trees, tool strategy, advanced techniques, failure modes, and output contracts.
- Executable evaluation harness: routing expectations for all 42 triggers, a deterministic scorer for trigger/specialist/scenario metrics and ablation deltas, its self-test, a documented ablation protocol, and five additional behavioral scenarios (s15-s19).
- Depth parity across all 54 specialist modules then available: every module now carries the full 13-section structure with domain-specific decision trees, tool strategy, failure modes, and verification contracts. Five modules (`rsaver`, `rsaver-gate`, `rsaver-anchor`, `rsaver-crosscheck`, `rscan`) were added in later releases, making the current total 59; the historical 54 figure is not the current count.

### Changed
- Normalized the evaluation contract: `evals/rubric.md` and `evals/results.md` now match the enforced 42-prompt, 24-positive, 18-negative, English-only, 14-scenario, four-criterion dataset; non-English activation is explicitly `NOT VERIFIED`.
- Verification terminology is aligned on VERIFIED / INFERRED / NOT VERIFIED across router, evaluation contract, and verification specialist.
- Validator now requires the model-adaptation reference and the compatibility/environment records.
- Synchronized version 1.3.0 across skill metadata, package/plugin manifests, changelog, and package builder.

## [1.2.0] - 2026-11-17

### Added
- Interactive global terminal launcher invoked by typing `RCoder`, with multi-target selection, Project/User scope, install/update, uninstall, backup restoration, and shared-root deduplication.
- Twenty Agentic AI and CLI integrations, including Cline, Roo Code, TRAE, Factory Droid, Qoder, OpenCode, Antigravity, Amp, Zed, Pi, OpenClaw, Autohand, Warp, and Kilo Code.
- Expanded programming specialists for language/runtime routing, systems programming, polyglot ecosystems, web platform, mobile, game/emulation, embedded, ML/AI, distributed systems, databases, build toolchains, and API protocols.
- Defensive cybersecurity specialists for threat modeling, secure code review, application/cloud/network security, cryptography, secrets, supply chain, vulnerability research, authorized penetration testing, incident response, malware analysis, and smart contracts.
- Reverse-engineering guidance for binary analysis, file formats, machine-state evidence, differential validation, and emulator/recompiler research.
- Token-efficiency reference, metadata-only repository context snapshot helper, and context-capsule template.
- Expanded evaluation corpus to 42 trigger prompts and 14 behavioral scenarios.

### Changed
- Preserved both official installation methods: PowerShell `irm` and Node.js/npm.
- Windows PowerShell installs a native `RCoder` launcher without requiring Node.js; the npm installer provisions the launcher on Node-enabled platforms.
- Target paths are recorded in `targets.json`; installers, tests, and documentation are synchronized to the catalog.
- Node package contents include the target catalog and PowerShell manager required by the global launcher.
- Installer tests cover all 20 target IDs across both scopes and verify launcher idempotence.
- Updated plugin manifests and package release metadata to 1.2.0.

## [1.1.0] - 2026-11-16

### Added
- One-command Node.js/npm installer available through the GitHub package spec.
- PowerShell bootstrap for direct `irm` installation.
- English-only repository documentation, prompts, templates, and installer messages.
- Node installer tests across six targets and both installation scopes.

### Changed
- Kept `npx` and `irm` as the two official one-command installation methods.
- Added English-only trigger validation and synchronized package metadata.

## [1.0.0] - 2026-11-16

### Added
- Portable `rcoder` Agent Skill with an evidence-led engineering workflow.
- Twelve required expert modules, a domain extension guide, and authoring templates.
- POSIX and PowerShell offline installers for six targets and both Project/User scopes.
- Claude Code and Agent Plugins manifests with Codex compatibility metadata.
- Trigger and behavioral evaluation suites, static validation, CI, and ZIP packages.
