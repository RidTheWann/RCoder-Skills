# RCoder MCP — Live Integration Test Report

## Live test status

**SUCCESS.** All 21 RCoder MCP tools were invoked through the live MCP connection and returned verified results.

| Status | Count |
|---|---:|
| PASS | **21** |
| PARTIAL | 0 |
| FAIL | 0 |
| NOT TESTED | 0 |

- **Test date:** 2026-11-22
- **Repository:** `/root/RCoder-Skills`
- **RCoder MCP server:** `1.14.0`
- **RSaver:** `1.11.0`
- **Scope:** the 21 MCP tools. MCP resources, prompts, completion, and host-side configuration were not part of this test.

Two independent live runs are combined below. **Run 1** is the previously committed test evidence; **Run 2** is the fresh verification run. Both returned PASS for all 21 tools. Run 2 adds independent SHA-256 byte-for-byte checks, tamper controls, and a bounded-scan check.

No tool was marked PASS without an actual invocation. No result was simulated or substituted with local script output. Local shell commands were used only to create controlled fixtures under `.mcp-live-test/fresh/` and to compute independent hashes for comparison.

---

## 1. Combined tool results

| # | Tool | Status | Run 1 evidence | Run 2 evidence |
|---|---|---|---|---|
| 1 | `rcoder_doctor` | **PASS** | `server_version=1.14.0`, `reference_count=61`, `enabled_tools=all` | Same metadata; helpers `rscan`, `rsaver`, `context_snapshot`, `detect_stack`, `tool_probe` all `true`; `features=null` |
| 2 | `rcoder_scan` | **PASS** | `max_paths=80` → 6 ranked options: `FINISH_CHANGE` 90, `QUALITY_GATES` 85, `DEPENDENCY_SECURITY` 80, `SECURITY_REVIEW` 75, `ONBOARD` 70, `REFACTOR` 50 | `max_paths=80` → same option set; `max_paths=300` → `quality.ci=true`, `no_ci` absent, 6 options including `PERFORMANCE` 45 |
| 3 | `rcoder_detect_stack` | **PASS** | `package.json`; `JavaScript / TypeScript (Node.js)`; quality entries `AGENTS.md`, `CLAUDE.md`, `.github/workflows` | Same manifests, stack, and quality entries |
| 4 | `rcoder_context_snapshot` | **PASS** | `max_paths=40`, `max_depth=2`; bounded paths, Git state, `truncated=true`, `source_contents_included=false` | Same limits; 40 `file_paths`, 4 key files, Git branch `live-testing`, no source contents |
| 5 | `rcoder_list_specialists` | **PASS** | 61 modules; query `test` → 2 ranked candidates (`test-engineering` 9, `testing-qa` 9) | Same; `category=project-local` → 0 modules |
| 6 | `rcoder_get_specialist` | **PASS** | `coding` with `Procedure` + `Verification`; `rsaver` with `Verification` | `coding` returned exactly the two requested sections; unknown name returned a clean error |
| 7 | `rcoder_validate_selection` | **PASS** | Valid `coding` + `rsaver` + `verification`; helper-only `rsaver` + `rsaver-gate` rejected | Valid `coding` + `testing-qa` + `rsaver` + `verification` → `valid=true`; helper-only case → two precise errors |
| 8 | `rsaver_measure` | **PASS** | Inline text → estimate 13, chars/4 13, v1 15; two files → 337 + 337 = 674, 35 lines | Inline text → estimate 4, chars/4 6, v1 7; two files → 262 + 57 = 319, 40 and 10 lines |
| 9 | `rsaver_select` | **PASS** | Kept `[[6,11],[15,18],[34,35]]`, 68.02% saved; path escape refused | Kept `[[23,25],[33,37]]`, omitted `[[1,22],[26,32],[38,40]]`, 75% saved; 234 chars hash-identical to the expected ranges |
| 10 | `rsaver_compact` | **PASS** | 344 → 100 estimate, 70.93% saved; kept `[[1,1],[7,11],[16,17],[34,35]]`; omitted `[[2,6],[12,15],[18,33]]`; original unchanged | 264 → 77 estimate, 70.83% saved; kept `[[1,3],[24,24],[34,36],[38,39]]`; omitted `[[4,23],[25,33],[37,37],[40,40]]`; 268 chars hash-identical to kept ranges |
| 11 | `rsaver_budget` | **PASS** | `4000/800/600/700` → `available_input=2600`, `item_budget=1900`, `reserve_percent=35`; invalid reserves → `exit_code=2` | Same arithmetic; same clean error on invalid reserves |
| 12 | `rsaver_drift` | **PASS** | Default → 3 signals; `recent_window=3` → 4 signals including objective/constraint loss; diagnosis labeled `NOT VERIFIED` | `recent_window=3` → 4 signals; default 12-line window → 3 signals including `repeated_command` |
| 13 | `rsaver_crosscheck` | **PASS** | Good artifacts → `verdict=PASS` (4 checks pass); failing test log → `verdict=FAIL` (`test_result` and `claim_consistency` fail) | Same PASS/FAIL discrimination; usage fields parsed (input 1000, output 200, cached 400, reasoning 50) |
| 14 | `rsaver_gate` | **PASS** | `projected_total=3750/4000`, `headroom=250`, `cache.eligible=true`, `contiguous_static_prefix=true`, 0 deferred; small window emitted budget warnings | Same normal result; 1000-token envelope → `projected_total=1550/1000`, `headroom=-550`, 2 deferred, `required_items_exceed_budget` |
| 15 | `rsaver_anchor` | **PASS** | Dual-end block with `[OBJECTIVE-1]`, 3 constraints, 2 facts, decision/unresolved, `[NEXT-ACTION]`; `estimate=304/400`; small budget → `anchor_exceeds_budget` | 9 explicit IDs; `estimate=293/400`, no warnings; `max_tokens=50` → estimate 126 and `anchor_exceeds_budget` |
| 16 | `rsaver_reanchor` | **PASS** | Anchor inserted at both ends; `deferred_count=1`; `projected_total=3853/4000`, `headroom=147`; cache eligible | Anchor start 197 tokens and anchor end 95 tokens; `projected_total=3842/4000`, `headroom=158`; `deferred_count=1`; cache eligible |
| 17 | `rsaver_dedupe` | **PASS** | 211 → 62 estimate, 70.62% saved; collision-free marker; critical lines `[7,8]` preserved | 193 → 109 estimate, 43.52% saved; two markers; critical lines `[5,6]` preserved; short-line control correctly declined collapse (saved 0) |
| 18 | `rsaver_recover` | **PASS** | Ranges `2:6`, `12:15`, `18:33` returned exact original lines; all byte-identical | Ranges `4:23`, `25:33`, `37:37`, `40:40` returned exact lines; all SHA-256 hashes matched; invalid `50:60` → `exit_code=2` |
| 19 | `rsaver_verify` | **PASS** | Valid manifest → PASS; tampered original hash → FAIL (`exit_code=1`) | Valid manifest → PASS; tampered original hash, tampered kept-range hash, and missing critical line each → FAIL (`exit_code=1`) |
| 20 | `rsaver_pack` | **PASS** | `zlib`: 481 → 80 estimate (83.37%), payload 208 chars; `dict`: 481 → 101 (79%); both `worthwhile=true` | `zlib`: 1031 → 416 chars, 264 → 144 estimate (45.45%); `dict`: 1031 → 539 chars, 264 → 236 (10.61%); both `worthwhile=true`; same original SHA-256 |
| 21 | `rsaver_unpack` | **PASS** | Both methods → `verified=true`, 2171 chars, byte-identical to the original | Both methods → `verified=true`, 1031 chars, SHA-256 `9e6f...e939`, byte-identical to the original |

**Combined totals: PASS 21 · PARTIAL 0 · FAIL 0 · NOT TESTED 0.**

---

## 2. Test cases and observed outputs

### 2.1 RCoder core (7 tools)

#### `rcoder_doctor()`

Both runs returned live server metadata:

```json
{
  "server_version": "1.14.0",
  "protocols": ["2025-06-18", "2025-03-26", "2024-11-05"],
  "negotiated_protocol": "2025-06-18",
  "root": "/root/RCoder-Skills",
  "skill_md": true,
  "reference_count": 61,
  "project_local_count": 0,
  "helpers": {
    "rscan": true,
    "rsaver": true,
    "context_snapshot": true,
    "detect_stack": true,
    "tool_probe": true
  },
  "features": null,
  "enabled_tools": "all"
}
```

The `note` field explicitly says server reachability is shown by the call itself; the call is the evidence.

#### `rcoder_scan`

Run 1 and Run 2 at `max_paths=80` returned six ranked options:

| ID | Priority | Triggered by |
|---|---:|---|
| `FINISH_CHANGE` | 90 | `uncommitted_changes` |
| `QUALITY_GATES` | 85 | `no_ci` |
| `DEPENDENCY_SECURITY` | 80 | `dependency_without_lock` |
| `SECURITY_REVIEW` | 75 | `security_surface` |
| `ONBOARD` | 70 | `unfamiliar_repository` |
| `REFACTOR` | 50 | `large_source_files` |

Run 2 also tested the bounded-sampling boundary. At `max_paths=80`, the scan reported:

```json
{
  "scan": {"max_paths": 80, "paths_sampled": 80, "truncated": true},
  "quality": {"agent_instructions": true, "ci": false, "lockfile": false, "readme": true, "tests": true},
  "risk_signals": [
    {"id": "uncommitted_changes", "severity": "low"},
    {"id": "no_ci", "severity": "high", "detail": "No CI workflow detected in sample"},
    {"id": "dependency_without_lock", "severity": "medium"},
    {"id": "large_source_files", "severity": "low"},
    {"id": "unfamiliar_repository", "severity": "info"}
  ]
}
```

At `max_paths=300`, it returned:

```json
{
  "scan": {"max_paths": 300, "paths_sampled": 300, "truncated": true},
  "quality": {"agent_instructions": true, "ci": true, "lockfile": false, "readme": true, "tests": true},
  "risk_ids": ["uncommitted_changes", "dependency_without_lock", "large_source_files", "benchmark_markers", "unfamiliar_repository"]
}
```

The `no_ci` signal disappeared and `ci` became `true`. This is a bounded-sampling false negative at 80 paths, not an invocation failure. The tool's wording ("in sample") and `limits` field are accurate.

#### `rcoder_detect_stack`

```json
{
  "manifests": ["package.json"],
  "candidate_stacks": ["JavaScript / TypeScript (Node.js)"],
  "quality_entry_points": ["AGENTS.md", "CLAUDE.md", ".github/workflows"],
  "notes": [
    "Read-only heuristic; verify actual commands and versions before running them.",
    "Hidden and common generated/vendor directories are skipped."
  ]
}
```

#### `rcoder_context_snapshot`

```json
{
  "root": "/root/RCoder-Skills",
  "git": {"branch": "live-testing", "status": "## live-testing...origin/live-testing"},
  "key_files": ["AGENTS.md", "CLAUDE.md", "README.md", "package.json"],
  "file_paths_count": 40,
  "truncated": true,
  "source_contents_included": false
}
```

No file contents were returned, matching the tool description.

#### `rcoder_list_specialists`

No arguments:

```json
{"count": 61}
```

`{category: "core", query: "test"}`:

```json
{
  "count": 2,
  "query": ["test"],
  "modules": [
    {"name": "test-engineering", "category": "core", "score": 9},
    {"name": "testing-qa", "category": "core", "score": 9}
  ],
  "note": "Names are the only valid selection values. ... A query only locates candidate names; it does not choose a primary."
}
```

`{category: "project-local"}`:

```json
{"count": 0, "modules": []}
```

#### `rcoder_get_specialist`

Input:

```json
{"name": "coding", "sections": ["Procedure", "Verification"]}
```

The result contained exactly two sections: `## Procedure` with 7 numbered steps and `## Verification` with the verification paragraph. `source` was `built-in`.

Negative control:

```text
{"name": "not-a-real-specialist"}
→ Error: unknown specialist; call rcoder_list_specialists for valid names
```

#### `rcoder_validate_selection`

Valid case:

```json
{
  "primary": "coding",
  "supporting": ["testing-qa", "rsaver"],
  "verifier": "verification"
}
```

Observed:

```json
{
  "valid": true,
  "errors": [],
  "warnings": [],
  "selected": ["coding", "testing-qa", "rsaver", "verification"]
}
```

Invalid helper-only case:

```json
{"primary": "rsaver", "supporting": ["rsaver-gate"]}
```

Observed:

```json
{
  "valid": false,
  "errors": [
    "helper modules (model-adaptation, rsaver, rsaver-gate, token-efficiency, verification) are supporting only and cannot be primary",
    "helper-only selection is a routing failure; add a domain specialist"
  ],
  "selected": ["rsaver", "rsaver-gate"]
}
```

### 2.2 RSaver (14 tools)

Both runs used controlled fixtures with known critical lines and known hashes. Run 2's primary fixture was a 40-line build log with SHA-256 `9e6fb3925484627c9127c6b71ea9c3717807c3367d1a5cb3ef80fe0ef733e939`.

#### `rsaver_measure`

Run 1 inline mode:

```json
{"total_estimate": 13, "files": [{"chars_over_4": 13, "v1_legacy": 15, "lines": 1}]}
```

Run 1 file mode: two 35-line files, `337` each, `total_estimate=674`.

Run 2 inline mode:

```json
{
  "files": [{"path": "-", "lines": 1, "estimate": 4, "v1_legacy": 7, "chars_over_4": 6, "exact": null, "exact_source": "not requested"}],
  "total_estimate": 4
}
```

Run 2 file mode:

```json
{
  "files": [
    {"path": ".../sample.log", "lines": 40, "estimate": 262, "chars_over_4": 258, "v1_legacy": 288},
    {"path": ".../dedupe.txt", "lines": 10, "estimate": 57, "chars_over_4": 65, "v1_legacy": 71}
  ],
  "total_estimate": 319
}
```

Arithmetic checks: `262 + 57 = 319`; `ceil(1031/4) = 258`; `ceil(259/4) = 65`. The result reports `exact: null` and `exact_source: "not requested"`.

#### `rsaver_select`

Run 1: `match="ERROR|STATUS=|sha256"`, `context=1` → kept `[[6,11],[15,18],[34,35]]`, critical lines `[7,9,10,16,17,35]`, 68.02% saved. A path outside the server root (`../../etc/passwd`) was refused.

Run 2:

```json
{
  "path": ".mcp-live-test/fresh/sample.log",
  "match": "ERROR|STATUS=|sha256",
  "context": 1,
  "max_lines": 20
}
```

Observed:

```json
{
  "kept_ranges": [[23, 25], [33, 37]],
  "omitted_ranges": [[1, 22], [26, 32], [38, 40]],
  "critical_lines": [24, 34, 35, 36],
  "budget_exceeded_by_critical": false,
  "estimate": {"original_estimate": 264, "compact_estimate": 66, "saved_percent": 75}
}
```

The returned `selected_text` was 234 characters and its SHA-256 matched the expected concatenation of lines 23–25 and 33–37:

```text
expected = a66a2c6f026c33afaa6c89f9ae7f4d6b50512922c384d3c623d100a3911a0210
actual   = a66a2c6f026c33afaa6c89f9ae7f4d6b50512922c384d3c623d100a3911a0210
```

#### `rsaver_compact`

Run 1:

```json
{
  "original_lines": 35,
  "critical_lines": [7, 8, 9, 10, 11, 16, 17, 34, 35],
  "kept_ranges": [[1, 1], [7, 11], [16, 17], [34, 35]],
  "omitted_ranges": [[2, 6], [12, 15], [18, 33]],
  "estimate": {"original_estimate": 344, "compact_estimate": 100, "saved_percent": 70.93}
}
```

Run 1 confirmed the original file was unchanged.

Run 2 input:

```json
{
  "path": ".mcp-live-test/fresh/sample.log",
  "max_lines": 14,
  "head": 3,
  "tail": 3,
  "target_savings": 70
}
```

Observed manifest (key fields):

```json
{
  "method": "structure_preserving_prune",
  "original_sha256": "9e6fb3925484627c9127c6b71ea9c3717807c3367d1a5cb3ef80fe0ef733e939",
  "original_lines": 40,
  "critical_lines": [24, 34, 35, 36],
  "kept_ranges": [[1, 3], [24, 24], [34, 36], [38, 39]],
  "omitted_ranges": [[4, 23], [25, 33], [37, 37], [40, 40]],
  "budget_exceeded_by_critical": false,
  "estimate": {
    "original_estimate": 264,
    "compact_estimate": 77,
    "saved_estimate": 187,
    "saved_percent": 70.83
  }
}
```

The returned `compacted` text was 268 characters and its SHA-256 matched the expected concatenation of the four kept ranges:

```text
expected = ee872719a2a903f4d29ce11fc2675dbe94f32ed217d2076ca97cd2a471ff9250
actual   = ee872719a2a903f4d29ce11fc2675dbe94f32ed217d2076ca97cd2a471ff9250
```

The original file's SHA-256 after all compaction tests remained `9e6fb392...e939`. The tool did not write a manifest file to disk; it returned the manifest inline.

#### `rsaver_budget`

Valid input:

```json
{"window": 4000, "output_reserve": 800, "reasoning_reserve": 600, "tool_schema": 700}
```

Observed:

```json
{
  "available_input": 2600,
  "item_budget": 1900,
  "reserve_percent": 35
}
```

Arithmetic: `4000 − 800 − 600 = 2600`; `2600 − 700 = 1900`; `(800 + 600) / 4000 = 35%`.

Negative control:

```json
{"window": 100, "output_reserve": 80, "reasoning_reserve": 40}
```

Observed:

```json
{"exit_code": 2, "ok": false, "stderr": "RSaver ERROR: output and reasoning reserves exceed the context window\n"}
```

#### `rsaver_drift`

Run 1 default window: 3 signals. `recent_window=3`: 4 signals including objective/constraint loss. Each output labeled `diagnosis: "NOT VERIFIED: signals are heuristics, not a model state diagnosis"`.

Run 2 `recent_window=3`:

```json
{
  "lines_scanned": 12,
  "recent_window": 3,
  "signal_count": 4,
  "signals": [
    {"signal": "objective_absent_from_recent_window", "severity": "high"},
    {"signal": "constraint_absent_from_recent_window", "severity": "high"},
    {"signal": "completion_claim_with_open_unknowns", "severity": "high", "lines": [11, 12]},
    {"signal": "unlabeled_confidence_claim", "severity": "low", "lines": [10]}
  ]
}
```

Run 2 default 12-line window:

```json
[
  {"signal": "repeated_command", "lines": [4, 6, 8], "command": "$ python3 scripts/test-mcp.py"},
  {"signal": "completion_claim_with_open_unknowns", "lines": [5, 7, 9, 11, 12]},
  {"signal": "unlabeled_confidence_claim", "lines": [10]}
]
```

The window tradeoff is real: the narrow window detects lost objective/constraints but excludes repeated commands; the default window detects repetition but retains the objective/constraints.

#### `rsaver_crosscheck`

Run 1 and Run 2 good artifacts:

```json
{
  "verdict": "PASS",
  "checks": [
    {"id": "required_edits", "status": "pass"},
    {"id": "scope_boundary", "status": "pass"},
    {"id": "test_result", "status": "pass"},
    {"id": "claim_consistency", "status": "pass"}
  ]
}
```

Run 2 usage fields: `input_tokens=1000`, `output_tokens=200`, `cached_tokens=400`, `reasoning_tokens=50`.

Failing test log:

```json
{
  "verdict": "FAIL",
  "checks": [
    {"id": "required_edits", "status": "pass"},
    {"id": "scope_boundary", "status": "pass"},
    {"id": "test_result", "status": "fail"},
    {"id": "claim_consistency", "status": "fail"}
  ]
}
```

The tool distinguishes a supported completion claim from a claim contradicted by test evidence.

#### `rsaver_gate`

Normal envelope (4000-token window, 800 output, 600 reasoning, 700 schema, 200 cache minimum):

```json
{
  "budget": {
    "available_input": 2600,
    "item_budget": 1900,
    "input_estimate": 2350,
    "cacheable_prefix_estimate": 1000,
    "ordinary_input_estimate": 1350,
    "projected_total": 3750,
    "headroom": 250
  },
  "cache": {"eligible": true, "contiguous_static_prefix": true},
  "deferred_count": 0,
  "warnings": []
}
```

Run 2 small envelope (1000-token window, 200 output, 100 reasoning, 700 schema):

```json
{
  "budget": {
    "available_input": 700,
    "item_budget": 0,
    "input_estimate": 1250,
    "projected_total": 1550,
    "headroom": -550
  },
  "deferred_count": 2,
  "warnings": ["required_items_exceed_budget"]
}
```

Required items were kept; `history` and `answer` were deferred with recovery pointers. Run 1's small-window test also emitted `tool_schema_exceeds_available_input` for its tighter envelope. The negative headroom is reported rather than hidden.

#### `rsaver_anchor`

Run 1 inline state: dual-end block with `[OBJECTIVE-1]`, 3 constraints, 2 facts, decision/unresolved, `[NEXT-ACTION]`; `estimate=304/400`, no warnings. With `max_tokens=50`, the block was produced with `anchor_exceeds_budget`.

Run 2 inline state:

```json
["OBJECTIVE-1", "CONSTRAINT-1", "CONSTRAINT-2", "CONSTRAINT-3", "FACT-1", "FACT-2", "DECISION-1", "UNRESOLVED-1", "NEXT-ACTION"]
```

`estimate=293`, `max_tokens=400`, `warnings=[]`. The block contained both `===== RSAVER ANCHOR START =====` and `===== RSAVER ANCHOR END =====`, with the objective, constraints, and next action mirrored at the end. Over-budget control (`max_tokens=50`) returned `estimate=126` with `anchor_exceeds_budget`.

#### `rsaver_reanchor`

Run 1: anchor inserted at both ends, `deferred_count=1`, `projected_total=3853/4000`, `headroom=147`, cache eligible.

Run 2 input files: `.mcp-live-test/fresh/envelope.json` and `.mcp-live-test/fresh/state.json`, `max_tokens=400`.

Observed:

```json
{
  "method": "reanchor_then_gate",
  "anchor": {"estimate": 293, "warnings": []},
  "gate": {
    "budget": {
      "input_estimate": 2442,
      "cacheable_prefix_estimate": 1197,
      "projected_total": 3842,
      "window_tokens": 4000,
      "headroom": 158
    },
    "cache": {"eligible": true, "contiguous_static_prefix": true},
    "deferred_count": 1,
    "warnings": []
  }
}
```

The inserted items were `rsaver-anchor-start` (197 tokens, prefix/static/required) and `rsaver-anchor-end` (95 tokens, tail/dynamic/required). The `answer` item was deferred; `history` was retained. The gate was re-evaluated after insertion.

#### `rsaver_dedupe`

Run 1: 211 → 62 estimate, 70.62% saved, 9 duplicate long lines collapsed, collision-free marker, critical lines `[7,8]` preserved.

Run 2 long-line fixture (4 identical alpha lines, 2 critical lines, 4 identical beta lines), `critical="(?i)(error|status[=:]\\s*\\d+)"`:

```json
{
  "method": "exact_duplicate_collapse",
  "critical_lines_preserved": [5, 6],
  "stats": {
    "original_estimate": 193,
    "deduped_estimate": 109,
    "saved_estimate": 84,
    "saved_percent": 43.52
  }
}
```

Returned text contained one alpha line plus `[RSaver: 3 identical non-critical line(s) collapsed; original lines 1-4]`, one beta line plus `[RSaver: 3 identical non-critical line(s) collapsed; original lines 7-10]`, and both critical lines exactly once.

A shorter-line control returned `saved_estimate: 0` and unchanged text. This is the documented economic guard: the marker would cost more than the duplicates it replaces. It is correct behavior, not a failed collapse.

#### `rsaver_recover`

Run 1 ranges `2:6`, `12:15`, `18:33` returned exact original lines; all three were byte-identical to the fixture.

Run 2 calls:

```json
[
  {"file": ".mcp-live-test/fresh/sample.log", "range": "4:23"},
  {"file": ".mcp-live-test/fresh/sample.log", "range": "25:33"},
  {"file": ".mcp-live-test/fresh/sample.log", "range": "37:37"},
  {"file": ".mcp-live-test/fresh/sample.log", "range": "40:40"}
]
```

All four returned exact lines; hashes are in §3.2.

Negative control:

```json
{"file": ".mcp-live-test/fresh/sample.log", "range": "50:60"}
→ {"exit_code": 2, "stderr": "RSaver ERROR: invalid range 50:60 for 40 lines\n"}
```

#### `rsaver_verify`

Run 1: valid manifest → `RSAVER VERIFY PASS ... critical lines and range hashes intact`; tampered original hash → `RSAVER VERIFY FAIL: original content hash does not match the manifest` with `exit_code=1`.

Run 2: valid manifest → PASS with `exit_code=0`; three tampered controls all failed correctly (see §3.3). `rsaver_verify` returns plain stdout text rather than JSON; the MCP handler does not pass `--json`.

#### `rsaver_pack`

Run 1: `zlib` 481 → 80 estimate (83.37%), payload 208 chars; `dict` 481 → 101 (79%); both `worthwhile=true`.

Run 2 inline text: the 40-line sample log, 1031 characters, SHA-256 `9e6fb392...e939`.

`method="zlib"`:

```json
{
  "method": "zlib9_base64_roundtrip",
  "original_chars": 1031,
  "compressed_chars": 416,
  "original_estimate": 264,
  "packed_estimate": 144,
  "saved_percent": 45.45,
  "worthwhile": true,
  "original_sha256": "9e6fb3925484627c9127c6b71ea9c3717807c3367d1a5cb3ef80fe0ef733e939"
}
```

`method="dict"`:

```json
{
  "method": "frequency_dict_zero_dup",
  "original_chars": 1031,
  "compressed_chars": 539,
  "original_estimate": 264,
  "packed_estimate": 236,
  "saved_percent": 10.61,
  "worthwhile": true,
  "original_sha256": "9e6fb3925484627c9127c6b71ea9c3717807c3367d1a5cb3ef80fe0ef733e939"
}
```

Both methods produced manifests with a payload; the dictionary method also produced a dictionary, block records, and inline-repeat records.

#### `rsaver_unpack`

Run 1: both manifests restored 2171 characters with `verified=true`; both were byte-identical to the original inline text.

Run 2: the two pack results were persisted as `.mcp-live-test/fresh/manifest-pack-zlib.json` and `.mcp-live-test/fresh/manifest-pack-dict.json`, then passed back into MCP:

```json
[
  {"manifest": ".mcp-live-test/fresh/manifest-pack-zlib.json"},
  {"manifest": ".mcp-live-test/fresh/manifest-pack-dict.json"}
]
```

Both returned `verified=true`, 1031 chars, SHA-256 `9e6fb392...e939`, byte-identical to the original.

---

## 3. RSaver integrity and recovery verification

### 3.1 Compaction manifest

Run 2 manifest:

| Field | Value |
|---|---|
| `original_sha256` | `9e6fb3925484627c9127c6b71ea9c3717807c3367d1a5cb3ef80fe0ef733e939` |
| `original_lines` | 40 |
| `critical_lines` | `[24, 34, 35, 36]` |
| `kept_ranges` | `[[1,3],[24,24],[34,36],[38,39]]` |
| `omitted_ranges` | `[[4,23],[25,33],[37,37],[40,40]]` |
| `kept_range_sha256` | four range hashes, all present |
| `estimate` | 264 → 77, saved 187, 70.83% |
| `budget_exceeded_by_critical` | `false` |

The manifest was persisted as `.mcp-live-test/fresh/manifest-compact.json` and passed back to MCP `rsaver_verify`. The original fixture was never modified: its joined-line SHA-256 before and after the test was `9e6fb392...e939`.

The compacted text was 268 characters and matched the expected concatenation of the kept ranges:

```text
expected = ee872719a2a903f4d29ce11fc2675dbe94f32ed217d2076ca97cd2a471ff9250
actual   = ee872719a2a903f4d29ce11fc2675dbe94f32ed217d2076ca97cd2a471ff9250
```

### 3.2 Range recovery — byte-for-byte

| Range | Chars | Expected SHA-256 | Actual SHA-256 | Byte-identical |
|---|---:|---|---|---|
| `4:23` | 518 | `dd3002a1168088ce05e53da6cd16bd288fd7784f2e65019ceff838e73652bced` | same | **YES** |
| `25:33` | 213 | `95e8afbfa3e9966eb6c3c910d4147e37c3cb7171391cefebf7178e0607c0d031` | same | **YES** |
| `37:37` | 19 | `21a832fea192f91a234e1152664ef89e87d844ab61c2aa3fc31759de9e62d3c0` | same | **YES** |
| `40:40` | 9 | `f2affe63ed62fd35c63182d2fc39edf2817868717574d903c01ab419be61683a` | same | **YES** |

The recovered text started and ended at the expected lines. No normalization, line-ending change, or whitespace rewriting was observed. Run 1's three-range recovery was also byte-identical.

### 3.3 Manifest tamper controls

| Tamper | Observed stderr | Correctly rejected |
|---|---|---|
| `original_sha256` zeroed | `RSAVER VERIFY FAIL: original content hash does not match the manifest` | **YES** |
| `kept_range_sha256["1-3"]` zeroed | `RSAVER VERIFY FAIL: kept range 1-3 content changed` | **YES** |
| Critical line 24 removed from `kept_ranges` | `RSAVER VERIFY FAIL: critical lines missing from kept ranges: [24]` | **YES** |

The valid manifest returned `RSAVER VERIFY PASS ... critical lines and range hashes intact` with `exit_code=0`. The integrity check verifies the whole original content, each kept range, and the presence of critical lines.

### 3.4 Pack / unpack — byte-for-byte

| Method | Original chars | Compressed chars | Estimate | `verified` | Restored chars | Restored SHA-256 | Byte-identical |
|---|---:|---:|---|---:|---:|---|---|
| `zlib9_base64_roundtrip` | 1031 | 416 | 264 → 144 (45.45%) | `true` | 1031 | `9e6fb392...e939` | **YES** |
| `frequency_dict_zero_dup` | 1031 | 539 | 264 → 236 (10.61%) | `true` | 1031 | `9e6fb392...e939` | **YES** |

Both manifests carried the same `original_sha256` as the source text. The dictionary method exercised the dictionary, block, and inline-repeat restoration paths; the zlib method exercised the zlib/base64 path. Run 1's two round-trips restored 2171 characters with `verified=true` and byte-identical content.

### 3.5 Deduplication integrity

- Run 1: 211 → 62 estimate, 70.62% saved, 9 duplicate long lines collapsed, collision-free marker, critical lines `[7,8]` preserved.
- Run 2 long-line fixture: 193 → 109 estimate, 84 saved (43.52%), two collision-free markers, critical lines `[5,6]` preserved exactly once.
- Run 2 short-line control: no collapse, `saved_estimate=0`; the tool declined to replace duplicates with a marker that would cost more.
- No marker collision was observed; the markers named the original line ranges.

### 3.6 Select / compact exactness

| Operation | Returned chars | Expected SHA-256 | Actual SHA-256 | Byte-identical |
|---|---:|---|---|---|
| `rsaver_select` ranges `[23,25],[33,37]` | 234 | `a66a2c6f026c33afaa6c89f9ae7f4d6b50512922c384d3c623d100a3911a0210` | same | **YES** |
| `rsaver_compact` kept ranges `[1,3],[24,24],[34,36],[38,39]` | 268 | `ee872719a2a903f4d29ce11fc2675dbe94f32ed217d2076ca97cd2a471ff9250` | same | **YES** |

Both reduction tools copy retained lines verbatim rather than regenerating or normalizing them.

---

## 4. Limitations and residual issues

1. **Manifest handoff gap.** `rsaver_compact` and `rsaver_pack` return their manifests inline in the JSON result and do not write manifest files to disk. `rsaver_verify`, `rsaver_recover`, and `rsaver_unpack` require a manifest file path. A host must persist the inline manifest before those tools can consume it. This test did so explicitly with controlled fixtures.
2. **`rsaver_verify` output shape.** It returns plain stdout text because the MCP handler does not pass `--json`; the other RSaver tools return structured JSON. A caller must parse text for this one tool.
3. **Bounded scan sampling.** At `max_paths=80`, `rcoder_scan` did not reach `.github/workflows/quality.yml` and emitted a high-severity `no_ci` signal. At `max_paths=300`, `ci` was `true` and `no_ci` disappeared. The tool is honest that the result is sample-based, but the default cap can produce misleading high-severity risk signals in repositories with large early-sorted directories.
4. **Feature-flag location.** `rcoder_doctor` reported `features: null` while `.agents/.rcoder-features.json` exists. The server checks `/root/RCoder-Skills/.rcoder-features.json`. This does not affect tool behavior but may confuse installation diagnostics.
5. **Dedupe economics.** Short duplicate lines are not collapsed because the marker costs more than the duplicates. This is intentional, but users expecting deduplication of short repeated lines may see no savings.
6. **Gate cache eligibility vs. budget.** In the small-window test, `cache.eligible` remained `true` while `headroom` was `-550`. Cache eligibility is a separate property of the static prefix; the budget warning is the signal that the plan does not fit.
7. **Compaction tail is a candidate, not a guarantee.** With `tail=3` and `target_savings=70`, the compactor kept lines 38–39 and omitted line 40 because the savings target constrained the kept set. The manifest records exactly what was kept, so recovery is unaffected.
8. **Drift window tradeoff.** `recent_window=3` detects lost objective/constraints but does not see repeated commands earlier in the transcript. The default 12-line window detects repeated commands but keeps the objective/constraints in view. Neither window detects everything; the tool labels its output as heuristic.
9. **Root confinement.** All path arguments must resolve inside `/root/RCoder-Skills`. Fixtures placed in `/tmp` or outside the root cannot be read through these tools. This is a security feature, but it constrains test staging.
10. **Relative estimates.** All token figures are deterministic heuristics (`content_class_pretoken_heuristic_v2`), not exact tokenizer counts. `rsaver_measure` reported `exact: null` because no tokenizer was requested.
11. **Out of scope.** MCP resources, prompts, completion, and host-side configuration were not tested. The report covers the 21-tool surface only.

---

## 5. Overall summary

| Status | Count |
|---|---:|
| PASS | **21** |
| PARTIAL | 0 |
| FAIL | 0 |
| NOT TESTED | 0 |

All 21 RCoder MCP tools were invoked through the live MCP connection and evaluated against real responses in two independent runs. RSaver measurement, bounded selection, compaction, budgeting, drift detection, crosschecking, gating, anchoring, re-anchoring, deduplication, range recovery, manifest verification, and both pack/unpack methods were exercised.

The live test succeeded. The acceptance criteria are met:

- All 21 tools were invoked through the actual MCP connection.
- All results were evaluated, including negative controls.
- RSaver recovery and integrity were verified byte-for-byte.
- No result was fabricated or substituted with local script output.
- This report is the consolidated, watermark-free evidence record.

The main caveat affecting a reported tool result is the bounded-scan behavior of `rcoder_scan` at 80 paths, documented in §4.3. It is a sampling limitation, not an invocation failure.

---

## 6. RCoder-specific follow-ups

1. **Close the manifest handoff gap.** Add inline-manifest variants to `rsaver_verify`, `rsaver_recover`, and `rsaver_unpack` (accepting JSON text), or document an explicit host-mediated persistence step. The server is read-only by design, so an inline input path is the least invasive fix.
2. **Return structured JSON from `rsaver_verify`.** Pass `--json` in the MCP handler and include a `verified` boolean plus problems/evidence fields.
3. **Improve bounded scan sampling.** Prioritize `.github/workflows/`, manifests, lockfiles, and agent-instruction files before walking large directory trees, or label risk signals as sample-only when `truncated=true`.
4. **Clarify feature-flag location.** Either write `.rcoder-features.json` at the server root or have `rcoder_doctor` also check `.agents/.rcoder-features.json`.
5. **Document the dedupe marker threshold.** State that short duplicate lines may not be collapsed because the marker is not economical.
6. **Separate cache eligibility from budget fit.** Add a `projected_exceeds_window` warning when `headroom < 0`, or rename `cache.eligible` to make clear it only describes the static prefix.
7. **Document that `tail` is a candidate set.** Make clear that `head`/`tail` lines may be dropped to satisfy `target_savings` or `max_lines`.
8. **Document drift window behavior.** Explain that `recent_window` controls which signals are visible: narrow windows catch lost objectives, wider windows catch repetition.

Report path: `docs/RCODER-MCP-LIVE-TEST-REPORT.md`.


## Follow-up scope boundary (2026-11-23)

The 21-tool results above are preserved as the historical live stdio run (2026-11-22). They do not cover the subsequently added `rsaver_redact` and `rsaver_ledger` tools, the stateless modern protocol, the shared pagination contract, or the optional Streamable HTTP adapter. Those changes have deterministic local conformance tests; they are not a replacement for a fresh native-host live run.

Required follow-up evidence before a 2.0 release:

1. Connect a real supported client to the HTTP adapter on loopback using an ephemeral token and the exact Origin allowlist; verify `server/discover`, paginated list calls, structured tool results, inline Skills manifest and a tool call.
2. Invoke all 24 tools in a live MCP connection, including both new RSaver tools, and retain raw request/response evidence with secrets removed.
3. Repeat the stdio tests against the same commit, recording host/client version and MCP protocol revision.
4. Run the with/without-RCoder ablation on the frozen English control and a separate multilingual dataset; retain both arms and scorer output. Do not merge multilingual results into the English control.
5. Update `docs/COMPATIBILITY.md` only for host tiers directly observed. CI and scripted clients prove protocol conformance, not native host discovery or behavioral improvement.

Status: local protocol tests can be VERIFIED by CI; native-host HTTP activation, the fresh all-24-tools live run, and post-change ablation remain NOT VERIFIED until executed in the target host runtime.
