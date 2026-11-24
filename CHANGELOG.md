# Changelog

RCoder follows Semantic Versioning.

## [Unreleased]

### Fixed
- The legacy stdio MCP core ignored the pagination contract that `contracts/rcoder-v2.json` and `docs/V2-CONTRACT.md` declare: only the modern transport paginated, so a stdio client received every tool in one response and an invalid cursor returned an internal error instead of Invalid params. `tools/list`, `resources/list`, `resources/templates/list`, and `prompts/list` now use the shared cursor through both transports, and an invalid or out-of-range cursor returns `-32602` (D-022). This also unblocked the context-cost budget: because a client reads one page at a time, `scripts/test-mcp.py` now bounds the first `tools/list` page (measured 5,156 characters) instead of the whole serialized registry, which was 13,288 of a 13,300-character budget. A double-pagination defect in the modern adapter (the core already paginated, then the adapter paged again and dropped a valid `nextCursor`) is fixed and covered by `scripts/test-mcp-contract.py`.

### Added
- MCP tools `rcoder_skill_lint` (validate an Agent Skill folder: frontmatter, file safety, reference depth, local links), `rcoder_hooks_config` (render the opt-in `PreToolUse`/`Stop` entries without applying them), and `rcoder_contract` (read the shared 2.0 contract). Tool count is 27. Scaffolding, packaging, and hook installation stay CLI-only so every MCP tool keeps `readOnlyHint: true` (D-023).
- Plugin CLI command `hooks <install|uninstall|print-config>` with `--scope`, `--root`, `--home-dir`, `--profile`, `--only`, and `--dry-run`, matching the existing `skill` subcommand. Previously the opt-in guard/completion-gate capability required hand-editing host settings JSON.
- Opt-in Claude Code hook handlers in `skills/rcoder/scripts/rcoder_hooks.py` (wrapper `scripts/rcoder-hooks.py`, guide `docs/HOOKS.md`, decision D-021): a `PreToolUse` guard that denies credential-file reads, searches, and writes, `git add`/`diff`/`show` of credential files, catastrophic deletes and raw-disk writes, and asks before force pushes and piping a download into an interpreter (profile `strict` adds more prompts); and a `Stop` completion gate that blocks once when a turn edited code, claimed completion, ran no check, and gave no evidence labels. `install`, `uninstall`, and `print-config` merge idempotently with a backup and refuse symbolic links and non-strict JSON. Handlers use no subprocess, network, or dynamic code, fail open, and never loop. The bundled `hooks/hooks.json` is unchanged and still SessionStart-only (D-019). `scripts/test-hooks.py` is registered in CI and covered by new `validate-all` invariants. Native Claude Code loading is NOT VERIFIED.
- Slash commands `plan`, `debug`, `test-plan`, and `threat-model`, and read-only subagents `rcoder-planner` and `rcoder-debugger` (no file-editing tools, per D-018).
- `CONTRIBUTING.md`, `SECURITY.md`, issue and pull request templates, and a Dependabot configuration for the pinned workflow actions.

### Fixed
- Packaging omitted `hooks/`: the Claude plugin ZIP built by `scripts/package` and the npm package (`package.json` `files`) did not include the SessionStart hook that D-019 ships, so plugins installed from those archives silently lacked it. Both now include it, and `validate-all` checks it.
- `docs/DECISIONS.md` used D-019 for two different decisions; the MCP-tool decision is now D-020.
- PowerShell bootstrap (`install.ps1`) failed on every PowerShell version: it assigned `$home`, which is the read-only automatic variable `$HOME` ("Cannot overwrite variable HOME"). Renamed; `scripts/test-installers.ps1` now fails if any script assigns `$HOME`.
- Interactive installers (PowerShell launcher and Node manager) printed two numbered lists back to back, so the RSaver/RScan descriptions were numbered 1-2 and the choices were numbered 1-4 again. The description list now uses bullets. `scripts/test-installer-menus.py` drives both menus and fails on repeated or non-sequential option numbers.
- PowerShell portability: scripts used Windows-only `\` path literals (now `Join-Path`, so `pwsh` on Linux/macOS works); the feature manifest was written with a UTF-8 BOM on Windows PowerShell 5.1 (now BOM-free, ordered keys); `exit` replaced by `return` for the `irm | iex` route; TLS 1.2 is added to, not substituted for, the existing protocols; download progress rendering no longer slows 5.1; the `RCoder.cmd` shim falls back to `pwsh.exe` when `powershell.exe` is missing.
- MCP resources ignored project-local guidance: `resources/read` for `rcoder://specialist/{name}` always returned the built-in module even when `.rcoder/references/<name>.md` replaced it (as `SKILL.md` and `rcoder_get_specialist` already specified), and project-local extension modules were neither listed nor readable as resources. Resources now follow the same override rules and are served behind the same untrusted-content notice. `rcoder_list_specialists` now summarizes the active override instead of the shadowed built-in text.
- RSaver reference/marker collision: `dedupe --words` emitted `@N` references and `dedupe --blocks`/`collapse_phrase_repeats` emitted `[RSaver: ...]` markers. When the source text already contained that literal string, `unpack` expanded the wrong span and the restore was not byte-exact. References now use a prefix proven absent from the payload (`_reference_prefix`), and markers are allocated by `MarkerFactory`, which guarantees uniqueness against the original source. `scripts/test-rsaver.py` adds an adversarial case with literal `@0` and `[RSaver#0: ...]` in the input.

### Added
- RCoder 2.0 development contract: one machine-readable protocol/transport/pagination contract shared by stdio, stateless MCP, and the optional loopback HTTP adapter. Modern list methods now use bounded opaque cursors; conformance tests cover cursor errors, structured results, and the inline Skills manifest.
- Optional stateless Streamable HTTP adapter at loopback only: POST JSON, bearer token, exact Origin allowlist when Origin is present, protocol/method/name header binding, bounded requests, and isolated worker processes. It does not claim GET/SSE resumability or MCP session support.
- RScan deterministic stratified sampling with pinned metadata/CI/test/lock markers, explicit sampled-path evidence, and an unknown-truncated CI state to prevent false absence claims.
- Host integrations for OpenCode V1 (skill plus plugin adapter), Gemini CLI extension, Codex marketplace, and Claude Code marketplace instructions. Added the global CLI integration manager and cross-platform MCP launcher; existing MCP host settings are not rewritten by plugin-only installation.
- Agent Skill authoring CLI: rcoder skill new, lint, and package, including a 13-section specialist template, strict frontmatter/links/file-bound checks, secret and symlink rejection, reproducible ZIP output, and SHA-256 sidecar.
- MCP transport specialist and explicit multilingual activation rules. The separate multilingual research dataset now has 12 verbatim English, Indonesian, and mixed-language cases with identifier-integrity expectations and negative controls; static fixture validation does not claim live routing accuracy.
- MCP tools `rsaver_redact` (mask credential-shaped values in inline text or a file; lossy, never echoes the secret, `fail_on_found` gate, credential files refused) and `rsaver_ledger` (read-only cumulative savings report), exposing the existing `rsaver redact` and `rsaver ledger report` commands to MCP hosts. Recording to a ledger stays in the CLI so every MCP tool keeps `readOnlyHint`. Tool count is now 24; the full-profile character budget in `scripts/test-mcp.py` moved from 12,500 to 13,300 (measured 13,288 characters, about 3,880 estimated tokens). `scripts/test-mcp.py` covers masking without echo, the `fail_on_found` exit, credential-file refusal, ledger reporting, and ledger immutability. `docs/MCP.md` and `rsaver.md` document both, including a redact-before-sharing step.
- Four specialist modules for areas that had no coverage: `android-platform-engineering` (AOSP and custom ROM trees, Soong, Treble/VINTF, SELinux policy, HALs, vendor blobs, boot, AVB and OTA), `windows-platform-engineering` (Win32/COM/ETW, services, installers, Authenticode signing, PowerShell 5.1 versus 7 pitfalls), `iac-platform-engineering` (Terraform/OpenTofu, Kubernetes, Helm, plan review, state, drift, rollout safety), and `graphics-gpu-engineering` (Vulkan/D3D/Metal/WebGPU, shaders, compute, device-lost, frame pacing). Each follows the 13-section template, is routed from `SKILL.md`, is required by `validate-all`, and has expanded routing cases `ex-23` to `ex-30` (seven positive, one negative control). They are not yet measured in a live run.
- MCP setup inside every installer. PowerShell (`-Mcp none|show|install`), Node (`--mcp`), POSIX (`--mcp`), and the interactive manager (a new MCP step after the optional tools, plus action "4. Set up MCP server" for hosts that already have RCoder). `show` prints the exact config for the chosen host and changes nothing; `install` merges only the `rcoder` entry, backs the file up first, never overwrites a different existing entry, leaves non-strict JSON (comments) untouched, refuses symbolic links, and then runs a live `initialize` + `tools/list` self-test. Automatic routes: Claude Code (`.mcp.json`, or `claude mcp add` for user scope), Cursor, Gemini CLI, GitHub Copilot/VS Code (project), OpenCode, Codex (user, TOML). Other hosts print the generic snippet. Implemented once in `skills/rcoder/scripts/rcoder_mcp_setup.py`; tested by `scripts/test-mcp-setup.py`. Native host loading remains NOT VERIFIED.
- `-SourceDir` on the PowerShell bootstrap installs from a local checkout (offline or pre-release testing) instead of downloading.
- Dual-era MCP entry point `skills/rcoder/scripts/rcoder_mcp_modern.py` (stateless `2026-07-28` plus Skills over MCP; legacy sessions reach the unchanged core), its test `scripts/test-mcp-modern.py`, and `docs/MCP-MODERN.md`. The Claude Code plugin manifest now launches it. Streamable HTTP is not implemented.
- Specialists `llm-agent-security` (prompt injection, tool poisoning, agent permission design) and `observability-sre` (telemetry, SLOs, alerting, rollback readiness), routed from `SKILL.md`, with two new expanded routing cases (`ex-21`, `ex-22`). They are not yet measured in a live run.
- Slash commands `agent-security` and `observe`. The plugin now ships a read-only `SessionStart` hook (`hooks/hooks.json`, decision D-019, authorized by the repository owner) that runs the bundled `rscan scan`; `validate-all` restricts it to that single event and command shape.
- `rsaver redact`: lossy, best-effort masking of credential-shaped values (private-key blocks, AWS and GitHub and Slack tokens, `sk-` style API keys, JWTs, bearer tokens, URL credentials, password/token assignments) with stable numbered placeholders, preserved line numbering, no stored or hashed secret, and `--fail-on-found` for gating. Available from the CLI and, as `rsaver_redact`, from the MCP server (see the MCP tools entry above).
- `rsaver ledger record|report` and `--ledger PATH` on `compact` and `dedupe`: a cumulative estimated-savings JSON ledger written atomically to a user-chosen path, rolling old entries into totals after 500 runs.
- `rsaver audit` and MCP tool `rsaver_audit` (tool count is now 22): a read-only, bounded project context-cost audit. It ranks files by estimated tokens, groups them by category (lockfile, minified, generated, log, data, source, docs), reports the share of cost that is rarely worth loading whole, gives a per-file reduction command, upper-bounds repeated-line cost for the top files, and suggests exclusion patterns. It skips dependency trees, symlinks, binaries, and credential files, never prints file contents, and honors `--max-files` and `--max-read-bytes`. Run on this repository it reported that retained evaluation run data files (mostly `*.jsonl`) account for about 78% of the repository's estimated tokens, a concrete reason to select from them instead of loading them. `scripts/test-rsaver.py` and `scripts/test-mcp.py` cover categories, skip rules, secret non-disclosure, truncation, ordering, and rejection paths.
- RSaver zero-token duplicate elimination. `dedupe --words` collapses repeated words and 2-7 word phrases to a single reference per distinct value; `dedupe --blocks` collapses contiguous repeated command/output blocks (PowerShell, CMD, terminal, test/build runners) keeping the first execution verbatim; `pack --method dict` / `unpack` provide the same dictionary form as a pack manifest. All three are byte-exact and SHA-256 checked on restore.
- `rsaver compact --target-savings N` prunes non-critical lines toward an explicit savings percentage while always retaining every critical (error, status, hash, URL) line.
- MCP tools `rsaver_anchor`, `rsaver_reanchor`, `rsaver_dedupe`, `rsaver_recover`, `rsaver_verify`, `rsaver_pack`, `rsaver_unpack`; `rsaver_compact` and `rsaver_dedupe` gained the corresponding parameters. Tool count is now 21.
- MCP prompts `rcoder_context_gate` and `rcoder_reanchor`.
- Slash command `saver` and least-privilege subagent `rcoder-saver` (read-only; no file-editing tools).

### Changed
- `docs/MCP.md` and `README.md` document the expanded RSaver toolset, the new prompts and plugin components, and the re-measured tool-list cost (21 tools; about 11,800 characters and 3,470 estimated tokens serialized).

### Measured savings (deterministic relative estimate)
- Repeating command blocks: about 94% (1424 -> 76).
- Repeating phrases/words: about 95% (481 -> 25).
- Timestamped template logs: about 96% (1253 -> 55).
- Low-repetition or high-entropy text: 0-5%; the tools report this instead of inflating it.
- Every figure above is reproducible from the working tree with `rsaver dedupe`/`rsaver pack`; they are relative estimates, not provider billing.

### Verification status
- Behavior above is VERIFIED locally by `scripts/test-rsaver.py`, `scripts/test-mcp.py`, and `scripts/validate-all` (3140 checks after the audit, redact, and ledger additions; 3139 before). `rsaver_audit` has not been exercised through a live host MCP connection, so `docs/RCODER-MCP-LIVE-TEST-REPORT.md` still covers the original 21 tools. Host-side activation and hosted CI for this change are NOT VERIFIED.

### Added
- `rcoder_list_specialists` accepts an optional `query` that ranks candidate module names by name, title, and "Activate when" text (top 15 with a score). It never chooses a primary.
- Deterministic specialist-routing assistant: `skills/rcoder/scripts/route_predict.py` (stdlib-only CLI, `--text/--file/--json`) proposes a narrow candidate set from documented high-precision signals plus cross-domain base/narrow composition, with per-module evidence, ordinal confidence, scope rejection, and a proposal cap of four modules. MCP tool `rcoder_route_predict` exposes the same proposal read-only through the server; `rcoder_validate_selection` gates the final set. Reference module `references/deterministic-routing.md` documents the contract, held-out scoring, failure modes, and output format. Held-out routing F1 (canonical 0.789, expanded 0.605, multilingual 0.718, manual held-out 0.828) and negative rejection are measured by `scripts/test-route-predict.py`. Results are labels from the frozen evaluation data, not live host activation; no model capability is claimed.
- Weak-model execution profile (`references/weak-model-profile.md`): a deterministic, prompt-only action policy for models below ~30B active or with ≤32K context — contract-first requirements, bounded exploration, edit-by-call-12, one focused verification plus one repair, anti-loop thresholds, an operating contract with an autonomy ceiling, and explicit partial-status stop criteria. Rules are derived from published 2025-2026 harness research (Fan et al. arXiv 2609.20804: planning +11.6pp on the weakest model; McAndrews arXiv 2604.21950: self-refine with execution feedback +4σ on 1-3B; Ghosh 2026 budget-disciplined prompting; DEV 2026-11-20 operating contracts). Evidence is cited in the module; it is not a claim that any single rule was measured here.
- Repository structural map (`skills/rcoder/scripts/repo_map.py`, wrapper `scripts/repo-map.py`, reference `references/repo-map.md`): a compact, token-budgeted map of public symbols, signatures, imports, entry points, and PageRank-ranked files, with no function bodies. `compact`/`default`/`detail` formats, `--json` mode, optional tree-sitter when present, regex fallback otherwise. MCP tool `rcoder_repo_map`. Deterministic checks in `scripts/test-repo-map.py` cover discovery, extraction, graph edges, ranking order, budget bounding, and determinism. The pattern is grounded in 2026 repo-map results (leanlm.ai 2026-11-21: wrong-file edits 47/80 to 0/80; sourcecrumb/atlas/repomap/sinter design notes), but the numbers are literature values, not measurements of this helper.
- `completion/complete` for the `{name}` argument of the specialist and template resource templates (case-insensitive prefix, at most 100 values), with the `completions` capability advertised from protocol `2025-03-26`.
- MCP prompts `rcoder_route` and `rcoder_verify`, mirroring the plugin's `/route` and `/verify` commands for hosts that surface MCP prompts.
- `scripts/test-mcp.py` covers the resource override and extension behavior, query ranking and rejection paths, completion success, hostile-value, and invalid-parameter paths, capability gating by protocol version, and the new prompts. The new assertions fail against the previous server.

### Changed
- `commands/route.md` mentions `query`; `docs/HANDOFF.md` now covers v1.14.0.

## [1.14.0] - 2026-11-22

### Added
- `skills/rcoder/scripts/rcoder_mcp.py`: a read-only, dependency-free stdio MCP server (protocol versions 2025-06-18, 2025-03-26, 2024-11-05) with 14 tools (RScan, RSaver, stack detection, bounded snapshot, specialist list/get with section-level loading, routing-selection validator, doctor), resources for the router, every specialist and every template, and four workflow prompts. Path arguments are confined to `--root`, symlink escapes and credential files are refused, helpers run with an argument vector, timeouts, and bounded output. `--profile minimal`, `--tools`, and `--print-config HOST` (claude-code, codex, cursor, gemini-cli, vscode, opencode, generic) are provided. Project-local `.rcoder/references/` guidance is served with an untrusted-content notice.
- `scripts/rcoder-mcp.py` repository-root wrapper and `docs/MCP.md` (tools, security model, measured context cost, evidence status).
- `agent-extensions-engineering` specialist (MCP servers, Agent Skills, plugins, marketplaces, slash commands, hooks, subagents), routed from `SKILL.md`.
- Claude Code plugin components: slash commands `scan`, `route`, `review`, `verify`, `handoff`, `doctor`, and subagents `rcoder-explorer`, `rcoder-reviewer`, `rcoder-verifier`, `rcoder-security-reviewer` (no file-editing tools; the security reviewer has no shell); the plugin manifest declares the MCP server.
- `scripts/test-mcp.py`: scripted-client protocol, negotiation, schema, confinement, secret-refusal, argument-injection, output-bound, resource, prompt, and CLI tests, including a character budget on the tool list.
- Expanded routing dataset cases `ex-19` and `ex-20` for the new specialist.
- Validator group G8: MCP server safety invariants (no shell, no network, no third-party imports, confinement present), helper-set parity with `SKILL.md`, stale-module-name detection, strict tool schemas, command and agent frontmatter rules, least-privilege agent tools, and a ban on default hooks.

### Changed
- `SKILL.md` gained an optional MCP section, a routing row for the new specialist, and a `compatibility` field. The skill description is unchanged so trigger behavior is not altered.
- `scripts/package` includes `commands/` and `agents/` in the Claude plugin archive; CI runs the MCP tests and verifies the printed configuration is valid JSON.
- `docs/ARCHITECTURE.md`, `docs/DECISIONS.md` (D-016 to D-018), `docs/COMPATIBILITY.md`, and `README.md` describe the new layer.

### Decisions
- No hook ships by default; automatic RScan stays opt-in through `rscan hooks install`.
- Slash commands do not pre-approve tools.

### Verification status
- MCP protocol behavior, confinement, secret refusal, output bounds, validator invariants, and packaging are VERIFIED locally by the scripts above.
- Host connection to the server, host-specific configuration formats, Claude Code loading of commands, agents, and the manifest `mcpServers` entry, and any effect on model outcomes are NOT VERIFIED.

## [1.13.0] - 2026-11-19

### Added
- Operational selection gate: a fired trigger must emit a non-empty, on-disk-valid, non-helper-only specialist set before execution; framing bases are additive and cannot be substituted by a near-neighbour module. Routing now classifies by deliverable and acceptance criteria so paraphrased and non-English prompts are not dependent on English keywords.
- Three deterministic routing-semantic checks in `verify-objective.py` (`negative_selection_empty`, `non_helper_primary`, `expected_specialist_overlap`) plus `--strict` for gating.
- `tool_probe.py` version detection, bounded output capture, POSIX process-group cleanup, partial-output retention, and CLI exit-code propagation (`--strict`); `model-adaptation.md` documents the verified flags.
- `run-benchmark.py` separate dataset paths, single-arm execution, and pinned `config.json` provenance, enabling separate control/expanded dataset runs.
- `scripts/check-dist.py` verifies rebuilt ZIP artifacts against `dist/SHA256SUMS`; CI registers it and a meta-check that every test script is wired into the workflow.
- `docs/V1.13-DEV-LEDGER.md` and a bounded live ablation record under `evals/runs/v113-live-free-2026-11-19/`.

### Changed
- `web-platform-engineering` was added to the SKILL.md routing tables; it existed on disk but was absent from the router.
- `validate-all` now derives the product version from SKILL.md instead of a hardcoded literal, enforces a minimum check-count floor, and requires the v1.13 records.
- Documentation states that "opencode NOT AVAILABLE" was an observation of an earlier development shell, not a permanent host fact: the CLI is available through the verified glibc loader in this session.

### Verification status
- Local gates: 2959 structural checks plus ten Python self-tests, Node installer matrix (40 target/scope cases), npm pack dry-run, installer simulations, reproducible package build, and SHA256SUMS verification — VERIFIED locally.
- Fresh bounded live ablation on the authorized free tier: CONTROL v1.11.0 vs TREATMENT v1.13 on 12 comparable positive triggers. Specialist F1 0.368 -> 0.476, exact-match 0.000 -> 0.083, empty positive sets 7/12 -> 5/12, trigger F1 0.957 -> 0.857 (regression), recorded tokens +0.5%, tool calls 99 -> 98 — VERIFIED computations over retained evidence, small sample, no significance claim. Full detail in the delivery record.
- Independent judge, human adjudication, expanded-dataset live run, multilingual live run, non-OpenCode host tiers T2-T4, and subagent orchestration measurements remain NOT VERIFIED.

## [1.12.0] - 2026-11-19

### Reconciled
- Product version advanced to 1.12.0 across SKILL.md, all four plugin/package manifests, marketplace manifest, package builder, changelog, and validator. The prior "v1.11.1" label existed only in commit and PR titles; the actual product version on main was 1.11.0 (evidence: `evals/runs/BASELINE-LEDGER.md`).
- Specialist inventory verified at 59 reference modules before the change; one (`specialist-routing`) was added for a demonstrated routing-coverage gap, for 60 total. All 60 retain the 13-section structure.

### Added
- `specialist-routing.md`: evidence-driven multi-stage routing architecture (request understanding through verification), an explicit specialist selection contract, primary/supporting/verifier roles, cross-discipline base+narrow rules, a disambiguation table for overlapping domains, and anti-over-selection rules. Derived from case-level analysis of the v1.11 control run.
- `scripts/verify-objective.py`: deterministic objective verifier producing `objective_checks` flag maps from prediction artifacts without using the tested model as judge.
- `scripts/test-score-scenarios.py`: judge helper unit tests (strict flag parsing, blinding, output naming) that do not require a live judge model.
- `evals/EVALUATION-INDEPENDENCE.md`: layered, blinded evaluation methodology with explicit bias disclosure.
- `evals/MULTILINGUAL-POLICY.md` and `evals/datasets/multilingual.triggers.json`: separate, explicitly documented multilingual activation dataset. The canonical English-only `evals/triggers.json` contract is unchanged.
- `evals/runs/BASELINE-LEDGER.md`: immutable SHA-256 control dataset record written before routing changes.
- Scorer: per-specialist confusion counts, trigger FP/FN rates, specialist negative false-activation and positive-empty-activation rates, cross-domain subset scoring, negative-prompt rejection metrics, `objective_checks` consumption, invalid-case exclusion, and F1 from raw counts.

### Changed
- SKILL.md routing tables use explicit "default / when-to-use-instead" disambiguation instead of ambiguous "X and Y" pairings, and require a non-empty specialist set whenever a trigger fires.
- `score-eval.py` treats prediction records with `"valid": false` as excluded by default (opt in with `--include-invalid`); the v1.11 control exposed an invalid case entering scoring.
- Scenario judgement no longer overwrites retained prediction files; judged copies are written separately and judge responses are retained in full.
- `validate-all` derives the expected version from SKILL.md (single source of truth) and adds semantic specialist checks beyond heading presence.
- CI adds objective-verifier and judge-helper regression steps.

### Verification status
- Deterministic checks (structure, scorer, self-tests, packaging, installers) are VERIFIED locally and in Linux/Windows CI.
- Model-dependent routing/behavioral metric improvements are INFERRED only: `opencode` is unavailable in the development shell and no live run was authorized, so no new paid benchmark was executed. The pinned control dataset is preserved unchanged.

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
