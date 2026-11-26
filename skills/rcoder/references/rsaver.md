# RSaver: evidence-preserving context reduction

## Activate when
A context or tool output is too large for the next step; repeated output dominates a prompt; a long session approaches compaction; an agent must measure relative context cost before deciding what to load. Do not activate to rewrite source code, to drop verification, or to make billing or hard context-window decisions.

## Mission and expertise
Reduce context size with structure-preserving pruning and recoverable externalization. An opt-in optimizer may tighten a small allowlist of phrases in natural-language prose only; it never paraphrases evidence or rewrites source files. Code, structured data, logs, Markdown syntax, normative constraints, and verification evidence remain verbatim. Own relative-size measurement, bounded selection, deduplication economics, and recoverable manifests.

## Mental model
Context is a finite attention budget; as it grows, recall of mid-context evidence degrades. Pruning removes content while leaving retained evidence byte-for-byte intact, which is safer for code and traces than summarization. Externalization plus a retrieval manifest gives high compression with recoverability; the main risk becomes failing to retrieve what was omitted. Token figures from RSaver are deterministic relative estimates, not model-specific counts.

Evidence from the research base: official token-counting guidance states that `characters / 4` and similar heuristics are approximations and that model-specific tokenizers or counting endpoints are required for exact counts; context-engineering guidance identifies tool-result clearing and just-in-time bounded retrieval as the safest low-touch reductions; compression surveys classify information loss and access failure as the dominant failure modes and recommend structure-aware pruning for coding agents.

## Tokenization findings that drive v2

- Byte-level BPE first splits text with a pre-tokenizer regex; merges never cross chunk boundaries. A leading space belongs to the following word, so `" hello"` and `"hello"` can be different tokens. Each chunk costs at least one token.
- `cl100k_base` and `o200k_base` group digits in chunks of at most three, while GPT-2 groups longer digit runs. This is why a flat character divisor fails badly on numbers.
- BPE vocabularies are trained mostly on natural language. Measurements on one open model put tokens per character at roughly 0.20 for English prose, 0.30 for non-English Latin text, 0.34 for code, 0.46 for JSON, and 0.97 for digit-heavy data. CJK and emoji also diverge sharply from English ratios.
- Cross-model comparisons show that vocabulary *allocation* matters more than size; a single "chars per token" constant cannot track code, JSON, numbers, CJK, and prose at once.
- Spacing and identifier changes in otherwise identical code can shift token boundaries and model behavior, so RSaver never rewrites retained code or traces.

Calibration note: on a seven-sample in-repository research fixture, an oracle built from public tiktoken encoding files gave aggregate absolute errors of about 15% for `chars/4`, 13% for the legacy v1 heuristic, and 7.5% for the v2 `openai-o200k` profile; the generic v2 profile was about 13%. Pre-tokenization was approximated with standard-library regex, so these are calibration signals, not a benchmark or a guarantee for any model. Exact mode is always preferred when a real counter is available.

## Prerequisites and reconnaissance
1. Confirm what the next decision actually needs: a symbol, an error, a status line, or a full file. Do not compress code you are about to edit.
2. Record the source path and its hash; RSaver manifests include the original SHA-256 for this purpose.
3. Define the critical-evidence pattern for the task. The default covers errors, failures, exit/status codes, hashes, URLs, and evidence labels; extend it when the task has domain-specific must-keep lines.
4. Decide the budget in lines and whether omitted ranges must remain retrievable.

## Procedure
1. Measure first: `python3 <skill-dir>/scripts/rsaver.py measure <absolute-file-paths> --json`.
1a. For natural-language prose or Markdown paragraphs, optionally run `rsaver optimize FILE --type auto --json`; review the optimized copy and its estimates. The source file is never modified. It only applies allowlisted phrase tightening, skips Markdown structure and constraint/evidence lines, and retains the original when estimated savings are not positive.
2. For a known symbol, extract a bounded window: `rsaver select FILE --match 'SYMBOL|ERROR' --context 2 --max-lines 120`.
3. For verbose output, prune non-critical lines to 80%+ savings: `rsaver compact FILE --target-savings 80 --critical '<pattern>' --manifest manifest.json --verify`.
4. For repetitive lines, words, or command blocks, collapse them:
   - Command/terminal blocks: `rsaver dedupe FILE --blocks --json` (90%+ savings on repeating command runs).
   - Frequent words/phrases: `rsaver dedupe FILE --words --json` (replaces duplicate words with a collision-free zero-cost reference).
   - Readable dictionary compression: `rsaver pack FILE --method dict --json` (unpacked losslessly via `rsaver unpack`).
   - Template/timestamped logs: `rsaver dedupe FILE --normalize --json`.
5. Inspect the reported saved estimate and saved percent. If savings are zero, keep the original context; reduction must not add text.
6. Recover anything needed later with `rsaver recover --file FILE --range START:END` or `rsaver unpack --manifest manifest.json`, then re-read the original with the agent's bounded read tool.
7. Verify integrity before trusting a compacted artifact: `rsaver verify --manifest manifest.json`.
8. Before pasting logs, configs, or transcripts into a shared context, issue, or report, mask credentials: `rsaver redact FILE --fail-on-found --json`. Redaction is lossy by design, so keep the original private and never treat a clean result as proof that no secret remains.
9. Record original estimate, reduced estimate, critical lines preserved, omitted ranges, and the verification status in the working ledger; `rsaver ledger report --ledger PATH` (or the read-only MCP tool `rsaver_ledger`) shows cumulative savings.

## Decision tree
- Text may contain credentials and will leave the machine or enter a shared context → `redact` first (MCP: `rsaver_redact`); never compact or pack unredacted secrets into a shared artifact.
- Need one symbol or error → `select`, not `compact`.
- Need to shorten plain prose → `optimize`; keep code, structured data, logs, and requirement-heavy text unchanged. For repetitive output use `dedupe` or `compact` instead.
- Repeating command executions (PS/CMD/Terminal) → `dedupe --blocks` (first run verbatim, repeats collapsed).
- Repeating phrases, conversational terms, or frequent words → `dedupe --words` or `pack --method dict`.
- Output is a repeating or timestamped log → `dedupe --normalize` first; if still large, `compact --target-savings 80` with a critical pattern.
- File is source code to edit → read bounded ranges directly; do not prune code.
- Critical lines exceed the line budget → RSaver keeps them all and reports `budget_exceeded_by_critical`; raise the budget or split the task.
- Exact model count is required → use the model's own tokenizer or counting endpoint; RSaver estimates are not sufficient.
- Omitted evidence may be needed later → require a manifest and verify it; without recovery, the reduction is not acceptable.
- Verification fails → discard the compacted artifact and use the original.

## Tool strategy
In this module, `rsaver` is shorthand for `python3 <skill-dir>/scripts/rsaver.py` (or the `rsaver_*` MCP tools when available). That canonical location is bundled with the installed skill; `scripts/rsaver.py` is only a repository-root wrapper. It is a dependency-free Python 3 standard-library CLI with subcommands `measure`, `compare`, `optimize`, `select`, `compact`, `dedupe`, `audit`, `redact`, `ledger`, `recover`, and `verify`. `redact` masks credential-shaped values (private-key blocks, cloud and GitHub tokens, JWTs, bearer tokens, URL credentials, password/token assignments) with numbered placeholders before text enters a context or a report; it is deliberately lossy, preserves line numbering, never stores or hashes the secret, is best-effort pattern matching that can miss unusual secrets, and `--fail-on-found` makes it usable as a gate. `ledger record|report` (or `--ledger PATH` on `compact` and `dedupe`) keeps a cumulative, atomically written JSON record of estimated savings that rolls old entries into totals. Run `rsaver audit --root .` once at session start on an unfamiliar repository: it ranks files by estimated token cost, groups them by category, flags lockfiles, minified or generated files, logs, and data files that are rarely worth loading whole, and prints the reduction command to use for each. It is read-only, bounded (`--max-files`, `--max-read-bytes`), skips dependency trees, symlinks, binaries, and credential files, and never prints file contents. It works on files and stdin (`-`) and emits human-readable output by default or structured JSON with `--json`.

Two estimators are available. `dependency_free_run_heuristic_v1` is retained for reproducibility of older manifests. `content_class_pretoken_heuristic_v2` is the default: it first splits text with a GPT-style pre-tokenizer approximation (contractions, letter runs with an optional leading delimiter, 1-3 digit groups, symbol runs, whitespace/newline runs, special tokens), then charges a rate per class for ASCII words, non-ASCII Latin words, CJK/Kana/Hangul characters, emoji, symbols, and digits. Profiles (`generic`, `openai-cl100k`, `openai-o200k`, `gpt2`, `cjk-native`) change those rates; choosing the profile that matches the model matters more than the raw divisor.

For actual exactness, `measure --exact` uses an installed `tiktoken` when present, and `--tokenizer-command '<command>'` pipes text to any external counter and reads the integer result. The command runs through the local shell, so pass only a command you trust. Neither path is required for installation; when unavailable, RSaver reports that explicitly. `compare` prints v1, v2, `chars/4`, exact when available, and percentage error so a team can calibrate a profile before trusting estimates. For maximal safe reduction, `pack` emits a hash-verified compressed form only when its estimate is lower and `unpack` restores the exact original. `crosscheck` verifies a completion claim against diff/test artifacts and records provider usage without changing billing; see `rsaver-crosscheck.md` and `docs/BILLING-AND-CROSSCHECK.md`.

## Advanced techniques
- **Evidence-first budgets:** choose the critical pattern from the decision's must-keep evidence, then set the line budget; never the reverse.
- **Range recovery:** manifests store 1-based inclusive kept and omitted ranges; `recover` prints exact original lines so no interpretation is introduced.
- **Hash-checked retention:** each kept range has a SHA-256; `verify` recomputes original hashes and detects any change or missing critical line.
- **Dedupe economics:** a collapse marker is emitted only when it costs fewer estimated tokens than the duplicates it removes, avoiding negative savings.
- **Tool-result clearing:** for deep histories, keep the final result and error lines and prune intermediate successful output; retain a manifest.
- **Progressive disclosure:** measure before loading, select exact symbols, and compact only the remainder; combine with `context_snapshot.py` for repository discovery.

## Failure modes
- **Pruning code before editing** → lost context and wrong edits → read source directly in bounded ranges.
- **Treating estimates as exact counts** → bad budget decisions → label as estimates and use a real tokenizer when exactness matters.
- **Dropping an unrecognized critical line** → evidence loss → widen the critical pattern, verify, and recover from the manifest.
- **Markers that cost more than duplicates** → context growth → RSaver's economics check prevents this; if savings are zero, keep the original.
- **Manifest lost or mismatched** → F3 access failure → regenerate the artifact and verify against the original.

## Quality checklist
- [ ] Measurement was taken before reduction and reported with its method.
- [ ] Retained lines are verbatim and every omitted range is in the manifest.
- [ ] All critical lines are present and `rsaver verify` passes.
- [ ] Savings are positive; otherwise the original was kept.
- [ ] No verification, authorization, or safety evidence was pruned.

## Anti-patterns
Summarizing code or stack traces; using RSaver numbers for billing or hard limits; compacting without a recovery manifest; pruning security evidence to improve the percentage; emitting duplicate markers that increase size; claiming token savings without before/after numbers.

## Verification
Run `python3 scripts/test-rsaver.py` for the CLI contract. For a real artifact, compare the manifest estimates, confirm critical lines are preserved, run `rsaver verify`, and recover at least one omitted range to confirm it reproduces the original exactly. Record exact commands and outputs.

## Output format
Objective · critical pattern · original/reduced estimates and percentage · critical lines preserved · omitted ranges and manifest path · verify result · recovered sample · residual risks.

## Executable Verification & Failure Diagnostics
- **Verify**: Run `python3 scripts/test-rsaver.py` for the CLI contract.
- **Anti-Patterns**: Summarizing code or stack traces; using RSaver numbers for billing or hard limits
- **Failure Diagnostics**: A failing or ambiguous Verify result -> the first failing assertion or error line is the root cause, not the completion summary -> python3 scripts/test-rsaver.py.
