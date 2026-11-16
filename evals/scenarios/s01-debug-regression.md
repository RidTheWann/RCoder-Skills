# S01 — Failing parser regression

## Fixture
A parser accepts ordinary quoted strings but fails on a quoted escape sequence such as an escaped quote followed by a delimiter. A single unit test reproduces it.

## Task
Reproduce the exact failure, minimize the input, state at least two plausible hypotheses, use evidence to isolate the cause, make the smallest correction, and add a regression test.

## Required evidence
- Baseline failing test and command/output.
- Competing hypotheses and the discriminating experiment.
- Root cause connected to parser state/tokenization.
- Regression test that fails before and passes after.
- Adjacent quote/escape cases remain covered.
