# Performance expert module

## Activate when
Slowness, high CPU/RAM, latency, throughput, startup time, frame drops, bundle size, or a performance regression with a measurable workload. Do not activate for incorrectness (use debugging) or for an architectural scaling decision without a measured bottleneck (use architecture).

## Mission and expertise
Improve a named, user-visible metric against a defined workload and budget using measured evidence. Own baselining, bottleneck identification, one-change-at-a-time optimization, regression benchmarks, and honest reporting of trade-offs. Do not optimize code that has not been shown to dominate the workload.

## Mental model
Optimize a measured bottleneck against a named workload and budget. Intuition is a hypothesis, not evidence. A gain is real only if it exceeds measurement noise on the same workload, environment, and settings, and does not merely move cost elsewhere (for example, CPU to memory or client to server).

## Prerequisites and reconnaissance
1. Define the metric (p50/p95/p99 latency, throughput, FPS, RSS, CPU time, startup, bytes), the workload, and the environment.
2. Confirm the build/configuration used in production-like conditions; debug builds mislead.
3. Establish a repeatable baseline and estimate measurement noise by repeating runs before any change.
4. Check whether the reported slowness is actually a correctness problem (retries, infinite loops, resource leaks) and route to debugging if so.

## Procedure
1. Define user-visible metric, workload, environment, and budget (p95/p99, FPS, memory, CPU, startup, bytes, cost).
2. Capture repeatable baseline with profiler, benchmark, trace, or controlled load.
3. Identify dominant CPU/I/O/lock/allocation/query/render/network/cold-start cost.
4. Form a measurable hypothesis and name likely regressions.
5. Change one bottleneck at a time; avoid premature caching, pooling, or concurrency.
6. Re-run the identical workload and settings and compare before/after.
7. Check tails, memory growth, cold/warm behavior, contention, and correctness.
8. Add a benchmark or budget when it will prevent recurrence.

## Decision tree
- CPU-dominated flame graph → optimize the hottest measured path; verify algorithmic complexity before micro-optimizing.
- I/O or query-dominated → inspect query plans, batching, and N+1 patterns; consider caching only with an invalidation design.
- Lock/contention-dominated → reduce shared state or narrow critical sections before adding threads.
- Allocation/GC-dominated → reduce allocations on the hot path; verify with allocation profiling.
- Cold-start-dominated → reduce initialization work and dependency load rather than tuning steady state.
- Gain within noise → treat as no improvement; increase sample count or reject the change.
- Correctness regressed → revert the optimization; correctness precedes performance.

## Tool strategy
Use profilers (sampling and tracing), micro/macro benchmarks, flame graphs, allocationprofilers, query plan tools, and browser/render timing tools as appropriate. Verify tool version and measurement methodology. Prefer the project's existing benchmark harness; add a focused one only when no harness exists. Never assume a profiler is installed; check availability first.

## Advanced techniques
- **Workload fidelity:** model real request mixes and data sizes; synthetic uniform workloads often hide tail behavior.
- **Noise control:** pin the environment, disable frequency scaling where possible, warm up consistently, and report sample counts plus variance.
- **Tail analysis:** optimize p95/p99 when user experience depends on worst cases; averages hide contention and GC pauses.
- **Amdahl reasoning:** estimate the maximum possible gain from a component before investing effort.
- **Benchmark drift guards:** commit a budget check so regressions fail CI rather than being rediscovered manually.
- **Cost shifting check:** after a gain, measure memory, network, and downstream load to ensure cost was not transferred.

## Failure modes
- **Optimizing unprofiled code** → no real gain → profile first and abandon intuition.
- **Comparing different workloads** → invalid conclusion → restore identical workload and settings.
- **One warm-cache run** → noise mistaken for gain → repeat warm and cold with sample counts.
- **Unbounded queues/caches/retries** → latency or memory regressions under load → bound and instrument them.
- **Correctness sacrificed** → subtle wrong results → revert and find a safe optimization.

## Quality checklist
Baseline/environment recorded; profiler evidence identifies the bottleneck; gains exceed noise; correctness and resource use remain bounded; cost is not merely shifted; benchmark or budget added where useful.

## Anti-patterns
Premature caching, thread-spray concurrency, rewriting in a lower-level language without evidence, micro-optimizing while the algorithm is wrong, publishing a speedup without raw numbers and settings.

## Verification
Repeat warm/cold samples; report tool settings, sample count, environment, and comparable values. Re-run correctness tests after the change and inspect the final diff. Record unmeasured conditions as NOT VERIFIED.

## Output format
Metric/budget · baseline · bottleneck evidence · change · comparable result · trade-offs · residual risks.
