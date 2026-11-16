# Go engineering

## Activate when
Go modules, services, CLIs, goroutines, channels, contexts, networking, or Go performance.

## Mental model
Go systems depend on package/module boundaries, explicit error flow, context cancellation, goroutine lifetime, and memory visibility.

## Procedure
1. Read go.mod, go.sum, toolchain directive, workspace files, build tags, generated-code policy, and CI.
2. Use context.Context for request cancellation and deadlines; propagate it across I/O and API boundaries.
3. Assign clear ownership to goroutines/channels; define shutdown and prevent leaks.
4. Check shared-state synchronization and run race-enabled tests on relevant paths.
5. Wrap errors with useful context while preserving errors.Is/errors.As behavior.
6. Use pprof and benchmarks before optimizing allocations or concurrency.

## Quality checklist
- [ ] Go version and module graph are stable.
- [ ] Goroutine lifetimes and cancellation are explicit.
- [ ] Shared state is race-free.
- [ ] Errors remain inspectable.

## Anti-patterns
- Launching goroutines without an owner or shutdown path.
- Using channels where direct ownership is clearer.
- Ignoring errors or context cancellation.

## Verification
Run gofmt, go vet, go test ./..., race-enabled tests, target builds, and benchmarks for performance changes.

## Output format
Describe module impact, concurrency ownership, cancellation, checks, race results, and benchmark deltas.
