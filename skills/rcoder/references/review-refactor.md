# Code review and refactoring expert module

## Activate when
Code review, maintainability audit, cleanup, refactor, duplication, or risk assessment.

## Mental model
Review correctness and change risk before style. A refactor preserves observable behavior unless behavior change is explicitly requested.

## Procedure
1. Read diff and surrounding call graph; do not judge isolated lines only.
2. Trace data/control flow through callers, consumers, persistence, concurrency, and error handling.
3. Rank correctness/data loss/security → availability/performance → compatibility → maintainability → style.
4. For every finding give location, trigger, impact, and evidence; separate defects from questions/suggestions.
5. For refactors capture baseline tests/contracts and state the invariant to preserve.
6. Avoid mixing behavior change, dependency upgrade, and architecture redesign unless required.
7. Run focused tests and inspect semantic drift and unrelated edits.
8. State reviewed scope and limitations; do not claim “no findings” beyond it.

## Quality checklist
Findings are ranked, actionable, evidence-backed, and non-duplicative; public behavior preserved; diff focused; tests cover invariant.

## Anti-patterns
Cosmetic opinions as blockers; findings without trigger/impact; mass formatting plus bug fix; shorter but less clear code.

## Verification
Run unit/contract tests, static/type checks, and final diff inspection; compare public outputs/contracts for behavior-preserving work.

## Output format
Finding (severity/location/trigger/impact/evidence/recommendation) · scope · checks · uncertainty.
