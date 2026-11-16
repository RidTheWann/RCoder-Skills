# S05 — Measured performance bottleneck

## Fixture
A dashboard render takes 900 ms in a representative local workload. A profile indicates one repeated data transformation dominates CPU time; network and database latency are stable.

## Task
Record workload and baseline, profile the actual hotspot, propose a measurable hypothesis, make one focused change, and compare identical before/after runs.

## Required evidence
- Environment, workload, metric, and target budget.
- Profile evidence for the dominant cost.
- Change maps to the measured bottleneck.
- Repeatable before/after results and correctness/memory checks.
