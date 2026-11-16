# RCoder decisions

## D-001 — One router, on-demand experts
- Decision: use one `rcoder` Agent Skill with focused references rather than injecting a large monolithic prompt.
- Criteria: portability, context efficiency, composability, and maintenance.
- Change: split/recombine only when trigger/evaluation evidence justifies it.

## D-002 — Minimal portable frontmatter
- Decision: keep core frontmatter to standard `name`, `description`, `license`, and string metadata; vendor extensions belong in adapter manifests.
- Reason: preserve Agent Skills portability and reduce host-specific parsing assumptions.

## D-003 — Native target paths
- Decision: install into documented native skill roots per host, or a generic `.agents/skills` interoperability root where appropriate.
- Change: update `targets.json`, installers, tests, docs, and CI together whenever a host path changes.

## D-004 — Offline, reversible lower-level installers
- Decision: retain POSIX and PowerShell helper installers for development and cross-platform tests; support dry-run, idempotence, backup, and restore.

## D-005 — Static checks do not impersonate runtime checks
- Decision: use a standard-library validator and explicitly label native product discovery/model activation as separate verification gates.

## D-006 — English-only repository content
- Decision: all repository-managed instructions, docs, prompts, templates, and installer messages are English-only. Never mix languages within a repository artifact.

## D-007 — No third-party installer runtime dependencies
- Decision: use Node built-ins, PowerShell, POSIX utilities, and Python standard library; add dependencies only with an explicit justification.

## D-008 — Pin CI actions to full commit SHAs
- Decision: keep GitHub Actions pinned to verified immutable commit SHAs. Update only after verifying upstream provenance.

## D-009 — Portable Agent Plugins manifest plus Codex fallback
- Decision: ship root `plugin.json` for portable Agent Plugins packaging and retain `.codex-plugin/plugin.json` as a compatibility fallback.

## D-010 — Preserve both official installation methods
- Decision: keep Windows PowerShell `irm` and Node.js/npm as first-class installation methods. Neither replaces the other.

## D-011 — Global launcher command is exactly RCoder
- Decision: install a global `RCoder` command. Windows `irm` provisions a `RCoder.cmd` shim invoking the bundled PowerShell manager; the Node installer provisions a POSIX wrapper or Windows shim.
- Criteria: no Node dependency for the Windows `irm` route, no third-party runtime, idempotent update, and clear PATH guidance.

## D-012 — Registry-driven host selection
- Decision: maintain stable host IDs, labels, and Project/User roots in `targets.json`; offer multi-select and deduplicate roots shared by multiple hosts.

## D-013 — Progressive disclosure and bounded context snapshots
- Decision: load specialists on demand; provide a bounded helper reporting paths and Git state without reading source contents; use a context capsule on long tasks.

## D-014 — Defensive cybersecurity and authorized reverse engineering
- Decision: require explicit authorization, written test scope, provenance, sample hashing, isolated analysis, and non-destructive proof in specialist workflows.

## D-015 — Evidence-led machine semantics
- Decision: undocumented ABI, instruction, register, memory, and file-format behavior remains unknown until corroborated by specifications, independent observations, or differential tests.
