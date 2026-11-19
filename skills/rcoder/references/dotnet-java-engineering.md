# .NET, C#, and Java/JVM engineering

## Activate when
C#, F#, .NET, Java, Kotlin/JVM, Gradle/Maven, JVM services, desktop clients, or runtime interop. Use dotnet-java-engineering for both families but verify the exact SDK/JDK and framework before applying idioms.

## Mission and expertise
Own correctness across framework versions, package resolution, GC, threading, assembly/class loading, and platform compatibility. Preserve nullable/type-safety settings and public API compatibility unless a change is explicitly requested.

## Mental model
Framework versions, package resolution, threading, GC, assembly/class loading, and platform compatibility determine behavior. The compiler, runtime, and serialization settings are part of the specification; a change in target framework is a compatibility decision, not a configuration tweak.

## Prerequisites and reconnaissance
1. Inspect global.json, target frameworks, Directory.Build files, NuGet locks/config, pom.xml/build.gradle, toolchains, and CI.
2. Determine the supported SDK/JDK versions and whether multiple target frameworks are built.
3. Identify analyzers, warnings-as-errors policy, nullable settings, and public API baselines.
4. Check reflection, serialization, DI, and dynamic-loading surfaces as trust boundaries.

## Procedure
1. Inspect global.json, target frameworks, Directory.Build files, NuGet locks/config, pom.xml/build.gradle, toolchains, and CI.
2. Preserve nullable/type-safety settings, analyzers, warnings, and dependency constraints.
3. Define cancellation, async lifetime, exception propagation, synchronization context, and resource disposal.
4. Review reflection, serialization, dependency injection, configuration, and dynamic loading as trust boundaries.
5. Check public API compatibility, assembly/module versioning, JNI/PInvoke boundaries, and platform-specific APIs.
6. Profile allocations, GC pressure, startup, JIT/AOT, and thread contention before tuning.

## Decision tree
- Async method called synchronously → redesign the call chain; do not block on async work.
- Resource cleanup needed → use deterministic disposal (`using`/try-with-resources), not finalizers.
- Public API change → check binary/source compatibility and update baselines deliberately.
- Reflection/deserialization with untrusted input → constrain types and validate before binding.
- Target framework upgrade → treat as an explicit decision with a compatibility matrix.
- Interop boundary → verify marshalling, calling convention, lifetime, and exception translation.
- Performance complaint → profile allocations and contention before changing GC settings.

## Tool strategy
Use locked restore, analyzers, formatters, API compatibility tools, profilers, and target builds. Verify SDK/JDK versions from CLI output and manifests. Do not rely on IDE behavior as proof of build behavior.

## Advanced techniques
- **Cancellation propagation:** pass tokens through every async layer and verify shutdown under cancellation.
- **API baseline diff:** compare public API surfaces between versions before release.
- **Allocation profiling:** identify GC pressure with evidence before tuning heap settings.
- **Serialization boundaries:** constrain bindable types and reject unexpected members on untrusted input.
- **Multi-target matrix:** build and test every declared target framework, marking unavailable ones NOT VERIFIED.

## Failure modes
- **Sync-over-async blocking** → deadlocks and thread starvation → make the call chain async.
- **Finalizers as routine cleanup** → nondeterministic resource release → use deterministic disposal.
- **Framework change without analysis** → compatibility break → verify target matrix.
- **Unconstrained reflection** → security risk → restrict types and inputs.
- **Interop exception crossing boundary** → crashes → translate explicitly at the boundary.

## Quality checklist
SDK/JDK and target frameworks match supported versions; cancellation and disposal are correct; public API and binary compatibility are considered; reflection and deserialization are constrained.

## Anti-patterns
Ignoring compiler warnings; catching all exceptions and continuing; using static mutable state for request data; shipping debug-only configuration; treating a single target build as full coverage.

## Verification
Run locked restore, analyzers, formatter, unit/integration tests, packaging, and every declared target build. Record exact SDK/JDK versions and results.

## Output format
SDK/JDK versions · framework changes · API/ABI effects · diagnostics · measured performance.
