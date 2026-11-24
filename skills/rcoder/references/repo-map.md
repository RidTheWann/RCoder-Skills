# Repository structural map

## Activate when

The repository is larger than the working context, or a task involves locating which files to change, understanding module boundaries, ranking entry points, or orienting a weak/small model before it opens any file. Do not activate when a single known file is already targeted.

## Mission and expertise

Emit a compact, token-budgeted structural map of a repository — public symbols, signatures, import edges, and entry-point ranking — small enough to stay in a small context window every turn. Own orientation, not implementation: the map replaces blind exploration and wrong-file edits; it never substitutes for reading the code you actually change.

## Mental model

Weak models waste context exploring an unfamiliar repo. A PageRank-ranked map over import edges surfaces the load-bearing files first (leanlm.ai 2026-11-21: wrong-file edits 47/80 → 0/80, pass rate 31.9% → 79.2%, cost 17× lower per verified pass). Structure only (signatures/imports, no bodies) keeps the map a fraction of source size. The map is a cache: rebuild on significant edits or periodically.

## Prerequisites and reconnaissance

1. Confirm `git` is available; `git ls-files` discovery is preferred and honors `.gitignore`.
2. Check whether tree-sitter bindings are present; if absent the helper uses regex fallback parsers (weaker but deterministic).
3. Estimate a token budget appropriate to the active model's context window (default 2048; scale down for ≤8K windows).

## Procedure

1. Run `python3 skills/rcoder/scripts/repo_map.py --root . --budget 2048 --format default` once per session.
2. Keep the map in context for every turn; do not re-run on every read.
3. Use the ranked file list to pick the first file to open; grep inside that file for the exact symbol.
4. After significant edits, rebuild the map (`--root .`) so stale structure does not mislead.
5. For a single-file task with a known target, skip the map and go straight to bounded reads.
6. For JSON consumers, pass `--json`; for names-only orientation, `--format compact`.

## Decision tree

- Unfamiliar large repo → generate map first, then bounded reads inside top-ranked files.
- Known target file → skip map; grep + line-range read.
- Map seems stale after edits → rebuild with `--root .`.
- Tree-sitter unavailable → regex fallback still yields imports/symbols; label confidence accordingly.
- Budget pressure → lower `--budget` and use `--format compact`.

## Tool strategy

- CLI: `repo_map.py` — stdlib-only; optional tree-sitter via subprocess/bindings when present.
- Formats: `compact` (names), `default` (signatures + imports), `detail` (signatures + fields).
- Ranking signals: PageRank over resolved imports, entry-point boost, exported-symbol count, boundary-import boost (http/sql/db/exec), deep-path penalty.
- Pair with `context_snapshot.py` for path/Git state and `rsaver gate` for the budget decision.

## Advanced techniques

- **Refresh cadence**: rebuild the map when the working set or key symbols change, not on every turn.
- **Boundary edges**: files importing http/sql/subprocess/containers rank higher — they own trust and data boundaries.
- **Entry-point detection**: `main.*`, `index.*`, `app.*`, `cmd/**/main.go` get the strongest boost.
- **JSON mode**: feed `--json` output into downstream tooling for deterministic ranking without an LLM.

## Failure modes

- Stale map after edits → rebuild or accept explicit staleness risk.
- Mis-ranking (utility code elevated over task symbols) → combine with `--intent`-style focused reads; report the limitation.
- Map bloat past budget → reduce `--budget` / switch to `compact`.
- Parser misses in unsupported languages → label unsupported, fall back to regex extraction.

## Quality checklist

- [ ] Map generated before first exploratory read in an unfamiliar repo.
- [ ] Map stays within its token budget and is refreshed on significant edits.
- [ ] Ranking is PageRank + entry-point + exports + boundary edges + depth penalty.
- [ ] No function bodies included; signatures/imports only.
- [ ] Discovery honors `.gitignore`/ignore rules and skips vendor/build dirs.
- [ ] Unsupported languages labeled rather than silently omitted.

## Anti-patterns

- Dumping whole files instead of consulting the map.
- Re-running the map on every turn without edits.
- Trusting a stale map after significant changes.
- Treating map ranking as ground truth for correctness.

## Verification

Run `scripts/test-repo-map.py`: synthetic multi-language fixtures assert discovery, symbol/import extraction, graph edges, ranking order, budget bounding, and deterministic output. Compare against a hand-checked expectation set.

## Output format

```
# Repo Map | N files | budget B | rendered ~U tokens
path/to/file.ext [score S]
  function: name signature
  class: name signature
  imports: dep1, dep2
```