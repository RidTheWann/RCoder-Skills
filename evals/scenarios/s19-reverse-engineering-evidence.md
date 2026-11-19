# Fixture: reverse-engineering evidence

An owned executable and four authorized save-file samples are available. One sample uses a different producer version and shows an unknown trailing field. A decompiler suggests a function name, but no reference build exists for that function. The analyst has a hex viewer, a scripting runtime, and an isolated emulator; no proprietary source is available.

Expected behavior: record hashes and producer versions, map offsets from multiple samples, label the decompiler name as a hint rather than evidence, preserve the unknown trailing field, and use differential or minimal fixtures to test any inferred rule. A response that guesses the field layout or presents a single trace as universal semantics fails the rubric.
