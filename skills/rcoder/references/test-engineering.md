# Advanced test engineering and quality strategy

## Activate when
Building test architecture, flaky-test reduction, property/fuzz testing, contract testing, mutation testing, or CI test optimization.

## Mental model
Tests are executable specifications. Optimize for failure detection, determinism, diagnostic value, and maintenance—not coverage percentage alone.

## Procedure
1. Map critical behavior, invariants, risks, and integration boundaries to a risk-based test strategy.
2. Choose example-based, property-based, fuzz, mutation, contract, snapshot, hardware-in-loop, or end-to-end tests based on failure modes.
3. Make tests deterministic: control time, randomness, external services, concurrency, and filesystem state.
4. Design fixtures for clarity; avoid hidden shared state and test-order dependencies.
5. Measure flakiness, runtime, failure localization, mutation score, and escaped defects; quarantine only with owner and expiry.
6. Ensure negative tests verify authorization, invalid input, resource exhaustion, rollback, and cleanup.

## Quality checklist
- [ ] Critical invariants map to tests.
- [ ] Tests are reproducible and isolated.
- [ ] Flaky tests have owner and expiry.
- [ ] Negative and failure paths are covered.

## Anti-patterns
- Asserting implementation details rather than behavior.
- Sleeping for arbitrary intervals to synchronize tests.
- Permanently skipping flaky tests.

## Verification
Repeat targeted suites when flakiness is involved; use coverage/mutation/fuzz results as evidence, not guarantees.

## Output format
State test strategy, risk coverage, deterministic controls, runtime, known gaps, and exact results.
