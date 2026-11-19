# Functional, immutable, and reactive programming

## Activate when
Pure functional design, immutable data, algebraic data types, reducers, reactive streams, or state-transition correctness. Use the language-specific module for runtime and tooling details.

## Mission and expertise
Own state modeling, purity/effect separation, and reactive lifetime correctness. Make invalid states unrepresentable where practical and verify invariants with property-based tests.

## Mental model
Make invalid states unrepresentable where practical. Separate pure transformations from effects and model state transitions explicitly. Hidden effects in "pure" code destroy testability and reasoning.

## Prerequisites and reconnaissance
1. Identify the language type system, effect model, immutability guarantees, and project conventions.
2. Map the domain states and transitions before writing combinators or stream pipelines.
3. Determine which effects exist (I/O, time, randomness, mutation) and where they are allowed.
4. Check existing property-testing and stream-testing setup.

## Procedure
1. Identify the language type system, effect model, immutability guarantees, and project conventions.
2. Represent domain states with explicit sum/product types and exhaustive matching.
3. Separate deterministic core logic from I/O, time, randomness, and mutable adapters.
4. Use explicit result/error types and preserve context at effect boundaries.
5. Check reactive subscriptions, backpressure, cancellation, and resource disposal.
6. Use property-based tests for algebraic laws, invariants, and state machines.

## Decision tree
- State has impossible combinations → model with distinct variants rather than optional fields.
- Effect needed in pure core → push it to an adapter boundary and inject an abstraction.
- Stream source is faster than consumer → apply backpressure; do not buffer without bound.
- Subscription may outlive its owner → tie disposal to a lifecycle and test cancellation.
- Error needs context → use a typed error channel and preserve cause at boundaries.
- Combinator chain is hard to read → prefer explicit steps; clarity beats cleverness.
- Law holds for all inputs → encode it as a property test.

## Tool strategy
Use the language's type checker, formatter, property-based testing framework, and stream/cancellation tests. Verify versions from manifests. Avoid adding an effect library unless the project already uses one or the complexity justifies it.

## Advanced techniques
- **Algebraic laws:** test identity, associativity, and round-trip properties rather than only examples.
- **State-machine testing:** generate random action sequences and assert invariants after each transition.
- **Effect adapters:** isolate time, randomness, and I/O behind injected interfaces for deterministic tests.
- **Backpressure strategy:** define bounded buffers, drop policies, and cancellation semantics explicitly.
- **Exhaustiveness checking:** make the compiler reject unhandled state variants.

## Failure modes
- **Over-abstracting simple flows** → unreadable code → use explicit steps.
- **Hiding effects in pure functions** → flaky tests and hidden dependencies → make effects explicit.
- **Ignoring cancellation/backpressure** → leaks and memory growth → define and test both.
- **Non-exhaustive matching** → unhandled states → use compiler checks.
- **Mutable shared state inside streams** → races → confine mutation to a single owner.

## Quality checklist
Pure core logic is independently testable; state transitions are exhaustive; effects and lifetimes are explicit; properties and invariants are tested.

## Anti-patterns
Deep point-free chains that obscure intent; swallowing errors in stream operators; global mutable subjects; unbounded buffering; treating immutability as a performance strategy without measurement.

## Verification
Run formatter/type checker, unit/property tests, state-machine tests, and integration tests for effect adapters. Record exact commands and results.

## Output format
State model · purity/effect boundaries · invariants · verification evidence.
