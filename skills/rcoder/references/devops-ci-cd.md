# DevOps and CI/CD expert module

## Activate when
Build pipelines, CI, release automation, containers, infrastructure, deployment, signing, packaging, or rollback changes. Load supply-chain-security for dependency trust and build-toolchain-engineering for compiler/packaging internals.

## Mission and expertise
Treat a pipeline as privileged production code. Own permissions, trust boundaries for untrusted contributions, reproducibility, artifact integrity, gating, and rollback. A green build is not deployment readiness.

## Mental model
A pipeline is privileged production code. Reproducibility, least privilege, provenance, artifact integrity, and rollback matter as much as a green build. Fork pull requests and external inputs are untrusted even when they arrive through a trusted platform.

## Prerequisites and reconnaissance
1. Read workflows, required checks, branch rules, secrets, environments, and release flow.
2. Map events, permissions, untrusted PR/fork code, artifact boundaries, and production credentials.
3. Identify which steps run on which runner and what network egress they have.
4. Confirm the project's pinning policy and approved action/image sources.

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

## Decision tree
- Fork PR triggers a workflow → no deploy credentials, no secrets, no privileged write token.
- Third-party action is unpinned → pin to a reviewed immutable version or replace it.
- Artifact will be published → verify contents, checksums, and provenance before promotion.
- Step fails intermittently → bound retries and investigate the cause; do not mask the failure.
- Deploy needs elevated credentials → isolate in a protected environment with manual approval.
- Rollback path is undefined → block the release until it is defined and tested.
- Local syntax passes → report as local evidence only; remote CI remains NOT VERIFIED until observed.

## Tool strategy
Use workflow linters/parsers, container image scanners, artifact inspectors, checksum tools, and dry-run modes. Verify runner images and tool versions. Prefer ephemeral credentials and least-privilege tokens. Never echo secrets into logs.

## Advanced techniques
- **Stage separation:** build once, promote the same immutable artifact through environments.
- **Provenance chain:** record source commit, tool versions, artifact hash, and signature or attestation.
- **Untrusted-input boundary:** treat PR titles, branch names, and workflow inputs as data, never as commands.
- **Concurrency control:** use concurrency groups and environment locks to avoid overlapping deployments.
- **Health gates:** deploy only after test/security gates; verify health after deploy and auto-rollback on failure.
- **Failure diagnostics:** retain bounded logs and artifacts sufficient to reproduce the failure.

## Failure modes
- **Broad write permissions** → account compromise → scope permissions per job.
- **Remote script execution in privileged jobs** → code injection → pin sources and verify checksums.
- **Unsafe fork deployments** → credential theft → separate untrusted and trusted workflows.
- **Swallowing failed steps** → false green builds → fail visibly and record why.
- **Mutable caches** → nondeterministic builds → key caches on declared inputs.

## Quality checklist
Least privilege; untrusted PRs lack deploy credentials; explicit action/image trust policy; diagnosable failures; deployment health gate and rollback.

## Anti-patterns
`continue-on-error` without justification; deploying from a PR branch; publishing debug artifacts; caching credentials; treating local validation as remote CI proof.

## Verification
Lint workflow files, test scripts locally, inspect CI jobs/artifacts. Local syntax is not remote workflow proof. Record exact run URLs and job results when observed; otherwise mark NOT VERIFIED.

## Output format
Pipeline changes · trust/permissions · reproducibility · local/CI evidence · rollback · residual risks.

## Executable Verification & Failure Diagnostics
- **Verify**: Lint workflow files, test scripts locally, inspect CI jobs/artifacts.
- **Anti-Patterns**: `continue-on-error` without justification; deploying from a PR branch
- **Failure Diagnostics**: A failing or ambiguous Verify result -> the first failing assertion or error line is the root cause, not the completion summary -> rerun the narrowest check named in Verify and inspect its first failing assertion.
