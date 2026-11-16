# Debugging expert module

## Activate when
Bug, crash, wrong output, regression, hang, intermittent issue, or unexplained failure.

## Mental model
A credible fix has a reproducible failure, evidence-backed cause, and regression protection. Never patch symptoms.

## Procedure
1. Reproduce with environment/version, input, exact action/command, expected/actual output, and logs. Establish baseline.
2. Minimize the case while preserving the failure.
3. Write at least two plausible root-cause hypotheses and the observation that distinguishes them.
4. Gather evidence with logs, debugger, instrumentation, traces, controlled experiments, or bisect; vary one factor at a time.
5. Link observed failure to responsible state, contract, race, boundary, or invalid assumption. Reject contradicted hypotheses.
6. Fix the cause with the smallest change, not a guard that hides symptoms.
7. Add a regression test that fails before and passes after; otherwise document a deterministic manual reproduction.
8. Check adjacent paths, callers, errors, state lifetime, performance, and compatibility.

## Quality checklist
Reproduction exists; two hypotheses assessed; cause supported; regression case captured; root cause fixed; side effects checked.

## Anti-patterns
Random edits before baseline; retries/sleeps/null guards without cause; deleting or weakening failing tests; declaring intermittent bugs fixed after one run.

## Verification
Run failing test before/after where feasible, repeat timing-sensitive cases, and compare logs/metrics.

## Output format
Reproduction · minimized case · hypotheses · evidence · root cause · fix · regression test · side effects.
