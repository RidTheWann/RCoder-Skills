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

## D-011 — Global launcher command is exactly rcoder
- Decision: install a global `rcoder` command. Windows `irm` provisions a `rcoder.cmd` shim invoking the bundled PowerShell manager; the Node installer provisions a POSIX wrapper or Windows shim.
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

## D-019 — Bundled local Claude lifecycle hooks
- Decision: the Claude Code plugin's `hooks/hooks.json` includes a read-only `SessionStart` RScan, a credential/destructive-command `PreToolUse` guard, a token-shaped-secret `PostToolUse` warning, a `PreCompact` context reminder, and the opt-in RFC Context Fabric `UserPromptSubmit` / `Stop` / `SessionEnd` adapters. This revision was explicitly requested by the repository owner on 2026-11-26 and supersedes the SessionStart-only limit below. The transcript-based `Stop` completion gate remains a separate CLI opt-in.
- Rationale: use the same local policy logic as OpenCode at tool boundaries and preserve task state at compaction without network access or subprocesses.
- Limits: hooks execute with the user's permissions whenever the plugin is active. The guard is lexical, not a sandbox. The default hook configuration does not enable the transcript-based `Stop` completion gate. Disable the plugin or its hooks to stop automatic behavior. Native host activation remains NOT VERIFIED.

## D-018 — Least-privilege subagents and unapproved commands
- Decision: plugin subagents are never granted file-editing tools, the security reviewer has no shell, and slash commands do not pre-approve tools. `scripts/validate-all` enforces this.

## D-020 — Extend an existing MCP tool instead of adding one
- Decision: module search is an optional `query` on `rcoder_list_specialists`, not a new tool, and it matches only name, title, and "Activate when" text.
- Rationale: every tool schema is sent on every request, so a new tool costs tokens in all sessions; matching only the activation text keeps incidental body words from producing misleading candidates. The result states that a query locates names and does not choose a primary, which preserves the rule to select by deliverable.
- Consequence: resources, tools, and prompts must apply project-local overrides identically; `scripts/test-mcp.py` asserts that parity.
- Note: this entry was previously numbered D-019 a second time; it was renumbered because D-019 is the bundled SessionStart hook decision that other files cite.

## D-021 — Explicit stop gate and Gemini settings merge
- Decision: keep the transcript-based `Stop` completion gate opt-in through `rcoder_hooks.py install`. The same handler can explicitly merge the shared guard and post-tool warning into Gemini CLI's `.gemini/settings.json` using Gemini's `BeforeTool` and `AfterTool` event schema.
- Rationale: a completion gate depends on transcript semantics, and Gemini's documented hook events and output schema differ from Claude's. Gemini has no documented `PreCompact` event.
- Safety properties, enforced by `scripts/test-hooks.py`: no subprocess, network, or dynamic-code use; malformed events fail open; `stop_hook_active` prevents repeat blocks; settings merge is idempotent, backed up, and refuses symlinks and non-strict JSON.
- Limits: the guard is a guardrail, not a sandbox. Gemini's documented schema has no permission-prompt decision, so actions classified as "ask" are denied with a request for user review. Native host behavior is NOT VERIFIED; see `docs/HOOKS.md`.

## D-022 — Legacy stdio honors the declared pagination contract
- Decision: the legacy stdio core paginates `tools/list`, `resources/list`, `resources/templates/list`, and `prompts/list` with the shared `rcoder_contract.paginate_result` cursor, exactly as the modern transport already did. An invalid or out-of-range cursor maps to Invalid params (`-32602`) instead of an internal error.
- Rationale: `contracts/rcoder-v2.json` and `docs/V2-CONTRACT.md` declared these collections paginated at 10 items per page, but only the modern transport implemented it. A stdio client therefore received all tools in one response, which is what made the serialized `tools/list` size the binding context-cost constraint and blocked any new tool.
- Consequence: the enforced bound moves from "whole registry serialized" to "`tools/list` first page", because that is the payload a client reads before paging. Existing clients that never send a cursor are unaffected beyond receiving the first page and a `nextCursor`.
- Note: legacy single-call results and the modern transport remain separate protocol paths; both now share the same cursor semantics.

## D-023 — MCP exposes read-only skill/hook introspection; writes stay in the CLI
- Decision: add `rcoder_skill_lint`, `rcoder_hooks_config`, and `rcoder_contract` to the MCP server. Skill scaffolding, skill packaging, and hook installation remain CLI-only (`skill new|package`, `hooks install|uninstall`).
- Rationale: D-016 requires every MCP tool to be read-only and `scripts/test-mcp.py` asserts `readOnlyHint: true` and `destructiveHint: false`. Creating files, writing ZIPs, and merging host settings are not read-only operations.
- Consequence: the plugin CLI gains a `hooks <install|uninstall|print-config>` command so the opt-in guard/completion-gate capability is reachable without hand-editing JSON, while the MCP server can render and validate configuration without ever applying it.


## D-024 — Opt-in RFC host injection through Claude lifecycle hooks
- Decision: extend the bundled Claude plugin hook manifest with `UserPromptSubmit`, `Stop`, and `SessionEnd` for RFC Context Fabric. `UserPromptSubmit` assembles and injects a fresh context payload through the host's documented `additionalContext` field; `Stop` records the final response and validates the canary against the same `(session_id, prompt_id)` delivery.
- Rationale: persistent storage becomes useful to a stateless model only when each request receives a newly assembled payload through the actual host request path. A corresponding response capture provides an auditable delivery signal.
- Safety and scope: the adapter is inert until a workspace RFC database exists, uses one private single-use canary per delivery, stores only its digest in SQLite, retains the canary across repeated Stop calls, removes it at the next prompt or SessionEnd, creates a private runtime prompt ID and pending-session pointer when Claude omits prompt_id, and fails open without blocking the conversation. It does not enable the separate heuristic completion Stop gate, does not write to MCP, and does not claim that the assistant understood or followed the context.
- Verification: `scripts/test-context-fabric-host.py` validates the local hook contract and delivery pairing; live loading and invocation in a Claude Code process remain NOT VERIFIED.


## D-025 — Runtime attaches to the actual local RCoder MCP process
- Decision: the optional Rust Runtime companion is started by the bundled local Python RCoder MCP stdio server or loopback HTTP service, not by scanning for arbitrary MCP processes or by keeping a global always-on daemon. It watches the exact long-lived MCP parent process and records a project-local session; one-request HTTP workers explicitly disable companion startup.
- Rationale: the actual RCoder MCP entrypoint is stronger evidence than a server alias or the presence of an unrelated MCP manifest. Detection requires the known RCoder command/module path rather than the server's display name. This avoids activating Runtime for Serena or other independent servers and scopes Runtime lifetime to a real RCoder MCP session.
- Safety and scope: Runtime is optional and fail-open; unavailable or failed startup never blocks MCP. It does not alter host permissions, intercept agent tool calls, execute arbitrary commands, or read/write RFC storage. Session metadata excludes MCP arguments, environment values, prompts, and tool output. Unix runtime-state directories are owner-only and symlinked state directories are rejected.
- Verification: Rust unit tests cover manifest detection, unrelated-server exclusion, orphan session classification, and state-directory symlink rejection; the Python bootstrap regression covers disabled, missing, successful, and failed startup paths. Native host activation was NOT VERIFIED when this decision was recorded; for OpenCode 2.4.2 it was subsequently exercised through the installed host, as recorded in D-032. Other hosts remain NOT VERIFIED.


## D-026 — Typed execution contracts and evidence-gated task completion
- Decision: Runtime persists versioned task contracts with an objective, explicit acceptance criteria, constraints, risk level, state history, and criterion-scoped evidence attestations. A task may enter `completed` only when every criterion's latest attestation in the current verification cycle is `pass`; reopening a completed task to `active` with a reason starts a new cycle while retaining old evidence for audit and excluding it from the new completion gate. Evidence and transition histories have fixed upper bounds; invalid state transitions are rejected.
- Rationale: the Runtime needs a machine-readable task record and deterministic lifecycle before it can provide host adapters, policy gates, and independent verification.
- Safety and scope: contracts are stored separately under `.rcoder/runtime/tasks/`; RFC remains responsible for durable cross-request context and RSaver remains responsible for context reduction. Evidence summaries and sources are caller-supplied attestations, not proof that a command ran or that the referenced artifact is valid. This controller does not intercept host tools or grant permissions.
- Verification: Rust unit tests cover task creation, valid/invalid transitions, fresh-evidence completion gates after reopening, latest-failure behavior, backward compatibility for older task contracts, blocking reasons, bounded history behavior, and task-ID/path safety.


## D-027 — Deterministic bounded instruction packet compilation
- Decision: Runtime compiles only active task contracts into a schema-versioned structured packet containing the task objective, constraints, risk, acceptance criteria, latest current-cycle evidence per criterion, explicit trust/permission boundaries, and a SHA-256 digest over the canonical payload.
- Rationale: hosts need a stable machine-readable contract representation before the next stage can inject it into each model request and retry. Deterministic serialization makes a task revision auditable and deduplicable.
- Safety and scope: task fields are explicitly untrusted data and cannot override system, repository, or host policy. Blocked/draft/completed/cancelled tasks cannot compile. The 64 KiB packet limit rejects oversized content without truncation. Compilation is on-demand and does not itself inject context or intercept host tools; RFC remains the owner of durable per-request context hydration.
- Verification: Rust unit tests cover deterministic digests, active-state gating, latest current-cycle evidence selection, stale-evidence exclusion after reopening, and oversized-packet rejection.


## D-028 — Fail-open Claude Runtime task packet injection
- Decision: The Claude Code plugin registers a dedicated `UserPromptSubmit` command beside RFC's existing context adapter. The Runtime adapter invokes `rcoder-runtime task compile --active --json` and emits `hookSpecificOutput.additionalContext` only when exactly one valid active task exists.
- Rationale: the deterministic instruction packet must be attached on each eligible request/retry without conflating Runtime task state with RFC's durable context store.
- Safety and scope: the adapter is opt-in through the packaged Claude plugin hook manifest, does not create a task store, and fails open on missing/multiple active tasks, missing binary, invalid packet, or timeout. It launches a fixed argument vector using an OS-environment allowlist and disables recursive companion startup. Task fields remain untrusted data; host permissions remain authoritative. Other hosts are not covered by this adapter.
- Verification: Python regression tests cover injection output, absent/disabled state, missing binary, ambiguous/no active tasks, malformed schema, recomputed SHA-256 integrity, a shared Rust/Python canonical digest fixture, best-effort secret-pattern rejection, timeout, sanitized child environment, and symlinked task store. Native Claude Code invocation remains NOT VERIFIED.


## D-029 — OpenCode V2 dual adapter with one canonical host state
- Decision: `.opencode/plugins/rcoder.js` exports both an official V2 `setup(ctx)` plugin and the V1 `server(options)` middleware. V2 calls a small Python bridge for independent Runtime and RFC payloads, and all host payloads come from one normalized state object built by `createHostState()`.
- Rationale: OpenCode 2.4.2 does not invoke V1 implementations and sanitizes the plugin environment (observed: `RCODER_*` variables and caller `PATH` absent; configured plugin options arrived as `{}`). A hidden lifecycle state or optional chaining would silently drop host configuration.
- Safety and scope: workspace JSON files supply `runtime_disabled`, `rfc_disabled`, and an absolute `runtime_path`; the existing Runtime adapter still uses an OS environment allowlist and sets `RCODER_RUNTIME_DISABLE=1` for the compiled child. Response capture is limited to sessions hydrated by this plugin instance and to model-step boundaries; ambiguous canary matches are rejected. There is no second task engine or context store.
- Verification: Node regression tests cover missing/default options, both disable flags, absolute/relative runtime paths, invalid workspace directories, and V1/V2 export shapes; Python tests cover bridge validation and RFC canary lifecycle. Live 2.4.2 evidence is recorded in `docs/OPENCODE-V2-ADAPTER.md`. Other hosts and versions remain NOT VERIFIED.


## D-030 — Bounded read-only artifact verification, not a verification engine
- Decision: add `rcoder-runtime task verify` as a narrow, read-only artifact inspector. It canonicalizes a project-relative path, rejects absolute/traversal/symlink paths, bounds reads to 256 KiB without truncation, hashes the inspected bytes with the existing `sha2` dependency, and records a deterministic report linked to an evidence record in the current verification cycle.
- Rationale: Runtime must distinguish a caller attestation from an artifact it independently inspected, without claiming that a command ran or that a claim is true. No command string from an evidence record is ever executed. The report cannot satisfy an acceptance criterion or change task state; completion still requires fresh passing evidence.
- Safety and scope: verification history is bounded (200 records), the artifact path and file contents never become instructions, the report contains no file contents, and the clock is explicit so identical inputs yield identical reports. Full command/artifact cross-checking and a general Verification Engine remain future work.
- Verification: Rust unit tests cover digest match/mismatch, no-declared-digest, missing/absolute/traversal/symlink/directory artifacts, oversized and malformed-digest refusal, deterministic reports, cycle linkage, persistence, bounded history, and non-satisfaction of a failing criterion. A CLI smoke test in an isolated fixture confirmed the persisted verdicts.


## D-031 — Artifact-backed outcome verification with explicit opt-in
- Decision: extend `task verify` with a versioned artifact-reference contract (path, allowlisted parser, optional digest, criterion, declared caller outcome, provenance) and a single strict `rcoder_test_report_v1` parser. A second bounded read confirms the inspected snapshot before any outcome is attributed. Reports carry distinct `declared_outcome`, integrity verdict, extracted counts, and verifier `verification_state` (`caller_attested`, `integrity_only`, `artifact_verified`, `failed`, `insufficient_evidence`).
- Rationale: a matching digest proves bytes, not passing tests. Only a report with passing cases and zero failures/errors may become `artifact_verified`; mixed reports are `failed`, and malformed, empty, unsupported, missing, oversized, mismatched, or mutated artifacts are `insufficient_evidence`. Nothing from an evidence source is executed as a command.
- Safety and scope: completion requirements remain opt-in per acceptance criterion via `--enforce`. Opted-in criteria require a current-cycle verified report linked to their latest passing evidence; stale-cycle reports and later failures cannot satisfy completion. Legacy contracts keep caller-attested behavior. The instruction compiler emits a compact verification summary with the caller claim beside the verifier state, omits the field when empty (preserving the golden digest), and enforces the 64 KiB packet bound. OpenCode remains transport glue and keeps RFC hydration independent.
- Verification: Rust tests cover passing/failing/mixed/empty/malformed reports, duplicate references, criterion mismatch, digest mismatch, unsupported parsers, mutation detection, reopen staleness, packet summaries and oversized packets. A live CLI fixture confirmed completion after a passing report and rejection after a mixed report. `scripts/test-opencode-host.py` asserts the structured summary reaches the compiled host context without raw report content.


## D-032 — Validate integration through the installed host, not adapter unit calls
- Decision: add a native OpenCode 2.4.2 end-to-end regression that starts the real executable with isolated XDG config/data/state, an OpenAI-compatible local mock provider, the real plugin and RCoder MCP entrypoint, and inspects the actual HTTP request body received by the provider.
- Rationale: a plugin load message, configuration digest, or direct adapter invocation cannot prove that context reached a model request. The host itself must be the source of the request, and RFC/Runtime delivery must be observable in the same payload with distinct provenance.
- Safety and scope: synthetic markers and a local-only mock key; no public API or real credential. The fixture enforces the build's `ses` session-ID prefix and an isolated `PWD`, uses timeouts, bounds provider output, and tears down processes. It adds no new host adapter, context store, or task engine. Other hosts, builds, and live provider behavior stay NOT VERIFIED.
- Verification: five regression cases passed locally — same-request marker delivery, four independence configurations, retry identity and missing context, Runtime startup failure, and direct MCP JSON-RPC with tool invocation. One companion session per fixture reached `stopped` with the fixture workspace root and no orphan process.


## D-033 — Portable host-test contracts instead of OS-specific fixtures
- Decision: extend `platform_runtime.py` with Node/host executable resolvers, a per-OS isolated host environment, a system-temp namespace, and a symlink-with-copy-fallback helper. The native E2E fixture now consumes those helpers instead of hardcoding `/tmp`, `XDG_*`, `PWD`, symlink support, or literal executable names.
- Rationale: the integration proof must be reproducible on the developer's PRoot/Termux host and structurally runnable on Windows, macOS and POSIX without maintaining separate fixtures. Windows `.cmd`/`.bat` host launchers are wrapped with `cmd.exe /c`; ambient provider credentials and OpenCode session variables are stripped on every OS.
- Safety and scope: helpers are pure local process/path contracts; no new runtime dependency, adapter, context store, or task engine. The Windows and macOS branches are covered by deterministic unit tests and remain NOT VERIFIED on those operating systems until executed there.
- Verification: `scripts/test-cross-platform.py` passes 13 tests, including simulated Windows environment and symlink-failure paths; the native OpenCode E2E suite still passes on the POSIX development host. README now reports this distinction in its Before/After and cross-platform sections.
