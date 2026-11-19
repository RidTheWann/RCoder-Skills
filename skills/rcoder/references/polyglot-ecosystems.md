# Polyglot language and framework ecosystems

## Activate when
Working with PHP/Laravel/Symfony, Ruby/Rails, Swift, Kotlin, Dart/Flutter, Scala, Elixir/Erlang, Haskell, Lua, R/Julia, or a less common runtime. Use programming-languages first when the correct ecosystem is unclear.

## Mission and expertise
Apply ecosystem-specific conventions, package management, runtime compatibility, and framework lifecycle correctly. Route to the exact platform and avoid assuming two frameworks share behavior.

## Mental model
Ecosystem conventions, package managers, runtime compatibility, and framework lifecycle matter as much as language syntax. Framework defaults are part of the specification and must be verified against version-matched sources.

## Prerequisites and reconnaissance
1. Identify language/framework/runtime versions, package manager, lockfiles, build targets, deployment runtime, and supported OS from source and CI.
2. Determine the framework's lifecycle and extension model before changing behavior.
3. Identify generated code, configuration conventions, and deployment packaging.
4. Verify commands against the project's manifests rather than memory.

## Procedure
1. Identify language/framework/runtime versions, package manager, lockfiles, build targets, deployment runtime, and supported OS from source and CI.
2. PHP: inspect composer.json/lock, PHP extensions, autoloading, framework middleware, ORM transactions, escaping, and worker lifecycle.
3. Ruby: inspect Gemfile/lock, Bundler, Rails/Rack versions, Active Record migrations, callbacks, background jobs, and security defaults.
4. Swift/iOS: inspect Swift tools version, Package.swift/Xcode project, concurrency isolation, Sendable, ARC, actors, entitlements, signing, and deployment targets.
5. Kotlin/Android/Multiplatform: inspect Gradle/catalogs, Kotlin and AGP versions, coroutine scopes, structured concurrency, nullability, lifecycle, JNI, and platform source sets.
6. Dart/Flutter: inspect pubspec.lock, SDK constraints, isolates, async streams, widget lifecycle, state management, platform channels, and release flavors.
7. Scala/JVM and functional ecosystems: inspect compiler/plugin versions, effect systems, implicit/given resolution, futures, resource scopes, and binary compatibility.
8. R/Julia/Lua and scripting/data ecosystems: inspect environment/manifest locks, native package dependencies, memory behavior, reproducibility, and input validation.
9. Use official versioned documentation for language-specific behavior; do not port idioms across frameworks without verifying semantic equivalence.

## Decision tree
- Exact ecosystem is unknown → determine it from manifests and lockfiles before acting.
- Framework version differs from memory → use version-matched official documentation.
- Concurrency model is actor/coroutine/isolate based → apply structured concurrency and lifecycle rules of that ecosystem.
- Framework upgrade is proposed → treat it as an explicit compatibility decision with tests.
- Native extension or platform channel → verify ABI, ownership, and version compatibility.
- No local toolchain → mark runtime verification NOT VERIFIED and avoid claiming compatibility.

## Tool strategy
Use the ecosystem's own formatter, linter, type checker, package manager, and test runner. Verify versions from CLI output and manifests. Prefer official documentation and reproducible local fixtures over general search results.

## Advanced techniques
- **Framework-default audit:** verify security, validation, and serialization defaults for the exact version.
- **Lockfile discipline:** review transitive changes and lifecycle scripts on every dependency update.
- **Lifecycle mapping:** document initialization, request, background, and shutdown hooks used by the framework.
- **Cross-framework idioms:** prove semantic equivalence before porting a pattern between ecosystems.
- **Platform boundary tests:** isolate and test native bridges, ABI assumptions, and serialization formats.

## Failure modes
- **Guessing framework conventions from language familiarity** → wrong idioms → verify the framework version.
- **Upgrading compilers or packages as an incidental fix** → unrelated breakage → handle upgrades explicitly.
- **Applying synchronous assumptions to coroutine/actor systems** → races and deadlocks → learn the concurrency model.
- **Ignoring platform-specific constraints** → build or store rejection → verify target matrix.

## Quality checklist
Exact runtime and framework constraints are documented; package locks and toolchains remain consistent; async, lifecycle, and resource ownership are explicit; platform-specific APIs are isolated and tested.

## Anti-patterns
Copying patterns across frameworks without verification; pinning nothing; disabling framework security defaults; assuming one OS for all targets.

## Verification
Run the ecosystem's pinned formatter, linter, type checker, unit/integration suite, production build, and platform-specific validation. Record versions and mark unavailable targets NOT VERIFIED.

## Output format
Language/framework versions · lifecycle/concurrency decisions · package impact · commands · platform limitations.
