# Go engineering

## Activate when
Go modules, services, CLIs, goroutines, channels, contexts, networking, or Go performance. Use systems-programming for cgo, ABI, or memory-model questions that cross into native code.

## Mission and expertise
Own module-boundary, error-flow, cancellation, concurrency-ownership, and race-freedom decisions in Go code. Preserve module stability and keep errors inspectable.

## Mental model
Go systems depend on package/module boundaries, explicit error flow, context cancellation, goroutine lifetime, and memory visibility. Concurrency is a design responsibility: every goroutine needs an owner and a shutdown path.

## Prerequisites and reconnaissance
1. Read go.mod, go.sum, toolchain directive, workspace files, build tags, generated-code policy, and CI.
2. Determine which packages are public API and which are internal implementation.
3. Identify existing context propagation, cancellation, and shutdown patterns before adding concurrency.
4. Check whether race-enabled tests and benchmarks are part of the project gate.

## Procedure
1. Read go.mod, go.sum, toolchain directive, workspace files, build tags, generated-code policy, and CI.
2. Use context.Context for request cancellation and deadlines; propagate it across I/O and API boundaries.
3. Assign clear ownership to goroutines/channels; define shutdown and prevent leaks.
4. Check shared-state synchronization and run race-enabled tests on relevant paths.
5. Wrap errors with useful context while preserving errors.Is/errors.As behavior.
6. Use pprof and benchmarks before optimizing allocations or concurrency.

## Decision tree
- Work is independent and bounded → a goroutine with explicit cancellation and a wait path is acceptable.
- Shared mutable state → prefer ownership transfer or synchronization with documented invariants.
- Error needs classification → wrap with context and preserve sentinel/type identity.
- Request crosses a boundary → pass context rather than creating a new background context.
- Channel used only to sequence one call → prefer a direct call; channels are for ownership and coordination.
- Race detector reports a problem → fix the synchronization, do not silence the detector.
- Performance claim → benchmark and profile with the same workload before and after.

## Tool strategy
Use gofmt, go vet, go test (including `-race`), build tags for target builds, pprof, and benchmarks. Verify Go version from the toolchain directive and CLI. Do not assume cgo or external tools are available in every target environment.

## Advanced techniques
- **Goroutine ownership ledger:** record who starts, cancels, and waits for each long-lived goroutine.
- **Context discipline:** derive child contexts with deadlines and always call cancel to release resources.
- **Error identity:** wrap with `%w` so errors.Is/errors.As keep working across layers.
- **Race-driven design:** use the race detector as a design check, not just a test step.
- **Benchmark discipline:** report allocation counts and nanoseconds per operation with a stable workload.

## Failure modes
- **Goroutines without owner or shutdown path** → leaks → add cancellation and wait groups.
- **Channels where direct ownership is clearer** → needless complexity → simplify.
- **Ignoring errors or cancellation** → silent failures → handle or propagate explicitly.
- **Data races under load** → corruption → fix synchronization and re-run race tests.
- **Lost error identity** → broken classification → wrap correctly.

## Quality checklist
Go version and module graph are stable; goroutine lifetimes and cancellation are explicit; shared state is race-free; errors remain inspectable.

## Anti-patterns
`context.Background()` inside request handlers; swallowing errors with `_ =`; unbounded worker pools; global mutable registries without synchronization; adding dependencies for standard-library tasks.

## Verification
Run gofmt, go vet, go test ./..., race-enabled tests, target builds, and benchmarks for performance changes. Record Go version and any target that could not be tested.

## Output format
Module impact · concurrency ownership · cancellation · checks · race results · benchmark deltas.
