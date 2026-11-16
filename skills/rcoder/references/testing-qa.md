# Testing and QA expert module

## Activate when
Behavior changes, test coverage, quality gates, acceptance criteria, flaky tests, or release confidence.

## Mental model
Tests are executable contracts. Use the lowest test layer that proves behavior, adding higher-level tests for integration risks.

## Procedure
1. Translate request into observable acceptance and negative criteria.
2. Inspect fixtures, test conventions, speed, and CI commands.
3. Choose unit, contract, integration, and end-to-end layers based on the boundary being proved.
4. Cover happy path, boundaries, invalid input, permission/error states, and regression behavior.
5. For bugs, prove baseline failure before fix when possible.
6. Control time, random, network, filesystem, and concurrency to keep tests deterministic.
7. Run narrow tests first, then broader suite and lint/type/build gates. Investigate flakes, do not mask them.

## Quality checklist
Assertions represent behavior and failure conditions; data is isolated/cleaned; denied access and errors are covered; CI and local checks use documented compatible runtimes.

## Anti-patterns
Unstable snapshots; over-mocking the subject; tests passing when operation never ran; no contract tests for changed external interfaces.

## Verification
Record exact command, exit code, count, runtime, and skipped suites.

## Output format
Acceptance matrix · test layers · added cases · commands/results · known gaps.
