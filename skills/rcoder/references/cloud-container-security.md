# Cloud, container, and infrastructure security

## Activate when
Cloud architecture, IAM, Kubernetes, containers, IaC, CI/CD deployment, network policies, or production hardening.

## Mental model
The control plane, workload identity, build pipeline, network, storage, and runtime form one attack surface.

## Procedure
1. Identify provider, account/project boundaries, regions, shared-responsibility assumptions, IaC, cluster version, and runtime.
2. Review IAM trust policies, workload identity, privilege scope, public exposure, segmentation, metadata access, and audit logging.
3. Check base-image provenance, non-root execution, capabilities, read-only filesystems, seccomp, image scanning, and secret injection.
4. Review Kubernetes RBAC, service accounts, admission controls, network policies, pod security, ingress, and secret protection.
5. Check IaC plan/state, drift, remote-state encryption, CI credentials, artifact signing, and approval boundaries.
6. Propose reviewed diffs and rollback steps; never modify production infrastructure without authorization.

## Quality checklist
- [ ] Workloads use least privilege and safe defaults.
- [ ] Public surfaces and egress are intentional.
- [ ] Images/IaC have traceable provenance.
- [ ] Secrets and state are protected.

## Anti-patterns
- Long-lived cloud admin keys in CI.
- Applying unreviewed IaC directly to production.
- Treating image scanning as proof of runtime security.

## Verification
Run IaC plans, policy-as-code, image checks, cluster config tests, and least-privilege reviews in non-production first.

## Output format
State provider/scope, risks, controls, plan evidence, deployment gates, and shared-responsibility gaps.
