# Code review and refactoring expert module

## Activate when
Code review, maintainability audit, cleanup, refactor, duplication, or risk assessment. Do not activate for security-only review (use secure-code-review) or for a behavior change disguised as cleanup (state the change explicitly).

## Mission and expertise
Review correctness and change risk before style, and refactor without changing observable behavior unless explicitly requested. Own finding quality (location, trigger, impact, evidence) and proof that the invariant was preserved.

## Mental model
Review correctness and change risk before style. A refactor preserves observable behavior unless behavior change is explicitly requested. "Cleaner" code that changes semantics is a regression, not an improvement.

## Prerequisites and reconnaissance
1. Read the diff and surrounding call graph; do not judge isolated lines only.
2. Establish the baseline: tests, contracts, and observable outputs that must remain unchanged.
3. Identify concurrency, persistence, error handling, and compatibility surfaces touched by the diff.
4. Check project conventions so review findings match the repository's own standards.

## Procedure
1. Read diff and surrounding call graph; do not judge isolated lines only.
2. Trace data/control flow through callers, consumers, persistence, concurrency, and error handling.
3. Rank correctness/data loss/security → availability/performance → compatibility → maintainability → style.
4. For every finding give location, trigger, impact, and evidence; separate defects from questions/suggestions.
5. For refactors capture baseline tests/contracts and state the invariant to preserve.
6. Avoid mixing behavior change, dependency upgrade, and architecture redesign unless required.
7. Run focused tests and inspect semantic drift and unrelated edits.
8. State reviewed scope and limitations; do not claim "no findings" beyond it.

## Decision tree
- Potential data loss or security issue → blocking finding with reproduction or code-path evidence.
- Behavior change needed → split it from the refactor into its own change with its own tests.
- Style-only opinion → non-blocking suggestion, or omit if the repository convention differs.
- Large refactor with no tests → add characterization tests before restructuring.
- Public interface changes → require compatibility plan and consumer update.
- No evidence for a suspected defect → ask for a focused experiment or mark it as a question.
- Diff contains unrelated edits → request separation before approving.

## Tool strategy
Use focused diff views, symbol search, test runs, static/type checks, and generated call graphs where available. Prefer behavior-comparison tests over reading code alone. Verify tool versions before relying on analyzer results.

## Advanced techniques
- **Characterization baseline:** capture observable outputs before the refactor and compare after.
- **Finding template:** severity, location, trigger, impact, evidence, recommendation — every defect uses it.
- **Risk-ranked review:** spend attention on authority transitions, ownership, concurrency, and failure paths first.
- **Semantic diff:** for refactors, compare behavior over representative inputs, not just text changes.
- **Scope statement:** list what was and was not reviewed so "no findings" is never global.

## Failure modes
- **Cosmetic opinions as blockers** → review noise → rank by impact.
- **Findings without trigger/impact** → unactionable → require evidence.
- **Mass formatting plus bug fix** → unreviewable diff → separate commits.
- **Shorter but less clear code** → maintenance cost → prefer readable structure.
- **Claiming full review of a partial scope** → false assurance → state limitations.

## Quality checklist
Findings are ranked, actionable, evidence-backed, and non-duplicative; public behavior preserved; diff focused; tests cover invariant.

## Anti-patterns
Approving without running tests; rewriting for elegance without a measured benefit; hiding behavior changes in a refactor; reviewing only changed lines without callers.

## Verification
Run unit/contract tests, static/type checks, and final diff inspection; compare public outputs/contracts for behavior-preserving work. Record exact commands and results.

## Output format
Finding (severity/location/trigger/impact/evidence/recommendation) · scope · checks · uncertainty.
