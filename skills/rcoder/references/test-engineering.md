# Advanced test engineering and quality strategy

## Activate when
Building test architecture, reducing flaky tests, adding property/fuzz/contract/mutation testing, or optimizing CI test execution. Do not activate to write a single straightforward unit test; use testing-qa for that, and load security for authorization/negative-security test design.

## Mission and expertise
Design a risk-based test strategy whose tests are deterministic, diagnostic, and aligned with failure modes. Own test layering, fixture design, flakiness control, and measurement of test effectiveness. Coverage percentage is an input, never the objective.

## Mental model
Tests are executable specifications. Optimize for failure detection, determinism, diagnostic value, and maintenance. A test suite is useful when it fails on realistic regressions, localizes the failure, and is cheap enough to run at the right frequency.

## Prerequisites and reconnaissance
1. Map the system's critical behaviors, invariants, trust boundaries, integration points, and known historical defects.
2. Identify existing test layers, runners, fixtures, CI gates, and runtime budgets from repository configuration.
3. Determine which behaviors are deterministic locally and which need controlled doubles, sandboxes, or fixtures.
4. Establish whether flakiness exists and collect baseline failure rates before changing tests.

## Procedure
1. Map critical behavior, invariants, risks, and integration boundaries to a risk-based test strategy.
2. Choose example-based, property-based, fuzz, mutation, contract, snapshot, hardware-in-loop, or end-to-end tests based on failure modes.
3. Make tests deterministic: control time, randomness, external services, concurrency, and filesystem state.
4. Design fixtures for clarity; avoid hidden shared state and test-order dependencies.
5. Measure flakiness, runtime, failure localization, mutation score, and escaped defects; quarantine only with owner and expiry.
6. Ensure negative tests verify authorization, invalid input, resource exhaustion, rollback, and cleanup.

## Decision tree
- Pure function with rich invariants → property-based tests plus a few readable examples.
- Parser/deserializer of untrusted input → fuzzing with a corpus and crash regression fixtures; load security.
- Contract between independently deployed services → consumer-driven contract tests plus schema validation.
- UI behavior → deterministic component tests plus a small number of end-to-end journeys; load ui-ux-accessibility for accessibility checks.
- Failure is flaky → reproduce in isolation first; if it needs external state, make time/randomness/I/O injectable rather than adding sleeps.
- High-risk refactor → characterization tests and mutation testing to check the suite actually detects changes.
- Test would require production data → build synthetic fixtures with the same invariants; never copy secrets or personal data.

## Tool strategy
Use the project's existing test runner and assertion style. Use property/fuzz frameworks only when the runtime already supports them and the failure mode justifies them. Use coverage to find untested paths and mutation testing to evaluate assertion strength; treat both as diagnostics. Verify tool versions from manifests before relying on plugin behavior.

## Advanced techniques
- **Property discovery:** express invariants (round-trip, idempotence, commutativity, bounds preservation) rather than enumerating examples.
- **Metamorphic testing:** assert that a related input produces a predictably related output when exact output is unknown.
- **Fault injection at boundaries:** verify timeout, retry, circuit-breaker, and rollback behavior by forcing dependency failures.
- **Mutation-driven review:** if a meaningful mutation survives, the spec assertion is too weak.
- **Deterministic time and randomness:** inject clocks and seeds so order-dependent failures become reproducible.
- **Test impact analysis:** run tests affected by the diff locally, then the full gate at the documented frequency.

## Failure modes
- **Asserting implementation details** → refactors break correct behavior → assert observable contracts.
- **Arbitrary sleeps** → slow, still flaky tests → wait on explicit conditions with bounded timeouts.
- **Permanently skipped flaky tests** → silent coverage loss → quarantine with owner, expiry, and a repair task.
- **Shared mutable fixtures** → order dependence → isolate state per test.
- **Coverage chasing** → many shallow assertions → target invariants and mutation score instead.

## Quality checklist
Critical invariants map to tests; tests are reproducible and isolated; flaky tests have owner and expiry; negative and failure paths are covered; runtime fits the CI budget; failures localize the cause.

## Anti-patterns
One giant integration test for every case; mocking the unit under test; asserting log strings instead of behavior; copying production data into fixtures; treating a green suite as proof of correctness.

## Verification
Repeat targeted suites when flakiness is involved; run the narrow set first and the documented gate second. Use coverage/mutation/fuzz results as evidence, not guarantees. Record exact commands, versions, counts, and known gaps.

## Output format
Test strategy · risk coverage · deterministic controls · runtime · known gaps · exact results.

## Executable Verification & Failure Diagnostics
- **Verify**: Repeat targeted suites when flakiness is involved; run the narrow set first and the documented gate second.
- **Anti-Patterns**: One giant integration test for every case; mocking the unit under test
- **Failure Diagnostics**: A failing or ambiguous Verify result -> the first failing assertion or error line is the root cause, not the completion summary -> rerun the narrowest check named in Verify and inspect its first failing assertion.
