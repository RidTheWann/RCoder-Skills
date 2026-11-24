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

## D-016 — Read-only, dependency-free MCP server
- Decision: expose RCoder's deterministic helpers, specialist lookup, and the routing-selection rules through a stdio MCP server that uses only the Python standard library and has no write tools.
- Criteria: no runtime dependency (matches the installers), safe by construction (root confinement, credential refusal, argument-vector subprocesses, timeouts, bounded output), cheap in context (a `minimal` profile and an allowlist), and testable without a model.
- Consequence: the server proves protocol behavior only. Host connection and model use are separate evidence gates.

## D-017 — No default hooks (superseded by D-019)
- Decision: do not ship an auto-firing `SessionStart` hook with the plugin. Automatic RScan stays opt-in through `rscan hooks install`.
- Rationale: an always-on hook changes behavior and token use for every session and runs a command with the user's permissions. `scripts/validate-all` rejects a `hooks/` directory so a change of this decision is deliberate.

## D-019 — Bundled read-only SessionStart hook
- Decision: the Claude Code plugin ships `hooks/hooks.json` with one `SessionStart` (matcher `startup`) hook that runs the bundled `rscan.py scan --hook claude`. Authorized explicitly by the repository owner on 2026-11-23, superseding D-017.
- Rationale: the scan is read-only, bounded (about 1.6 KB of context, 15 s timeout), and gives every session a ranked menu of next steps without a manual call.
- Limits: `scripts/validate-all` allows only this one event and command shape; blocking or tool-event hooks (`PreToolUse`, `PostToolUse`, `Stop`) and network or destructive programs stay forbidden. Cost: roughly 400 tokens per session start. Disable by disabling the plugin or via `/hooks`. Do not also run `rscan hooks install` for Claude Code, or the menu is injected twice.

## D-018 — Least-privilege subagents and unapproved commands
- Decision: plugin subagents are never granted file-editing tools, the security reviewer has no shell, and slash commands do not pre-approve tools. `scripts/validate-all` enforces this.

## D-020 — Extend an existing MCP tool instead of adding one
- Decision: module search is an optional `query` on `rcoder_list_specialists`, not a new tool, and it matches only name, title, and "Activate when" text.
- Rationale: every tool schema is sent on every request, so a new tool costs tokens in all sessions; matching only the activation text keeps incidental body words from producing misleading candidates. The result states that a query locates names and does not choose a primary, which preserves the rule to select by deliverable.
- Consequence: resources, tools, and prompts must apply project-local overrides identically; `scripts/test-mcp.py` asserts that parity.
- Note: this entry was previously numbered D-019 a second time; it was renumbered because D-019 is the bundled SessionStart hook decision that other files cite.

## D-021 — Opt-in guard and completion-gate hooks
- Decision: ship `skills/rcoder/scripts/rcoder_hooks.py`, a standard-library handler for a `PreToolUse` guard and a `Stop` completion gate, that the user enables explicitly with `rcoder_hooks.py install` or by pasting `print-config` output. The bundled `hooks/hooks.json` stays SessionStart-only, so D-019 and its validator rule are unchanged.
- Rationale: tool-event hooks can block work and run on every tool call, so they must be a deliberate user choice rather than a plugin default. Opt-in delivers the capability (refusing credential reads and staging, catastrophic commands, unreviewed force pushes and remote-script execution, and unevidenced completion claims) without changing any default session.
- Safety properties, enforced by `scripts/test-hooks.py`: no subprocess, network, or dynamic-code use; fail open on any malformed event or internal error; `stop_hook_active` always allows, so a block cannot loop; `install` merges idempotently, backs up first, and refuses symbolic links and non-strict JSON.
- Limits: a guard is a guardrail, not a sandbox. Interpreters, obfuscated names, and variables can still reach a credential file. Native host behavior is NOT VERIFIED; see `docs/HOOKS.md`.
