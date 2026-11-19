# RSaver: evidence-preserving context reduction

## Activate when
A context or tool output is too large for the next step; repeated output dominates a prompt; a long session approaches compaction; an agent must measure relative context cost before deciding what to load. Do not activate to rewrite source code, to drop verification, or to make billing or hard context-window decisions.

## Mission and expertise
Reduce context size with structure-preserving pruning and recoverable externalization, never with lossy paraphrasing of evidence. Own the measurement of relative size, the selection of bounded line ranges, the deduplication economics check, and the manifest that makes every omitted range recoverable and verifiable.

## Mental model
Context is a finite attention budget; as it grows, recall of mid-context evidence degrades. Pruning removes content while leaving retained evidence byte-for-byte intact, which is safer for code and traces than summarization. Externalization plus a retrieval manifest gives high compression with recoverability; the main risk becomes failing to retrieve what was omitted. Token figures from RSaver are deterministic relative estimates, not model-specific counts.

Evidence from the research base: official token-counting guidance states that `characters / 4` and similar heuristics are approximations and that model-specific tokenizers or counting endpoints are required for exact counts; context-engineering guidance identifies tool-result clearing and just-in-time bounded retrieval as the safest low-touch reductions; compression surveys classify information loss and access failure as the dominant failure modes and recommend structure-aware pruning for coding agents.

## Prerequisites and reconnaissance
1. Confirm what the next decision actually needs: a symbol, an error, a status line, or a full file. Do not compress code you are about to edit.
2. Record the source path and its hash; RSaver manifests include the original SHA-256 for this purpose.
3. Define the critical-evidence pattern for the task. The default covers errors, failures, exit/status codes, hashes, URLs, and evidence labels; extend it when the task has domain-specific must-keep lines.
4. Decide the budget in lines and whether omitted ranges must remain retrievable.

## Procedure
1. Measure first: `python3 scripts/rsaver.py measure <paths> --json`.
2. For a known symbol, extract a bounded window: `rsaver select FILE --match 'SYMBOL|ERROR' --context 2 --max-lines 120`.
3. For verbose output, prune non-critical lines: `rsaver compact FILE --max-lines 120 --critical '<pattern>' --manifest manifest.json --verify`.
4. For exact repeated lines, collapse them: `rsaver dedupe FILE --json`; RSaver only emits a marker when the marker itself costs less than the removed lines.
5. Inspect the reported saved estimate and saved percent. If savings are zero, keep the original context; reduction must not add text.
6. Recover anything needed later with `rsaver recover --file FILE --range START:END`, then re-read the original with the agent's bounded read tool.
7. Verify integrity before trusting a compacted artifact: `rsaver verify --manifest manifest.json`.
8. Record original estimate, reduced estimate, critical lines preserved, omitted ranges, and the verification status in the working ledger.

## Decision tree
- Need one symbol or error → `select`, not `compact`.
- Output is a repeating log → `dedupe` first; if still large, `compact` with a critical pattern.
- File is source code to edit → read bounded ranges directly; do not prune code.
- Critical lines exceed the line budget → RSaver keeps them all and reports `budget_exceeded_by_critical`; raise the budget or split the task.
- Exact model count is required → use the model's own tokenizer or counting endpoint; RSaver estimates are not sufficient.
- Omitted evidence may be needed later → require a manifest and verify it; without recovery, the reduction is not acceptable.
- Verification fails → discard the compacted artifact and use the original.

## Tool strategy
In this module, `rsaver` is shorthand for `python3 skills/rcoder/scripts/rsaver.py` from the repository root. That canonical location is bundled with the installed skill; `scripts/rsaver.py` is only a repository-root wrapper. It is a dependency-free Python 3 standard-library CLI with subcommands `measure`, `select`, `compact`, `dedupe`, `recover`, and `verify`. It works on files and stdin (`-`), emits human-readable output by default and structured JSON with `--json`. Its estimator is `dependency_free_run_heuristic_v1`: word, number, and symbol runs are charged one token each up to four characters, with longer runs split into four-character pieces. This is deterministic and reproducible across hosts, but model-specific, non-English, and structured content will differ from a real tokenizer.

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
