# Polyglot language and framework ecosystems

## Activate when
Working with PHP/Laravel/Symfony, Ruby/Rails, Swift, Kotlin, Dart/Flutter, Scala, Elixir/Erlang, Haskell, Lua, R/Julia, or a less common runtime.

## Mental model
Ecosystem conventions, package managers, runtime compatibility, and framework lifecycle matter as much as language syntax. Route to the exact platform and avoid assuming two frameworks share behavior.

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

## Quality checklist
- [ ] Exact runtime and framework constraints are documented.
- [ ] Package locks and toolchains remain consistent.
- [ ] Async, lifecycle, and resource ownership are explicit.
- [ ] Platform-specific APIs are isolated and tested.

## Anti-patterns
- Guessing framework conventions from language familiarity.
- Upgrading compilers or packages as an incidental fix.
- Applying synchronous assumptions to coroutine/actor systems.

## Verification
Run the ecosystem's pinned formatter, linter, type checker, unit/integration suite, production build, and platform-specific validation.

## Output format
Report language/framework versions, lifecycle/concurrency decisions, package impact, commands, and platform limitations.
