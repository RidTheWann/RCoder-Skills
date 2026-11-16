# S09 — CI permissions and deployment

## Fixture
One workflow runs on pull requests from forks and deploys to production on pushes to main. It uses a broadly scoped token and third-party actions by mutable tags.

## Task
Map events and trust boundaries, reduce permissions, isolate deployment secrets, pin actions under the repository policy, and define deployment health and rollback gates.

## Required evidence
- Event/branch/fork execution path.
- Job-level least privilege and secret exposure analysis.
- Untrusted PR code cannot access production credentials.
- Immutable action references, artifact integrity, deployment checks and rollback.
