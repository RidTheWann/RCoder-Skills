# Cloud, container, and infrastructure security

## Activate when
Cloud architecture, IAM, Kubernetes, containers, IaC, CI/CD deployment, network policies, or production hardening. Load threat-modeling for system-level analysis and supply-chain-security for artifact trust.

## Mission and expertise
Own least-privilege, exposure, provenance, and deployment-gate correctness across control plane, workload identity, network, storage, and runtime. Never modify production infrastructure without authorization.

## Mental model
The control plane, workload identity, build pipeline, network, storage, and runtime form one attack surface. A green image scan does not prove runtime safety; identity and configuration determine actual exposure.

## Prerequisites and reconnaissance
1. Identify provider, account/project boundaries, regions, shared-responsibility assumptions, IaC, cluster version, and runtime.
2. Determine who can approve changes and which environments are production.
3. Establish the current network exposure, IAM trust policies, and secret-injection mechanism from configuration.
4. Check whether policy-as-code and drift detection exist.

## Procedure
1. Identify provider, account/project boundaries, regions, shared-responsibility assumptions, IaC, cluster version, and runtime.
2. Review IAM trust policies, workload identity, privilege scope, public exposure, segmentation, metadata access, and audit logging.
3. Check base-image provenance, non-root execution, capabilities, read-only filesystems, seccomp, image scanning, and secret injection.
4. Review Kubernetes RBAC, service accounts, admission controls, network policies, pod security, ingress, and secret protection.
5. Check IaC plan/state, drift, remote-state encryption, CI credentials, artifact signing, and approval boundaries.
6. Propose reviewed diffs and rollback steps; never modify production infrastructure without authorization.

## Decision tree
- Public endpoint found → verify it is intentional and protected by authentication/authorization and rate limits.
- Workload uses long-lived credentials → migrate to workload identity or short-lived tokens.
- Container runs as root → switch to a non-root user with minimal capabilities.
- IaC plan shows destructive change → require explicit review and a rollback plan before apply.
- Image has unpatched advisories → assess reachability and exposure, not only the scanner count.
- Secret stored in manifests → move to an approved secret manager and rotate the exposed value.
- Metadata endpoint reachable from workloads → restrict it and verify SSRF defenses.

## Tool strategy
Use IaC plan tools, policy-as-code checks, image scanners, cluster configuration tests, and least-privilege reviews in non-production first. Verify provider and cluster versions. Use synthetic accounts and disposable environments; never paste credentials into analysis artifacts.

## Advanced techniques
- **Trust-policy graph:** map which principals can assume which roles and reach which resources.
- **Blast-radius analysis:** determine what a compromised workload identity could access.
- **Admission policy tests:** verify that unsafe pods are rejected before they can be scheduled.
- **Drift detection:** compare live configuration to the declared IaC state and explain differences.
- **Rollback rehearsal:** validate that a proposed change can be reversed from a known-good artifact.

## Failure modes
- **Long-lived cloud admin keys in CI** → credential theft → use workload identity and short-lived tokens.
- **Applying unreviewed IaC directly to production** → outage → require plan review and approval.
- **Treating image scanning as proof of runtime security** → false assurance → review runtime controls.
- **Overly permissive RBAC/network policy** → lateral movement → least privilege and segmentation.
- **Unprotected state backend** → supply-chain and data risk → encrypt and restrict access.

## Quality checklist
Workloads use least privilege and safe defaults; public surfaces and egress are intentional; images/IaC have traceable provenance; secrets and state are protected.

## Anti-patterns
Privileged containers by default; wildcard IAM policies; unencrypted remote state; applying changes from a developer workstation without review; claiming production security from a plan that was never applied.

## Verification
Run IaC plans, policy-as-code, image checks, cluster config tests, and least-privilege reviews in non-production first. Record exact plan output and mark production changes NOT VERIFIED until observed.

## Output format
Provider/scope · risks · controls · plan evidence · deployment gates · shared-responsibility gaps.

## Executable Verification & Failure Diagnostics
- **Verify**: Run IaC plans, policy-as-code, image checks, cluster config tests, and least-privilege reviews in non-production first.
- **Anti-Patterns**: Privileged containers by default; wildcard IAM policies
- **Failure Diagnostics**: A failing or ambiguous Verify result -> the first failing assertion or error line is the root cause, not the completion summary -> rerun the narrowest check named in Verify and inspect its first failing assertion.
