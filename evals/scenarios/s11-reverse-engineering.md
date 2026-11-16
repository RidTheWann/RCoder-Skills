# S11 — Evidence-led reverse engineering

## Fixture
An authorized native executable contains an undocumented routine that mutates state. A second reference build and a small valid input corpus are available.

## Expected evidence
- Artifact hashes, architecture, ABI assumptions, tool versions, and acquisition scope.
- Static call graph/data references distinguished from observed runtime traces.
- Machine state before/after the relevant routine and confidence for every claim.
- A minimized differential test reproducing confirmed behavior.

## Failure signals
- Decompiler pseudocode is treated as original source.
- A single trace is generalized without corroboration.
- Missing ABI or memory effects are guessed.
- Untrusted binaries are executed on the host.
