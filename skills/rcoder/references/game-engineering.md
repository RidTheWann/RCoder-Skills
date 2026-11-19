# Game, emulator, and real-time engine engineering

## Activate when
Game loops, rendering, simulation, emulation, input, audio, frame pacing, deterministic replay, or engine architecture. Use reverse-engineering for undocumented ISA/format semantics and performance for measurement discipline.

## Mission and expertise
Own timing-model, determinism, frame-budget, and compatibility correctness. Separate guest/game semantics from host scheduling and presentation, and verify behavior with repeatable measurements and fixtures.

## Mental model
Real-time systems need deterministic transitions, explicit frame budgets, bounded work, and observable synchronization between simulation and presentation. Average FPS hides stalls; frame-time percentiles reveal them.

## Prerequisites and reconnaissance
1. Identify target hardware/API, frame rate, simulation tick, threading model, renderer, audio backend, and determinism requirements.
2. Determine what must be deterministic (replay, networking, tests) and what may vary (presentation timing).
3. Identify existing fixtures, save-state formats, and compatibility baselines.
4. Confirm profiling tools and target hardware availability before making performance claims.

## Procedure
1. Identify target hardware/API, frame rate, simulation tick, threading model, renderer, audio backend, and determinism requirements.
2. Separate guest/game semantics from host scheduling and presentation; document timing/state ownership.
3. Use fixed or bounded timestep policies; prevent unbounded queues and frame-dependent simulation.
4. Measure frame-time percentiles, GPU/CPU use, allocation spikes, synchronization stalls, and audio underruns.
5. Preserve save-state, replay, compatibility, and deterministic fixtures when core state changes.
6. Validate ISA/binary behavior against authoritative specifications, hardware tests, or differential implementations.

## Decision tree
- Replay determinism required → remove host-time and uninitialized-state dependencies; hash state at intervals.
- Frame pacing unstable → measure before changing the timestep; distinguish simulation cost from presentation stalls.
- Emulator timing wrong → consult authoritative ISA/hardware documentation and use differential tests.
- Save format changed → version it and preserve backward compatibility or provide migration.
- Audio underruns → bound audio-callback work and avoid allocation in the callback.
- Input feels wrong → check polling cadence and event ordering before changing game logic.
- Performance claim → report frame-time percentiles, environment, and repeatable workload.

## Tool strategy
Use deterministic regressions, scene fixtures, CPU/GPU profilers, frame-time captures, audio timing tests, and target builds. Verify SDK/driver versions. Treat hardware measurements as evidence only on the tested configuration.

## Advanced techniques
- **State hashing:** hash deterministic core state at checkpoints to localize divergence in replays.
- **Frame-time budgets:** allocate a per-frame budget and assert that no stage exceeds it.
- **Differential emulation:** compare an implementation against a reference on minimal instruction sequences.
- **Bounded queues:** cap pending frames, audio buffers, and tasks with explicit overflow policy.
- **Snapshot compatibility:** version save states and test loading older fixtures.

## Failure modes
- **Changing game timing blindly to fix frame pacing** → gameplay regressions → measure the actual bottleneck.
- **Mixing UI state into deterministic core state** → broken replays → separate presentation from simulation.
- **Using average FPS as the only metric** → hidden stalls → report percentiles.
- **Unbounded queues** → latency growth and memory use → bound them.
- **Guessing undocumented ISA behavior** → incorrect emulation → use evidence-led analysis.

## Quality checklist
Simulation and render timing are defined; work queues and frame budgets are bounded; determinism and compatibility are tested; performance claims include repeatable measurements.

## Anti-patterns
Frame-rate-dependent physics; allocation in audio callbacks; global mutable singletons for game state; treating an emulator as ground truth for hardware behavior; shipping without replay regression.

## Verification
Run deterministic regressions, scene/game fixtures, CPU/GPU profiling, frame-time captures, audio timing tests, and target builds. Record environment and results; mark unavailable targets NOT VERIFIED.

## Output format
Timing model · affected subsystems · deterministic evidence · frame metrics · compatibility limits.
