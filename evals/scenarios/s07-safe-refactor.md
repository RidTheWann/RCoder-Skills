# S07 — Behavior-preserving refactor

## Fixture
Two billing paths duplicate tax and rounding logic. Historical output format and rounding behavior are consumed by downstream invoices.

## Task
Capture observable baseline, state the invariant, identify safe shared logic, refactor without changing behavior, and prove output equivalence for boundaries.

## Required evidence
- Baseline tests/output preserved.
- Explicit rounding, precision and compatibility invariant.
- Focused diff without unrelated dependency/toolchain changes.
- Tests for boundary amounts, negative/zero inputs where valid, and public output.
