# DevOps and CI/CD expert module

## Activate when
Build pipelines, CI, release automation, containers, infrastructure, deployment, signing, packaging, or rollback changes.

## Mental model
A pipeline is privileged production code. Reproducibility, least privilege, provenance, artifact integrity, and rollback matter as much as a green build.

## Procedure
1. Read workflows, required checks, branch rules, secrets, environments, and release flow.
2. Map events, permissions, untrusted PR/fork code, artifact boundaries, and production credentials.
3. Pin actions/images/toolchains per project trust policy.
4. Minimize token permissions and scope secrets to the smallest job/environment.
5. Separate build/test/package/publish/deploy stages and gate production.
6. Cache only reproducible inputs; never cache secrets or mutable deployment state.
7. Keep logs, artifacts, checksums, provenance, and rollback/recovery steps.
8. Bound retries/timeouts/concurrency and prevent overlapping deployments.
9. Run syntax/lint/dry-run checks and confirm the actual remote CI result.

## Quality checklist
Least privilege; untrusted PRs lack deploy credentials; explicit action/image trust policy; diagnosable failures; deployment health gate and rollback.

## Anti-patterns
Broad write permissions; remote script execution in privileged jobs; unsafe fork deployments; swallowing failed steps without reason.

## Verification
Lint workflow files, test scripts locally, inspect CI jobs/artifacts. Local syntax is not remote workflow proof.

## Output format
Pipeline changes · trust/permissions · reproducibility · local/CI evidence · rollback · residual risks.
