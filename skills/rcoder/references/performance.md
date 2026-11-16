# Performance expert module

## Activate when
Slowness, high CPU/RAM, latency, throughput, startup, frame drops, bundle size, or performance regression.

## Mental model
Optimize a measured bottleneck against a named workload and budget. Intuition is a hypothesis, not evidence.

## Procedure
1. Define user-visible metric, workload, environment, and budget (p95/p99, FPS, memory, CPU, startup, bytes, cost).
2. Capture repeatable baseline with profiler, benchmark, trace, or controlled load.
3. Identify dominant CPU/I/O/lock/allocation/query/render/network/cold-start cost.
4. Form a measurable hypothesis and name likely regressions.
5. Change one bottleneck at a time; avoid premature caching, pooling, or concurrency.
6. Re-run identical workload/settings and compare before/after.
7. Check tails, memory growth, cold/warm behavior, contention, and correctness.
8. Add a benchmark/budget when it will prevent recurrence.

## Quality checklist
Baseline/environment recorded; profiler evidence identifies bottleneck; gains exceed noise; correctness/resources remain bounded; cost is not merely shifted.

## Anti-patterns
Optimizing unprofiled code; comparing different workloads; one warm-cache run; unbounded queues/caches/retries.

## Verification
Repeat warm/cold samples; report tool settings, sample count, and comparable values.

## Output format
Metric/budget · baseline · bottleneck evidence · change · comparable result · trade-offs.
