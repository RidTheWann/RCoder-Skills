# Game, emulator, and real-time engine engineering

## Activate when
Game loops, rendering, simulation, emulation, input, audio, frame pacing, deterministic replay, or engine architecture.

## Mental model
Real-time systems need deterministic transitions, explicit frame budgets, bounded work, and observable synchronization between simulation and presentation.

## Procedure
1. Identify target hardware/API, frame rate, simulation tick, threading model, renderer, audio backend, and determinism requirements.
2. Separate guest/game semantics from host scheduling and presentation; document timing/state ownership.
3. Use fixed or bounded timestep policies; prevent unbounded queues and frame-dependent simulation.
4. Measure frame-time percentiles, GPU/CPU use, allocation spikes, synchronization stalls, and audio underruns.
5. Preserve save-state, replay, compatibility, and deterministic fixtures when core state changes.
6. Validate ISA/binary behavior against authoritative specifications, hardware tests, or differential implementations.

## Quality checklist
- [ ] Simulation and render timing are defined.
- [ ] Work queues and frame budgets are bounded.
- [ ] Determinism and compatibility are tested.
- [ ] Performance claims include repeatable measurements.

## Anti-patterns
- Changing game timing blindly to fix frame pacing.
- Mixing UI state into deterministic core state.
- Using average FPS as the only metric.

## Verification
Run deterministic regressions, scene/game fixtures, CPU/GPU profiling, frame-time captures, audio timing tests, and target builds.

## Output format
State timing model, affected subsystems, deterministic evidence, frame metrics, and compatibility limits.
