# Advanced debugging and observability

## Activate when
Intermittent failures, production-like incidents, distributed traces, nondeterministic bugs, race conditions, or complex state corruption.

## Mental model
Debugging is controlled hypothesis elimination. Preserve evidence, reproduce the smallest failure, and avoid changing several variables at once.

## Procedure
1. Capture exact versions, configuration, environment, input, timestamps, correlation IDs, and failure frequency.
2. Establish a baseline and define observable success/failure metrics before modifying behavior.
3. Construct competing hypotheses and discriminating experiments; change one variable per experiment.
4. Use structured logs, traces, core dumps, profilers, race detectors, and deterministic replay appropriate to the failure.
5. Minimize reproduction and preserve failing fixtures; avoid deleting caches or state unless proven relevant.
6. Fix the root cause, add regression coverage, and inspect adjacent failure paths.

## Quality checklist
- [ ] Hypotheses are tested with discriminating evidence.
- [ ] Reproduction is minimized and retained.
- [ ] Observability avoids secrets/PII.
- [ ] Regression verifies root-cause correction.

## Anti-patterns
- Changing multiple variables simultaneously.
- Treating correlation as causation.
- Suppressing errors or retrying indefinitely.

## Verification
Record baseline, exact experiment commands, before/after signals, regression result, and untested conditions.

## Output format
Provide timeline, hypotheses, evidence, root-cause confidence, fix, tests, and residual risks.
