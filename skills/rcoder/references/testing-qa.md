# Testing and QA expert module

## Activate when
Behavior changes, test coverage, quality gates, acceptance criteria, flaky tests, or release confidence. Use test-engineering for strategy design (property/fuzz/mutation) and coding for implementing the source change.

## Mission and expertise
Turn acceptance criteria into a deterministic, layered set of tests that proves behavior at the lowest sufficient level and protects against regression. Own test selection, fixtures, determinism, and the honesty of reported results. Do not treat coverage percentage as proof of correctness.

## Mental model
Tests are executable contracts. Use the lowest test layer that proves behavior, adding higher-level tests for integration risks. A test that can pass while the operation never ran is worse than no test; it creates false confidence.

## Prerequisites and reconnaissance
1. Translate the request into observable acceptance criteria and explicit negative criteria.
2. Inspect fixtures, test conventions, runner configuration, CI commands, and the pinned runtime before writing tests.
3. Identify which boundaries need proof (function, module, persistence, network, UI) and which can be doubled safely.
4. Record baseline failures for bug fixes before applying a fix when possible.

## Procedure
1. Translate request into observable acceptance and negative criteria.
2. Inspect fixtures, test conventions, speed, and CI commands.
3. Choose unit, contract, integration, and end-to-end layers based on the boundary being proved.
4. Cover happy path, boundaries, invalid input, permission/error states, and regression behavior.
5. For bugs, prove baseline failure before fix when possible.
6. Control time, random, network, filesystem, and concurrency to keep tests deterministic.
7. Run narrow tests first, then broader suite and lint/type/build gates. Investigate flakes, do not mask them.

## Decision tree
- Pure logic with clear inputs → unit test with explicit boundary cases.
- Contract with another service → contract test plus a small integration test against a local fixture.
- Bug fix → regression test that fails on the unfixed code; verify that failure.
- Behavior depends on time/randomness → inject a clock or seed; do not sleep.
- Test is flaky → reproduce deterministically first; quarantine only with owner and expiry.
- External system is unavailable → local fake with the same contract; mark live integration NOT VERIFIED.
- Full suite is too slow locally → run the narrow set, then the documented gate in CI.

## Tool strategy
Use the project's existing runner, fixtures, and assertion style. Use coverage to locate untested paths and fuzz/property tools only when the failure mode warrants them. Verify runner versions from manifests. Never assume a framework plugin is installed; check help or package metadata first.

## Advanced techniques
- **Acceptance matrix:** map each criterion to at least one passing test and one failing-condition test.
- **Deterministic controls:** inject time, randomness, IDs, and I/O; assert on outcomes, not implementation steps.
- **Baseline proof:** run the new test against the pre-fix code (or a stashed diff) and record the failure.
- **Isolated fixtures:** create and clean state per test so order never matters.
- **Failure localization:** name the invariant in the assertion message so failures explain themselves.

## Failure modes
- **Unstable snapshots** → noisy failures → assert on stable, meaningful fields.
- **Over-mocking the subject** → tests pass without exercising behavior → mock only external dependencies.
- **Tests passing when the operation never ran** → false confidence → assert observable effects and call counts.
- **Missing contract tests after interface changes** → integration breakage → add a consumer-driven test.
- **Masked flakes** → hidden regressions → investigate root cause and record retry policy explicitly.

## Quality checklist
Assertions represent behavior and failure conditions; data is isolated/cleaned; denied access and errors are covered; CI and local checks use documented compatible runtimes.

## Anti-patterns
Asserting log text instead of behavior; arbitrary sleeps; permanent skips; duplicating production data with secrets into fixtures; running only the fast tests and calling it a full pass.

## Verification
Record exact command, exit code, count, runtime, and skipped suites. Inspect the final diff. Mark any suite that could not run as NOT VERIFIED with the reason.

## Output format
Acceptance matrix · test layers · added cases · commands/results · known gaps.
