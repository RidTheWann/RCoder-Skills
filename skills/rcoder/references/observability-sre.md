# Observability and reliability engineering: telemetry, SLOs, alerting, and incident readiness

## Activate when
Instrumenting a service, choosing logs, metrics, and traces, defining service level objectives, tuning noisy or missing alerts, building dashboards or runbooks, diagnosing a production issue that lacks evidence, or reviewing capacity, rollout, and rollback safety. Do not activate for a live security incident (use incident-response-forensics), for single-process profiling (use performance), or for pipeline design without a runtime question (use devops-ci-cd).

## Mission and expertise
Own the ability to answer "is it working for users, and if not, why" from production signals, at bounded cost. Claims about reliability are backed by measurements; unmeasured behavior is reported as UNKNOWN.

## Mental model
Telemetry is evidence with a price. Metrics are cheap, aggregated, and good for alerting and trends; traces show causality across services; logs carry detail and are expensive at volume. Cardinality is the main cost and failure driver for metrics. An SLO converts reliability into an error budget that arbitrates between shipping and stabilizing. Alerts should page on user-visible symptoms that need a human now, and everything else goes to tickets or dashboards. A signal nobody can act on is noise.

## Prerequisites and reconnaissance
1. Identify the user journeys and the dependencies each one crosses, including third parties.
2. Inventory the existing telemetry stack, retention, sampling, cost, and who is on call.
3. Find the current incidents, alert history, and the most common causes of pages.
4. Establish the deploy and rollback mechanism and how a change is correlated to a signal.
5. Check data-handling constraints: personal data, secrets, and regional retention rules.

## Procedure
1. Define service level indicators per journey, such as the ratio of good events to valid events for availability and a latency percentile threshold, measured as close to the user as practical.
2. Set SLO targets from user need and history, not aspiration; compute the error budget and agree a policy for what happens when it is spent.
3. Instrument with a vendor-neutral standard such as OpenTelemetry where the stack allows; propagate trace context across every hop, including queues and async jobs.
4. Emit structured logs with a correlation or trace identifier, severity, and stable field names; never log secrets or unredacted personal data.
5. Use the RED method for request-driven services (rate, errors, duration) and the USE method for resources (utilization, saturation, errors); add business signals that detect silent failure.
6. Control cardinality: no unbounded identifiers as metric labels; use exemplars or traces for per-request detail.
7. Alert on SLO burn rate with multiple windows to catch fast and slow burns, route by severity, and attach a runbook link and the first diagnostic query to every page.
8. Make rollouts observable and reversible: canary or staged exposure, automated comparison against baseline, and a tested rollback.
9. Practice: run game days or failure injection in a safe environment and fix the gaps they show.

## Decision tree
- Users report failure but no alert fired → add or repair the symptom-based SLI first, not another cause-based alert.
- Pages are frequent and unactionable → delete, merge, or demote them to tickets; keep only symptoms that need a human now.
- Metric cost or cardinality is exploding → find the label with unbounded values, drop or bucket it, and move detail to traces.
- A request crosses services and the cause is unclear → require trace propagation before adding more logs.
- Telemetry might contain personal data → redact at the source and shorten retention before expanding collection.
- Reliability target is unspecified → measure current behavior and propose an SLO with its evidence rather than inventing one.

## Tool strategy
Use the existing stack first; check the query language and retention limits before designing signals. Use the telemetry SDK's test or in-memory exporters for unit tests, and a local collector for integration checks. Use load generation and failure injection only in environments the user owns and has authorized. Estimate telemetry volume and cost from sample data before enabling it broadly.

## Advanced techniques
- Multi-window, multi-burn-rate alerts tied to the error budget.
- Tail-based sampling that keeps errors and slow traces while dropping routine ones.
- Exemplars linking a metric spike to a trace.
- Synthetic probes for journeys with low organic traffic.
- Dependency SLO budgeting so a downstream outage does not consume the whole error budget unseen.
- Structured change events on dashboards to correlate deploys, flags, and config.
- Saturation signals for queues, pools, and rate limits, with back-pressure rather than unbounded buffering.

## Failure modes
- Alerting on causes such as CPU instead of symptoms users feel.
- Averages hiding tail latency.
- Unbounded metric labels causing cost spikes or dropped data.
- Broken trace context across async boundaries.
- Dashboards that cannot answer a question during an incident.
- SLOs that cannot be measured from available data.
- Secrets or personal data in logs and traces.
- Runbooks that are stale or untested.

## Quality checklist
- Each critical journey has an SLI, an SLO, and an error-budget policy.
- Pages are symptom-based, actionable, and link a runbook.
- Trace context propagates across all hops including async.
- Logs are structured, correlated, and redacted.
- Metric cardinality and telemetry cost are bounded and estimated.
- Rollouts are staged with a tested rollback.
- The on-call can reach the answer to "what changed" quickly.

## Anti-patterns
- Collecting everything and querying nothing.
- Alert fatigue tolerated as normal.
- Per-user or per-request identifiers as metric labels.
- Averages as the latency target.
- Claiming a reliability level that no signal supports.

## Verification
Replay or inject a representative failure in a safe environment and assert the right alert fires within the target time with a usable runbook. Verify trace continuity across each service and async hop with a test request. Compute the SLI from raw data and compare it with the dashboard value. Confirm label cardinality stays within budget under load. Confirm redaction by searching emitted telemetry for known test secrets. Test the rollback. Mark production behavior NOT VERIFIED unless observed.

## Output format
Journeys and SLIs · SLO targets with evidence · instrumentation and alert changes · cost and cardinality estimate · runbook and rollback status · tests run with observed results · residual gaps and items NOT VERIFIED.

## Executable Verification & Failure Diagnostics
- **Verify**: Replay or inject a representative failure in a safe environment and assert the right alert fires within the target time with a usable runbook.
- **Anti-Patterns**: Collecting everything and querying nothing.; Alert fatigue tolerated as normal.
- **Failure Diagnostics**: A failing or ambiguous Verify result -> the first failing assertion or error line is the root cause, not the completion summary -> rerun the narrowest check named in Verify and inspect its first failing assertion.
