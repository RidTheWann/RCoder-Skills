# Advanced debugging and observability

## Activate when
Intermittent failures, production-like incidents, distributed traces, nondeterministic bugs, race conditions, memory corruption, or complex state corruption. Use plain debugging first for deterministic local bugs; escalate here when the failure resists a single reproducer.

## Mission and expertise
Eliminate hypotheses systematically under uncertainty and preserve evidence that may disappear. Own controlled experiments, observability design, and incident-timeline reconstruction for hard failure classes. Coordinate with reverse engineering or security when the fault lies in third-party binaries, undocumented protocols, or a suspected attack.

## Mental model
Debugging is controlled hypothesis elimination. Preserve evidence, reproduce the smallest failure, and avoid changing several variables at once. Under nondeterminism, the goal is to raise the probability of observing the failure and to identify the invariant that was violated, not merely to make one run pass.

## Prerequisites and reconnaissance
1. Capture exact versions, configuration, environment, input, timestamps, correlation IDs, and failure frequency.
2. Establish a baseline and define observable success/failure metrics before modifying behavior.
3. Confirm observability does not expose secrets or personal data; redact at collection time rather than after publication.
4. Ensure dumps, traces, and logs are retained under a defined retention policy and that analysis happens on a copy.

## Procedure
1. Capture exact versions, configuration, environment, input, timestamps, correlation IDs, and failure frequency.
2. Establish a baseline and define observable success/failure metrics before modifying behavior.
3. Construct competing hypotheses and discriminating experiments; change one variable per experiment.
4. Use structured logs, traces, core dumps, profilers, race detectors, and deterministic replay appropriate to the failure.
5. Minimize reproduction and preserve failing fixtures; avoid deleting caches or state unless proven relevant.
6. Fix the root cause, add regression coverage, and inspect adjacent failure paths.
7. Reconstruct the incident timeline from independent evidence sources and record confidence per step.

## Decision tree
- Memory corruption suspected → use sanitizers (ASan/UBSan) and preserve the core dump; do not "fix" by adding padding.
- Race/deadlock suspected → use a race detector or lock-order analysis; verify happens-before relationships.
- Failure spans services → follow correlation IDs across boundaries; check clocks and clock skew before ordering events.
- Failure only under load → reproduce with controlled load; distinguish saturation, contention, and resource exhaustion.
- Failure is in third-party native code → collect the exact version, symbols, and offsets; load reverse engineering rather than guessing semantics.
- Evidence is insufficient → keep the hypothesis unresolved and gather more observations; never invent missing state.

## Tool strategy
Choose the tool by failure class: structured logging for sequences, distributed tracing for cross-service timelines, core dumps and debuggers for state, profilers for contention and hot paths, race detectors for concurrency, and deterministic replay for nondeterminism. Confirm licensing, availability, and version compatibility. Run multiple independent tools when a conclusion is high-impact.

## Advanced techniques
- **Delta debugging:** automatically minimize a failing input while preserving the failure predicate.
- **Deterministic replay:** record inputs/scheduling and replay to make an intermittent fault observable on demand.
- **Clock reconciliation:** normalize timestamps across hosts before asserting causal order; record skew explicitly.
- **Observability as code:** define structured events with stable fields so queries remain valid across versions.
- **Chaos-style fault injection:** inject a failure in a controlled fixture to verify detection and recovery paths without touching production.
- **Statistical confirmation:** compare failure rates before and after a fix over enough trials to exceed noise.

## Failure modes
- **Changing multiple variables simultaneously** → no discriminating evidence → replay one-variable experiments.
- **Treating correlation as causation** → wrong fix → require a mechanism and a discriminating experiment.
- **Suppressing errors or retrying indefinitely** → masks the cause and can amplify load → bound retries, log them, and fix the cause.
- **Losing volatile evidence** → investigation dead end → capture dumps/logs before restart and preserve hashes.
- **Leaking secrets into traces** → new security incident → redact at collection and verify captured artifacts.

## Quality checklist
Hypotheses are tested with discriminating evidence; reproduction is minimized and retained; observability avoids secrets/PII; regression verifies root-cause correction; timeline steps carry confidence; untested conditions are listed.

## Anti-patterns
Restarting as a diagnostic without preserving state; editing production behavior during an incident without approval; assuming a single successful run proves a fix; unbounded logging that changes timing or fills disks.

## Verification
Record baseline, exact experiment commands, before/after signals, regression result, and untested conditions. Repeat under original conditions. Validate that monitoring detects recurrence.

## Output format
Timeline · hypotheses · evidence · root-cause confidence · fix · tests · residual risks · unresolved observations.
