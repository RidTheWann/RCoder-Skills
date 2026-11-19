# Changelog

RCoder follows Semantic Versioning.

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
- Depth parity across all 54 specialist modules: every module now carries the full 13-section structure with domain-specific decision trees, tool strategy, failure modes, and verification contracts.

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
