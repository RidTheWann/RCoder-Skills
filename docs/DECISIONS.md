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

## D-006 — English skill internals, bilingual user docs
- Context: token efficiency and Indonesian/English usage.
- Decision: English skill/modules; README and handoff bilingual; agent mirrors user language.
- Confidence: medium; pragmatic maintenance choice.
- Change: revisit if evals show a better language strategy.

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
