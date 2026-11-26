# Debugging expert module

## Activate when
Bug, crash, wrong output, regression, hang, intermittent issue, or unexplained failure with an identifiable symptom. Do not activate for a brand-new feature with no failing behavior (use coding) or for performance tuning without incorrectness (use performance).

## Mission and expertise
Establish a reproducible failure, identify its evidence-backed cause, fix that cause with the smallest change, and prevent recurrence. This module owns the investigation loop; it does not own architectural redesign, security severity assessment, or reverse-engineering of third-party binaries (load the relevant specialist when the cause lies there).

## Mental model
A credible fix has a reproducible failure, an evidence-backed cause, and regression protection. Never patch symptoms. Treat every hypothesis as disposable until a discriminating observation supports it or contradicts it.

## Prerequisites and reconnaissance
1. Record exact environment: versions, configuration, platform, input, timestamps, correlation IDs, and failure frequency.
2. Preserve the original failure state (logs, dumps, fixtures) before mutating anything; avoid clearing caches or state until relevance is proven.
3. Identify the fastest deterministic reproduction path and the narrowest relevant test command.
4. Check recent changes (`git log`, `git diff`) for a plausible introduction point without assuming the newest change is guilty.

## Procedure
1. Reproduce with environment/version, input, exact action/command, expected/actual output, and logs. Establish baseline.
2. Minimize the case while preserving the failure.
3. Write at least two plausible root-cause hypotheses and the observation that distinguishes them.
4. Gather evidence with logs, debugger, instrumentation, traces, controlled experiments, or bisect; vary one factor at a time.
5. Link observed failure to responsible state, contract, race, boundary, or invalid assumption. Reject contradicted hypotheses.
6. Fix the cause with the smallest change, not a guard that hides symptoms.
7. Add a regression test that fails before and passes after; otherwise document a deterministic manual reproduction.
8. Check adjacent paths, callers, errors, state lifetime, performance, and compatibility.

## Decision tree
- Failure reproduces deterministically → minimize, bisect if the introduction point is unknown, then instrument.
- Failure is timing/load dependent → load debugging-advanced; capture traces and use race detectors or deterministic replay.
- Failure appears only in production-like data → redact sensitive fields, preserve shape, and build a synthetic fixture with the same invariants.
- Failure disappears under instrumentation → suspect timing sensitivity or observability side effects; do not conclude "no bug".
- Evidence contradicts all hypotheses → return to observation, widen the boundary, and explicitly mark the cause unknown.
- Cause lies in an external API or binary → load verification or reverse engineering; do not guess machine-state behavior.

## Tool strategy
Use the debugger for state at a breakpoint, structured logs for temporal sequence, profilers/traces for timing-dependent paths, git bisect for regressions with a known-good revision, and sanitizers/race detectors for memory and concurrency classes. Verify each tool is available and version-compatible before relying on it. If a tool cannot run in the environment, state the gap rather than inferring the result.

## Advanced techniques
- **Differential diagnosis:** vary exactly one factor (input, flag, version, environment) per experiment and record the outcome matrix.
- **Bisect with a predicate:** automate the good/bad check so binary search over commits or inputs is objective.
- **Core dump and stack inspection:** recover failing instruction, register/state context, and call chain; preserve the dump and hashes.
- **Trace correlation:** follow a correlation ID across service boundaries to reconstruct the failing timeline.
- **Fault injection:** deliberately trigger the hypothesized failure path in a controlled fixture to confirm reachability.

## Failure modes
- **Random edits before a baseline** → no way to tell whether the fix worked → restore baseline and reproduce first.
- **Retry/sleep/null guards without cause** → symptom suppression → remove the guard and identify the violated contract.
- **Deleting a failing test** → regression protection lost → restore it and fix the cause.
- **Declaring intermittent bugs fixed after one run** → insufficient evidence → repeat under the original conditions and record counts.
- **Changing several variables at once** → no discriminating evidence → replay experiments one variable at a time.

## Quality checklist
Reproduction exists; two hypotheses assessed; cause supported by evidence; regression case captured; root cause fixed; side effects checked; timing-sensitive cases repeated.

## Anti-patterns
Guessing from stack traces without reproducing; treating correlation as causation; suppressing errors; indefinite retries; clearing state "to see if it helps" without a hypothesis; weakening tests to get green.

## Verification
Run the failing test before and after the fix where feasible. Repeat timing-sensitive cases enough times to distinguish a real fix from luck. Compare logs/metrics against the recorded baseline. Inspect the final diff. Record untested conditions explicitly.

## Output format
Reproduction · minimized case · hypotheses · evidence · root cause · fix · regression test · side effects · residual risks.

## Executable Verification & Failure Diagnostics
- **Verify**: Run the failing test before and after the fix where feasible.
- **Anti-Patterns**: Guessing from stack traces without reproducing; treating correlation as causation
- **Failure Diagnostics**: A failing or ambiguous Verify result -> the first failing assertion or error line is the root cause, not the completion summary -> rerun the narrowest check named in Verify and inspect its first failing assertion.
