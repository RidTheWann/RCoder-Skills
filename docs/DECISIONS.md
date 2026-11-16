# RCoder decisions

## D-001 — One router, on-demand experts
- Context: broad engineering coverage with low activation cost.
- Options: monolithic instructions; many standalone skills; one router with modules.
- Criteria: portability, context efficiency, maintenance, composability.
- Decision: one `rcoder` skill links focused `references/`.
- Confidence: high.
- Change: split only after trigger measurements prove better routing.

## D-002 — Minimal portable frontmatter
- Context: vendor frontmatter support varies.
- Options: vendor keys in core; minimal standard plus adapters.
- Decision: core uses `name`, `description`, `license`, and string metadata; omit experimental `allowed-tools`.
- Confidence: high, grounded in Agent Skills spec.
- Change: vendor keys only in adapter files after official/runtime verification.

## D-003 — Native target paths
- Context: products use distinct discovery directories.
- Options: single alias for all; product-native paths; marketplace only.
- Decision: `.claude/skills`, `.agents/skills`, `.cursor/skills`, `.gemini/skills`, `.github/skills`; Copilot user path `~/.copilot/skills`; generic alias `.agents/skills`.
- Confidence: high for documented paths; live discovery unverified.
- Change: update both installers, tests, README and installation matrix together.

## D-004 — Offline and reversible installers
- Context: no network, telemetry, or silent overwrite.
- Decision: POSIX/PowerShell native copy; idempotent; dry-run; backup existing content; uninstall restores newest backup.
- Confidence: high for POSIX after simulation; medium for PowerShell pending Windows execution.
- Change: keep both scripts and target/scope tests synchronized.

## D-005 — Static checks do not impersonate runtime checks
- Context: `skills-ref` and target CLIs absent.
- Decision: standard-library validator plus explicit `NOT VERIFIED` live gates.
- Confidence: high for static constraints only.
- Change: add official validator/runtime results when the products are available.

## D-006 — English-only repository content
- Context: mixed-language source documentation and evaluation prompts reduce consistency and make maintenance harder.
- Options: bilingual documentation; language-dependent source artifacts; one English-only repository standard.
- Decision: all repository-managed instructions, documentation, prompts, templates, comments, and installer messages are English-only.
- Confidence: high; explicit project requirement.
- Change: add a separately maintained translation only when explicitly required; never mix languages in a single artifact.

## D-007 — No installer/package runtime dependencies
- Context: offline portability.
- Decision: POSIX/PowerShell platform utilities and Python standard library for development tooling.
- Confidence: high for Linux POSIX; PowerShell pending native execution.
- Change: any new dependency needs explicit justification and docs.

## D-008 — Pin CI actions to full commit SHAs
- Context: the repository's own CI is a software supply-chain input.
- Options: mutable major tags; full commit SHA; maintain a third-party action lockfile.
- Decision: pin official checkout and setup-python releases to their verified full Git commit SHAs.
- Criteria: immutable references, official upstream provenance, low maintenance overhead.
- Confidence: high; refs read directly from the official GitHub repositories on 2026-11-16.
- Change: update both SHAs only after verifying the release tag resolves in the official upstream repository.

## D-009 — Portable Agent Plugins manifest plus Codex fallback
- Context: current OpenAI/Codex plugin docs prefer root `plugin.json`; `.codex-plugin/plugin.json` remains supported as a compatibility fallback.
- Options: keep legacy-only manifest; replace it with root-only; ship root manifest plus fallback.
- Decision: ship root portable `plugin.json` with Agent Plugins schema and OpenAI interface/onboarding metadata, while retaining `.codex-plugin/plugin.json` for older Codex compatibility.
- Confidence: high; verified against current OpenAI official plugin packaging and submission docs on 2026-11-16.
- Change: keep root and compatibility manifest names/version/skill paths synchronized; update the package builder and validator together.

## D-010 — One-command Node.js and PowerShell entry points
- Context: the previous install instructions exposed low-level shell flags and multiple platform-specific steps before the skill could be used.
- Options: keep platform-specific installers as the primary interface; publish to the npm registry; provide a Node.js GitHub-package CLI and a PowerShell `irm` bootstrap.
- Decision: make `npx -y github:RidTheWann/RCoder-Skills` and the root `install.ps1` bootstrap the primary entry points. Retain offline POSIX and PowerShell helpers for development and compatibility tests.
- Confidence: high; npm documents GitHub package specs and `npx` binary execution, and Microsoft documents `irm` as the `Invoke-RestMethod` alias.
- Change: update `package.json`, the root bootstrap, README, and cross-platform tests together whenever install behavior changes.
