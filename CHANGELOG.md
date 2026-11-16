# Changelog

RCoder follows Semantic Versioning.

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
