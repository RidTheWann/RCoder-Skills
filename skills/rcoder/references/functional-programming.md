# Functional, immutable, and reactive programming

## Activate when
Pure functional design, immutable data, algebraic data types, reducers, reactive streams, or state-transition correctness.

## Mental model
Make invalid states unrepresentable where practical. Separate pure transformations from effects and model state transitions explicitly.

## Procedure
1. Identify the language type system, effect model, immutability guarantees, and project conventions.
2. Represent domain states with explicit sum/product types and exhaustive matching.
3. Separate deterministic core logic from I/O, time, randomness, and mutable adapters.
4. Use explicit result/error types and preserve context at effect boundaries.
5. Check reactive subscriptions, backpressure, cancellation, and resource disposal.
6. Use property-based tests for algebraic laws, invariants, and state machines.

## Quality checklist
- [ ] Pure core logic is independently testable.
- [ ] State transitions are exhaustive.
- [ ] Effects and lifetimes are explicit.
- [ ] Properties and invariants are tested.

## Anti-patterns
- Over-abstracting simple flows into opaque combinators.
- Hiding effects in supposedly pure functions.
- Ignoring stream cancellation or backpressure.

## Verification
Run formatter/type checker, unit/property tests, state-machine tests, and integration tests for effect adapters.

## Output format
Explain state model, purity/effect boundaries, invariants, and verification.
