# S08 — Polyglot monorepo reconnaissance

## Fixture
A repository contains a Rust service, TypeScript frontend, and Python background jobs. A shared API schema is consumed/generated in more than one package.

## Task
Run the stack detector, inspect each manifest and CI entry point, trace schema consumers/generated clients, and verify actual commands before changing the API.

## Required evidence
- Detector output or explicit explanation why unavailable.
- Each package manifest and quality entry point inspected.
- Shared contract ownership and generated artifacts identified.
- Commands verified from local scripts/config rather than guessed.
