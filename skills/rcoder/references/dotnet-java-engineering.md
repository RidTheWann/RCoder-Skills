# .NET, C#, and Java/JVM engineering

## Activate when
C#, F#, .NET, Java, Kotlin/JVM, Gradle/Maven, JVM services, desktop clients, or runtime interop.

## Mental model
Framework versions, package resolution, threading, GC, assembly/class loading, and platform compatibility determine behavior.

## Procedure
1. Inspect global.json, target frameworks, Directory.Build files, NuGet locks/config, pom.xml/build.gradle, toolchains, and CI.
2. Preserve nullable/type-safety settings, analyzers, warnings, and dependency constraints.
3. Define cancellation, async lifetime, exception propagation, synchronization context, and resource disposal.
4. Review reflection, serialization, dependency injection, configuration, and dynamic loading as trust boundaries.
5. Check public API compatibility, assembly/module versioning, JNI/PInvoke boundaries, and platform-specific APIs.
6. Profile allocations, GC pressure, startup, JIT/AOT, and thread contention before tuning.

## Quality checklist
- [ ] SDK/JDK and target frameworks match supported versions.
- [ ] Cancellation and disposal are correct.
- [ ] Public API and binary compatibility are considered.
- [ ] Reflection and deserialization are constrained.

## Anti-patterns
- Sync-over-async blocking.
- Using finalizers as routine resource management.
- Changing target frameworks without compatibility analysis.

## Verification
Run locked restore, analyzers, formatter, unit/integration tests, packaging, and every declared target build.

## Output format
Report SDK/JDK versions, framework changes, API/ABI effects, diagnostics, and measured performance.
