# Fixture: compiler regression

Repository contains `bench.c`, `Makefile`, and a CI log. Two toolchains are available locally:
`cc --version` reports 13.2.0 and `cc-14 --version` reports 14.1.0. The benchmark `bench.c` has a
deterministic inner loop; run each binary three times and record the median. Original binaries must
be copied to `artifacts/` and hashed with `sha256sum` before any change. The suspected cause is a
loop-invariant code motion pass, but this is a hypothesis, not a conclusion. No optimization flag
may be removed without a controlled comparison. The final report must separate measured numbers
from interpretation and include the exact commands used.
