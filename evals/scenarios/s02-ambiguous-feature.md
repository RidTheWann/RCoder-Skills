# S02 — Ambiguous feature request

## Fixture
An existing service exports one record to CSV. The request is: “Add bulk export.” No product policy exists for size limits, partial failures, or ordering.

## Task
Inspect current export contracts and tests, state reversible assumptions/non-goals, implement a safe bounded first slice, and identify policy decisions that cannot safely be inferred.

## Required evidence
- Existing implementation and project conventions inspected.
- Assumptions, non-goals, and size/timeout limits stated.
- No speculative storage or job architecture introduced.
- Tests for success, invalid selection, and failure.
