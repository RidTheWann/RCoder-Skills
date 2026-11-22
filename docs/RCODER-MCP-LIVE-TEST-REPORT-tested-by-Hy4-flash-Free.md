# RCoder MCP — Full Live Integration Test & Evidence Report

> **Tested by model: Hy4 flash Free** (OpenCode, model ID `hy4-flash-free`)

## Evidence provenance

Every tool listed below was **actually invoked through the OpenCode MCP connection** in this session using the exposed `tools.rcoder.*` surface. Tool definitions and argument schemas were inspected from the tool catalog exposed by the session before invocation. No local script was substituted for an MCP call, and no response was simulated. Local shell commands were used only for environment reconnaissance (versions, git state, file listing) and for creating controlled fixture files; the behavior under test always came from an MCP invocation.

Fixtures used for file-based tools are under `.mcp-live-test/` (created for this test and left in place for reproducibility). They are disposable and contain no source code modifications.

This file was renamed after test execution to carry the model watermark in its filename; all quoted tool outputs remain verbatim from execution time.

---

## 1. Test date and environment

| Item | Observed value |
|---|---|
| Test date | 2026-11-22 |
| Host platform | Linux |
| Working directory / server root | `/root/RCoder-Skills` |
| Git state | branch `main`, HEAD `6b64b7d`; pre-existing untracked `.agents/` and `opencode.json` (not modified) |
| Python | 3.14.4 |
| RCoder MCP server version | `1.14.0` (from `rcoder_doctor`) |
| Negotiated MCP protocol | `2025-06-18` (also advertises `2025-03-26`, `2024-11-05`) |
| Skill directory | `/root/RCoder-Skills/skills/rcoder` |
| Reference modules | 61 built-in, 0 project-local |
| Helpers | `rscan`, `rsaver`, `context_snapshot`, `detect_stack`, `tool_probe` all `true` |
| Enabled tools | `all` |
| RSaver helper version | `1.11.0` (reported in RSaver tool results) |
| Feature flags | `null` in `rcoder_doctor` (no root `.rcoder-features.json`; a `.agents/.rcoder-features.json` path appears in the snapshot) |

## 2. OpenCode version

`opencode --version` reported **`opencode v2.3.2`**. No native OpenCode "MCP status" subcommand was observed in this session, so connection status was established by tool discovery plus successful calls rather than by a status display.

## 3. MCP connection status

**CONNECTED AND FUNCTIONAL.** Evidence:

- All 21 expected tools were discoverable with strict argument schemas (`additionalProperties: false`, bounded integers/strings).
- The first call, `rcoder_doctor`, returned live server metadata (`server_version: 1.14.0`, `root: /root/RCoder-Skills`, `enabled_tools: all`).
- All 21 tools were subsequently invoked and returned real results; no tool was unavailable.
- This closes the "NOT VERIFIED — any host connects to the server, lists its tools, and a model calls them" claim in `docs/MCP.md`, for this OpenCode host and session.

The server note in `rcoder_doctor` is respected: reachability is proven by the call itself, while host-side native skill discovery is a separate matter and was **not** independently verified.

---

## 4. All 21 tools — individual results

Status legend: **PASS** = actual MCP invocation succeeded and functionality verified; **PARTIAL** = invoked but only partly verified; **FAIL** = invocation failed or behavior incorrect; **NOT TESTED** = no invocation.

| # | Tool | Status | Invocation evidence (abridged) |
|---|---|---|---|
| 1 | `rcoder_doctor` | **PASS** | `server_version=1.14.0`, `python=3.14.4`, `negotiated_protocol=2025-06-18`, `root=/root/RCoder-Skills`, `reference_count=61`, `enabled_tools=all` |
| 2 | `rcoder_scan` | **PASS** | `root="."`, `max_paths=80` → `ok=true`, 6 ranked `development_options` (`FINISH_CHANGE` 90, `QUALITY_GATES` 85, `DEPENDENCY_SECURITY` 80, `SECURITY_REVIEW` 75, `ONBOARD` 70, `REFACTOR` 50) with first commands and specialists |
| 3 | `rcoder_detect_stack` | **PASS** | `root="."`, `max_depth=3` → manifest `package.json`, stack `JavaScript / TypeScript (Node.js)`, quality entries `AGENTS.md`, `CLAUDE.md`, `.github/workflows` |
| 4 | `rcoder_context_snapshot` | **PASS** | `root="."`, `max_paths=40`, `max_depth=2` → git `main...origin/main`, key files present, bounded path list, `source_contents_included=false`, `truncated=true` |
| 5 | `rcoder_list_specialists` | **PASS** | No args → `count=61`; with `category="core", query="test"` → `count=2` ranked (`test-engineering` 9, `testing-qa` 9) plus ranking caveat |
| 6 | `rcoder_get_specialist` | **PASS** | `name="coding", sections=["Procedure","Verification"]` → exact two sections; `name="rsaver", sections=["Verification"]` → exact section |
| 7 | `rcoder_validate_selection` | **PASS** | Valid selection `coding`/`rsaver`/`verification` → `valid=true`; helper-only `rsaver`/`rsaver-gate` → `valid=false` with two precise errors |
| 8 | `rsaver_measure` | **PASS** | Inline text → `total_estimate=13` (`chars_over_4=13`, v1=15); two file paths with `openai-o200k` → `337` each, `total=674`, `lines=35` |
| 9 | `rsaver_select` | **PASS** | `match="ERROR\|STATUS=\|sha256", context=1` → 3 kept ranges `[[6,11],[15,18],[34,35]]`, critical lines `[7,9,10,16,17,35]`, 68.02% saved; path escape `"../../etc/passwd"` correctly refused |
| 10 | `rsaver_compact` | **PASS** | `max_lines=12, target_savings=70, head=3, tail=3` → 344→100 estimate (70.93%), 9 critical lines preserved, omitted ranges `[[2,6],[12,15],[18,33]]`; source file unchanged |
| 11 | `rsaver_budget` | **PASS** | `window=4000`, reserves `800/600`, schema `700` → `available_input=2600`, `item_budget=1900`, `reserve_percent=35`; invalid reserves → clean `exit_code=2` error |
| 12 | `rsaver_drift` | **PASS** | Default window → 3 signals; `recent_window=3` → 4 signals including objective/constraint loss; diagnosis correctly labeled `NOT VERIFIED` heuristic |
| 13 | `rsaver_crosscheck` | **PASS** | Good artifacts → `verdict=PASS` with usage fields; failing test log → `verdict=FAIL` with `claim_consistency=fail` |
| 14 | `rsaver_gate` | **PASS** | Inline envelope → `projected_total=3750/4000`, `headroom=250`, `cache.eligible=true`, `contiguous_static_prefix=true`, 0 deferred; small window → warnings `required_items_exceed_budget`, `tool_schema_exceeds_available_input` |
| 15 | `rsaver_anchor` | **PASS** | Inline state → dual-end block with `[OBJECTIVE-1]`, 3 constraints, 2 facts, decision/unresolved, `[NEXT-ACTION]`; `estimate=304/400`; small budget → `anchor_exceeds_budget` warning |
| 16 | `rsaver_reanchor` | **PASS** | Envelope + state files → anchor inserted at both ends, gate re-evaluated: `deferred_count=1`, `projected_total=3853/4000`, `headroom=147`, cache eligible |
| 17 | `rsaver_dedupe` | **PASS** | Inline text with 9 duplicate long lines → `211→62` estimate, 70.62% saved, collision-free marker, critical lines `[7,8]` preserved |
| 18 | `rsaver_recover` | **PASS** | Ranges `2:6`, `12:15`, `18:33` returned exact original lines; all three byte-identical to fixture (details in §6) |
| 19 | `rsaver_verify` | **PASS** | Valid manifest → `RSAVER VERIFY PASS ... critical lines and range hashes intact`; tampered hash → `RSAVER VERIFY FAIL: original content hash does not match the manifest` (`exit_code=1`) |
| 20 | `rsaver_pack` | **PASS** | `method=zlib` → 481→80 estimate (83.37%), payload 208 chars; `method=dict` → 481→101 (79%), dictionary + block markers, both `worthwhile=true` |
| 21 | `rsaver_unpack` | **PASS** | Both manifests → `verified=true`, 2171 chars restored; byte-identical to original inline text for both methods |

**Totals: PASS 21 · PARTIAL 0 · FAIL 0 · NOT TESTED 0.**

---

## 5. Actual test cases and observed outputs

### 5.1 RCoder core (7 tools)

1. **`rcoder_doctor()`** — first live call. Returned metadata quoted in §1 and §3.
2. **`rcoder_scan({root:".", max_paths:80})`** — `ok=true`; top option `FINISH_CHANGE` (priority 90, triggered by `uncommitted_changes`, first commands `git status --short`, `git diff --stat`, `python3 scripts/validate-all`); also detected `no_ci`, `dependency_without_lock`, `security_surface`, `unfamiliar_repository`. Functionality matches "ranked next actions with first commands and specialists".
3. **`rcoder_detect_stack({root:".", max_depth:3})`** — heuristic manifest/quality detection; note field "Read-only heuristic; verify actual commands and versions before running them." respected.
4. **`rcoder_context_snapshot({root:".", max_paths:40, max_depth:2})`** — returned a bounded path/Git map with `truncated=true` and no source contents, as designed.
5. **`rcoder_list_specialists({})`** → 61 modules. **`rcoder_list_specialists({category:"core", query:"test"})`** → only 2 ranked candidates with `score=9` and the explicit warning that a query "does not choose a primary".
6. **`rcoder_get_specialist({name:"coding", sections:["Procedure","Verification"]})`** → exactly the requested sections, 7 procedure steps plus verification text; `source="built-in"`.
7. **`rcoder_validate_selection`** — valid: `{"valid":true,"errors":[],"selected":["coding","rsaver","verification"]}`. Invalid (helper primary + helper-only set): `{"valid":false,"errors":["helper modules (...) are supporting only and cannot be primary","helper-only selection is a routing failure; add a domain specialist"]}`.

### 5.2 RSaver (14 tools)

- **`rsaver_measure`** — inline profile `generic`: `total_estimate=13`, `chars_over_4=13`, legacy 15, `exact=null`, `exact_source="not requested"` (honest about estimate-only mode). File mode with `openai-o200k`: 35-line fixture measured 337 each, total 674.
- **`rsaver_select`** — windows `6-11`, `15-18`, `34-35` around `ERROR|STATUS=|sha256`; `selected_text` began `INFO compiling module gamma / ERROR: module delta failed to compile ...` and ended `build exit code 1 / ERROR final: build failed`. `omitted_ranges=[[1,5],[12,14],[19,33]]`, 68.02% estimated saving.
- **`rsaver_compact`** — input 35 lines, 344-estimate; output 10 kept lines, 100-estimate; 70.93% saved; critical pattern is the documented default; `budget_exceeded_by_critical=false`; `kept_range_sha256` for `1-1`, `7-11`, `16-17`, `34-35`; original file left unchanged (confirmed by the later successful `verify` against the original hash).
- **`rsaver_budget`** — exact arithmetic verified: `4000 - 800 - 600 = 2600` available, `2600 - 700 = 1900` item budget, 35% reserve. Negative case `window=100, output=80, reasoning=40` → `RSaver ERROR: output and reasoning reserves exceed the context window`, `exit_code=2`, surfaced as an MCP error rather than a silent wrong number.
- **`rsaver_drift`** — fixture with a command repeated 3 times, "All tests pass, work is complete.", and an "unknown ... not verified" line. Default: signals `repeated_command` (lines 3,5,7), `completion_claim_with_open_unknowns`, `unlabeled_confidence_claim`. `recent_window=3`: additionally `objective_absent_from_recent_window` and `constraint_absent_from_recent_window`. Each output carries `diagnosis: "NOT VERIFIED: signals are heuristics, not a model state diagnosis"`.
- **`rsaver_crosscheck`** — PASS case: all four checks (`required_edits`, `scope_boundary`, `test_result`, `claim_consistency`) `pass`; usage parsed as `input_tokens=1000`, `cached_tokens=400`, `reasoning_tokens=50`, `billing_effect="NOT CHANGED by RSaver"`. FAIL case: `test_result=fail`, `claim_consistency=fail`, verdict `FAIL` — proving the tool distinguishes outcomes instead of always reporting success.
- **`rsaver_gate`** — 4000-token envelope: `input_estimate=2350`, `cacheable_prefix_estimate=1000`, `headroom=250`, all 4 items kept, 0 deferred, static prefix contiguous and cache eligible. Under `window_tokens=1000`, history deferred and two warnings emitted.
- **`rsaver_anchor`** — inline state produced explicit IDs and a mirrored closing block; `estimate=304`, `max_tokens=400`, `warnings=[]`. With `max_tokens=50` the tool still produced the block but warned `anchor_exceeds_budget` (does not silently truncate).
- **`rsaver_reanchor`** — inserted `rsaver-anchor-start` (prefix/static/required) and `rsaver-anchor-end` (tail/dynamic/required), re-ran the gate, deferred the `answer` item, `deferred_count=1`, and preserved the `reanchor_then_gate` method label.
- **`rsaver_dedupe`** — 9 identical long non-critical lines collapsed into one collision-free marker `[RSaver: 9 identical non-critical line(s) collapsed; original lines 2-6,9-13]`; `original_estimate=211`, `deduped_estimate=62`, `saved_percent=70.62`; `critical_lines_preserved=[7,8]`.
- **`rsaver_pack`** — `zlib`: `original_chars=2171`, `compressed_chars=208`, `481→80` estimate, `saved_percent=83.37`, `method=zlib9_base64_roundtrip`. `dict`: `481→101`, `saved_percent=79`, `method=frequency_dict_zero_dup`, with dictionary and block/inline-repeat records. Both `worthwhile=true`.
- **`rsaver_unpack`** — both pack manifests restored `2171` chars with `verified=true`; see §6.

---

## 6. RSaver integrity and recovery verification

### 6.1 Compaction manifest and verification

MCP `rsaver_compact` returned the full manifest inline in its JSON result. Key fields:

- `original_sha256 = 8780470cedc895aecf5590115180bfe17f3b127fd35595c536c8a3aa1339b315`
- `original_lines = 35`, `kept_ranges = [[1,1],[7,11],[16,17],[34,35]]`
- `omitted_ranges = [[2,6],[12,15],[18,33]]`
- `critical_lines = [7,8,9,10,11,16,17,34,35]`
- estimate: `344 → 100`, saved `244`, `70.93%`

That manifest was persisted as `.mcp-live-test/compact-manifest.json` and then passed **back into the MCP connection**:

- `rsaver_verify({manifest:".mcp-live-test/compact-manifest.json"})` → `exit_code=0`, `ok=true`, stdout: `RSAVER VERIFY PASS: /root/RCoder-Skills/.mcp-live-test/sample.log critical lines and range hashes intact`.
- Control: `.mcp-live-test/compact-manifest-tampered.json` (only `original_sha256` zeroed) → MCP error carrying `exit_code=1`, stderr `RSAVER VERIFY FAIL: original content hash does not match the manifest`. The integrity check is real and discriminating.

### 6.2 Range recovery — byte-for-byte

`rsaver_recover` was called for all three omitted ranges. Each returned text was compared byte-for-byte with the corresponding lines of the original fixture:

| Range | Chars | Byte-identical |
|---|---|---|
| `2:6` | 123 | **YES** — `$ npm run build` … `INFO compiling module gamma` |
| `12:15` | 102 | **YES** — `INFO retrying build` … `INFO compiling module gamma` |
| `18:33` | 425 | **YES** — `INFO compiling module epsilon` … `===== summary =====` |

All three comparisons returned `true`; the exact returned strings matched the fixture lines with no rewriting or normalization. Combined with `verify`, every omitted range is provably recoverable and every kept range hash is intact.

### 6.3 Pack / unpack — byte-for-byte

Both MCP `rsaver_pack` results carried `original_sha256 = 2c7f38ce9baf44fd4c5ec1dc2099b0497916dfea67ada865c71f26762235e7ac`, `original_chars=2171`. The manifests were persisted (`.mcp-live-test/pack-zlib.json`, `pack-dict.json`) and passed to MCP `rsaver_unpack`:

- `zlib9_base64_roundtrip`: `ok=true`, `verified=true`, 2171 chars, byte-identical to the original inline text.
- `frequency_dict_zero_dup`: `ok=true`, `verified=true`, 2171 chars, byte-identical to the original inline text (dictionary + block + inline-repeat records all applied correctly).

### 6.4 Deduplication and crosscheck integrity

- Dedupe preserved the two critical lines (`ERROR: build failed`, `STATUS=1`) and reduced the estimate by 70.62% with a collision-free marker.
- Crosscheck produced the correct opposite verdicts for clean and failing artifacts (`PASS` vs `FAIL`) including claim-consistency detection.

---

## 7. Failed, unavailable, or partially tested functionality

**No normal-path tool invocation failed. No tool was unavailable. No tool was left uninvoked.**

Intentional negative tests produced the expected failures (these are evidence of correct behavior, not test failures):

- Tampered compaction manifest → `rsaver_verify` returned FAIL (`exit_code=1`).
- Invalid budget reserves → `rsaver_budget` returned `exit_code=2` with a precise message.
- Path outside server root (`../../etc/passwd`) → `rsaver_select` refused with `path is outside the server root (--root); refusing`.
- Over-budget gate/anchor → warnings emitted rather than silent truncation.

Not exercised in this session (and therefore **NOT TESTED**, outside the 21-tool scope):

- MCP **resources** (`rcoder://skill`, `rcoder://specialist/{name}`, `rcoder://template/{name}`), **prompts** (`rcoder_route`, `rcoder_verify`, etc.), and `completion/complete`. Only the tool surface was in scope.
- Host-side native skill discovery / automatic session-start hook execution.
- Other RSaver profiles (`openai-cl100k`, `gpt2`, `cjk-native`), `--exact` tokenizer mode (no `tiktoken` requested), and Windows/macOS hosts.
- Provider billing effects (explicitly out of scope; RSaver reports "NOT CHANGED by RSaver").
- `rcoder_scan` against a different repository root.

Caveat affecting the *end-to-end chain* (not an individual tool result): `rsaver_compact` and `rsaver_pack` return their manifests **inline in JSON** and do not write manifest files to disk, because the MCP server is read-only; `rsaver_verify`, `rsaver_recover`, and `rsaver_unpack` require a **manifest file path**. The host must therefore persist the returned manifest before those tools can consume it. This test did that explicitly with controlled fixtures. The individual tools are PASS; the handoff is an integration gap documented in §9.

---

## 8. Overall test summary

| Status | Count |
|---|---|
| PASS | **21** |
| PARTIAL | 0 |
| FAIL | 0 |
| NOT TESTED | 0 |

All 21 RCoder MCP tools were discovered from the live OpenCode session, invoked through the MCP connection with schema-valid arguments, and evaluated against real responses. RSaver compaction verification, three-range recovery, two pack/unpack round-trips, dedupe preservation, drift/crosscheck discrimination, budgeting and anchoring were all functionally verified, including byte-for-byte equality checks. The acceptance criteria are met.

---

## 9. Remaining integration issues and recommended fixes

1. **Manifest handoff gap (highest impact).** `compact`/`pack` emit manifests inline, while `verify`/`recover`/`unpack` accept only file paths. A host cannot complete a recoverable reduction loop using MCP tools alone. Recommended fix: add inline-manifest variants (e.g. `verify_inline`, `unpack_inline`, `recover_inline` taking JSON text) or an explicitly host-mediated, documented manifest-persistence step. No source changes were made during this test.
2. **Inconsistent output shape.** `rsaver_verify` returns plain stdout text because the MCP handler does not pass `--json`, unlike the other RSaver tools. Recommended fix: add `--json` to that handler for structured, parseable results.
3. **Tool-schema token cost.** The full 21-tool schema set is roughly 3,470 estimated tokens (per `docs/MCP.md`) on every request. For routing-only sessions, configure the server with `--profile minimal` / `--tools` allowlist; keep full profile when RSaver operations are needed.
4. **Root confinement.** All paths must reside under `--root` (`/root/RCoder-Skills`); logs placed in `/tmp` or elsewhere cannot be read through these tools. Workaround: stage fixtures inside the project root (as done here) or start a separate server instance with an appropriate root.
5. **Feature-flag location.** `rcoder_doctor` reported `features: null` while `.agents/.rcoder-features.json` exists in the tree. Recommended check: confirm the installer writes the flags where the server expects them; this does not affect tool behavior.
6. **"Connected" is not proof.** This report demonstrates why a connection badge is insufficient: a CI smoke test should call `rcoder_doctor` plus at least one representative tool from each family and assert on returned fields (as done here).
7. **Estimates are relative.** All token figures are deterministic heuristics (`content_class_pretoken_heuristic_v2`), not provider billing or exact counts; use a real tokenizer when exact counts are required.

Report path: `docs/RCODER-MCP-LIVE-TEST-REPORT-tested-by-Hy4-flash-Free.md`.
