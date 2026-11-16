# Build systems, compilers, linkers, and packaging

## Activate when
Build graph, compiler flags, linker behavior, CI toolchains, package publishing, cross-compilation, or reproducibility.

## Mental model
A build is a dependency graph and supply-chain boundary. Reproducibility requires controlled inputs, environments, and artifact provenance.

## Procedure
1. Identify build orchestrator, compiler/linker versions, lockfiles, environment variables, generated sources, caches, and target matrix.
2. Trace the smallest affected dependency graph; avoid broad clean/rebuild unless stale state is proven.
3. Pin toolchains and actions to reviewed versions; verify provenance for downloaded binaries and plugins.
4. Separate generated artifacts from source; make build steps deterministic and keep credentials out of outputs.
5. Check ABI, symbols, LTO, optimization flags, debug info, licensing, and platform packaging.
6. Document cache invalidation and hermeticity assumptions.

## Quality checklist
- [ ] Build inputs are pinned or intentionally constrained.
- [ ] Generated outputs are reproducible or variance is explained.
- [ ] Artifacts exclude credentials and unreviewed debris.
- [ ] Cross-target ABI and packaging are checked.

## Anti-patterns
- Deleting arbitrary caches and lockfiles to fix builds.
- Downloading executables without provenance verification.
- Publishing local debug outputs as release artifacts.

## Verification
Run clean/incremental builds, lockfile checks, reproducibility comparison, package inspection, signing/attestation checks, and CI matrix.

## Output format
Describe graph/toolchain changes, artifact contents, provenance, reproducibility, and build evidence.
