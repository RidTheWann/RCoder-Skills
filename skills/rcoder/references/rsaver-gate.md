# RSaver Gate: context filtering above the skill layer

## Activate when
At the start of any non-trivial prompt, before selecting specialists; before each agent step that would load a skill, run a search, call a tool, emit reasoning, or send a request; when a context window, cost ceiling, cache prefix, or output reserve matters. Do not activate to filter source code you are about to edit, or to justify skipping a required verification gate.

## Mission and expertise
Act as the process filter between the prompt and every downstream stage: Skills, reasoning, searching, tool calls, and the final response. Decide what enters the model, what stays in a stable cacheable prefix, what is deferred with a recovery pointer, and how much window is reserved for output and reasoning. Own the budget arithmetic and the decision ledger; do not own the domain decision itself.

## Mental model
RSaver cannot intercept a model runtime from a Markdown skill file. It is an instruction-level gate plus a deterministic CLI that the agent invokes at each boundary. The pipeline is:

```text
Prompt
  -> RSaver Gate: classify, budget input/cache/output, filter context, plan prefix
  -> Model
  -> Skills / reasoning / searching / tools (only the selected slice)
  -> RSaver Gate: filter tool results, update the ledger and cache plan, re-check budget
  -> Model
  -> Response
```

Every arrow back to the model is a new budget decision. A cache hit is a billing and latency fact from usage fields, never an assumption.

## Prerequisites and reconnaissance
1. Determine whether the host exposes a context-window value, a token-counting endpoint, and usage fields. Record each as observed or UNKNOWN.
2. Identify static material (system instructions, tool schemas, stable references) and volatile material (user prompt, tool output, search results, history).
3. Identify the provider's minimum cacheable prefix and TTL behavior from version-matched official documentation, not memory.
4. Define the output and reasoning reserve for this step; a reasoning model may need far more than the visible answer suggests.

## Procedure
1. Build a context envelope: each item has `id`, `section` (`prefix`, `working`, `history`, `tail`), `tokens`, `stability` (`static` or `dynamic`), and `priority` (`required`, `useful`, `optional`).
2. Run `python3 scripts/rsaver.py gate envelope.json --json` to get the budget split, cache eligibility, per-item decisions, and warnings.
3. Keep every required item, including the user prompt and the last tool result needed for the current decision. Defer optional history first, then merely useful material.
4. Place retained static items first and contiguously; never insert a volatile item into the planned cache prefix.
5. Check `cache_prefix_below_minimum` and `cache_prefix_fragmented_by_dynamic_item` warnings. A prefix below the minimum earns no discount; a fragmented prefix must be re-planned.
6. Confirm `projected_total <= window_tokens` with explicit output and reasoning reserves before sending the request.
7. After each tool or search result, filter verbose output with `compact` or `dedupe`, write a hash-checked manifest, and re-run the gate for the next step.
8. Record input estimate, cacheable prefix estimate, ordinary input, reserves, deferred item IDs, warnings, and observed usage in the working ledger.

## Decision tree
- Single bounded prompt with no tools → Focused profile; skip the gate ceremony but keep the output reserve.
- Multi-step or tool-heavy task → always run the gate at each model boundary.
- Window pressure with old successful tool output → clear or defer that output first; keep the final result and all error lines.
- Prefix below the cache minimum → either merge stable material to reach the minimum or accept no caching; do not fabricate a cache hit.
- Dynamic item must be early → move it to `tail` where the protocol allows, or accept a shorter cache prefix.
- Required items exceed the budget → stop and reduce scope or choose a larger window; never silently drop a required item.
- Exact cost or billing question → use the provider's counting endpoint and observed usage; RSaver estimates are planning aids.
- Verification or authorization context → required; never defer it for budget reasons.

## Tool strategy
The CLI is `python3 skills/rcoder/scripts/rsaver.py` (bundled) with a repository-root wrapper at `scripts/rsaver.py`. Use `budget` to allocate a window, `gate` to filter an envelope, `measure`/`compare` to estimate item sizes, `compact`/`dedupe` to reduce verbose results, and `recover`/`verify` to preserve evidence. Token counts in an envelope may come from an exact counter, a provider count endpoint, or RSaver's v2 estimator; label their source.

## Advanced techniques
- **Prefix ordering:** sort by section (`prefix`, `working`, `history`, `tail`) and keep static items adjacent so cumulative cache hashes remain stable across turns.
- **Reserve-first budgeting:** subtract output and reasoning reserves before computing the input budget; this prevents `incomplete` responses with no visible text.
- **Deferred ledger:** every deferred item carries a recovery pointer; a deferred item is externalized, not deleted.
- **Cache break-even:** with common 0.1x read and 1.25x write rates, two requests justify a short-TTL write and three justify a long-TTL write; measure actual hits.
- **Tool-result clearing:** retain the final result, errors, and status; defer intermediate successful output from earlier steps.
- **Usage reconciliation:** compare planned estimates with `usage` fields after the response and record the delta for calibration.

## Failure modes
- **Caching assumed from a stable-looking prompt** → silent miss → verify with usage fields.
- **Reasoning tokens ignored** → `incomplete` response after billed input → reserve headroom explicitly.
- **Dynamic content inside the prefix** → every turn rewrites the cache → move volatile content to the tail.
- **Over-aggressive pruning** → evidence loss → keep required items and manifests, then verify.
- **Estimator treated as exact** → wrong budget decisions → use a real counting endpoint for consequential calls.
- **Tool schemas forgotten** → undercounted input → include `tool_schema_tokens` in the envelope.

## Quality checklist
- [ ] Output and reasoning reserves are explicit and subtracted before the input budget.
- [ ] Required items are kept; deferred items have recovery pointers.
- [ ] The cacheable prefix is contiguous static content and meets the provider minimum or is labeled ineligible.
- [ ] No security, authorization, or verification evidence was deferred.
- [ ] Projected total is within the window and warnings are resolved or accepted with reasoning.
- [ ] Planned estimates are reconciled with observed usage when available.

## Anti-patterns
Deferring the user prompt or failing tests to save tokens; claiming a cache hit without usage evidence; putting timestamps or random IDs in a cached prefix; reserving zero output budget; pruning stack traces to improve a savings percentage; treating RSaver as a runtime interceptor.

## Verification
Run `python3 scripts/test-rsaver.py`, which checks budget arithmetic, required/deferred decisions, cache eligibility, fragmentation, and rejection paths. For a live run, retain the envelope, gate output, final response usage fields, and the delta between planned and observed tokens in the working ledger.

## Output format
Gate decision summary · input/cache/output/reserve numbers · kept and deferred item IDs · cache warnings · recovery pointers · observed usage delta · residual risks.
