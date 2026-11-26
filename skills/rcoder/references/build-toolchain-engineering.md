# Build systems, compilers, linkers, and packaging

## Activate when
Build graph, compiler flags, linker behavior, CI toolchains, package publishing, cross-compilation, or reproducibility. Do not activate for application source behavior (use coding) or for a security supply-chain assessment (load supply-chain-security alongside this module).

## Mission and expertise
Own build-input control, dependency graph reasoning, artifact provenance, and reproducible packaging. A build is a dependency graph and a supply-chain boundary; changes must keep inputs pinned, generated outputs separated from source, and credentials out of artifacts.

## Mental model
A build is a dependency graph and supply-chain boundary. Reproducibility requires controlled inputs, environments, and artifact provenance. "It builds on my machine" is not a build system; a build system must be repeatable from a clean checkout with declared inputs.

## Prerequisites and reconnaissance
1. Identify build orchestrator, compiler/linker versions, lockfiles, environment variables, generated sources, caches, and target matrix.
2. Determine which files are generated and which are authoritative source.
3. Confirm where credentials and signing keys enter the process and that they are never emitted into artifacts or logs.
4. Verify the CI definition matches local build commands; mismatches are a common source of "works locally" failures.

## Procedure
1. Identify build orchestrator, compiler/linker versions, lockfiles, environment variables, generated sources, caches, and target matrix.
2. Trace the smallest affected dependency graph; avoid broad clean/rebuild unless stale state is proven.
3. Pin toolchains and actions to reviewed versions; verify provenance for downloaded binaries and plugins.
4. Separate generated artifacts from source; make build steps deterministic and keep credentials out of outputs.
5. Check ABI, symbols, LTO, optimization flags, debug info, licensing, and platform packaging.
6. Document cache invalidation and hermeticity assumptions.

## Decision tree
- Build fails after a dependency change → inspect lockfile and graph before clearing caches.
- Output differs between machines → identify nondeterministic inputs (timestamps, paths, locale, tool versions) and normalize them.
- Cross-compile target fails → verify target triple, sysroot, linker, and ABI flags in that order.
- Binary grows unexpectedly → inspect symbols, debug info, and static linkage before changing optimization.
- A plugin/action version is unpinned → pin to a reviewed version or refuse the dependency.
- Artifact may contain a secret → stop publishing, inspect the artifact, rotate the credential, and fix the build input.
- Build cannot be reproduced locally → record the gap and do not claim reproducibility.

## Tool strategy
Use the project's build orchestrator, lockfile tooling, compiler/linker version queries, dependency graph viewers, package inspectors, and checksum/attestation tools. Prefer offline or cached dependency resolution when available. Verify tool provenance and versions before use; never download an executable without a checksum or signature check.

## Advanced techniques
- **Hermetic inputs:** make the build depend only on declared files and pinned tools, not ambient environment state.
- **Reproducibility comparison:** build twice from a clean checkout and compare hashes; explain any variance.
- **Cache invalidation design:** key caches on the hash of declared inputs, not on timestamps.
- **Artifact inspection:** list package contents and scan for secrets, debug artifacts, and unintended files before publishing.
- **Staged rollout:** publish to a staging channel and verify installation before promoting a release.
- **SBOM and attestation:** generate a bill of materials and provenance attestation when the project's release policy requires it.

## Failure modes
- **Deleting arbitrary caches and lockfiles** → hidden nondeterminism and unreviewed upgrades → trace inputs and change only the cause.
- **Downloading executables without provenance verification** → supply-chain compromise → require checksum/signature and pin the source.
- **Publishing local debug outputs** → leaked paths, symbols, or secrets → build release artifacts from clean inputs.
- **Unpinned CI actions** → silent upstream change → pin to reviewed immutable versions.
- **Platform-specific path assumptions** → cross-platform breakage → use the build system's path APIs.

## Quality checklist
Build inputs are pinned or intentionally constrained; generated outputs are reproducible or variance is explained; artifacts exclude credentials and unreviewed debris; cross-target ABI and packaging are checked; CI and local commands agree.

## Anti-patterns
Global installs as build prerequisites; `latest` tags in reproducible builds; editing generated files; masking warnings in CI; copying artifacts from a developer machine as release output.

## Verification
Run clean and incremental builds, lockfile checks, reproducibility comparison, package inspection, signing/attestation checks, and the CI matrix. Record exact commands, versions, artifact hashes, and any platform that could not be tested.

## Output format
Graph/toolchain changes · artifact contents · provenance · reproducibility · build evidence · NOT VERIFIED platforms.

## Executable Verification & Failure Diagnostics
- **Verify**: Run clean and incremental builds, lockfile checks, reproducibility comparison, package inspection, signing/attestation checks, and the CI matrix.
- **Anti-Patterns**: Global installs as build prerequisites; `latest` tags in reproducible builds
- **Failure Diagnostics**: A failing or ambiguous Verify result -> the first failing assertion or error line is the root cause, not the completion summary -> rerun the narrowest check named in Verify and inspect its first failing assertion.
