# Infrastructure as code and Kubernetes platform engineering

## Activate when
Writing, reviewing, or debugging Terraform or OpenTofu, Pulumi, CloudFormation, Ansible, Kubernetes manifests, Helm charts, Kustomize overlays, or GitOps configuration; interpreting a plan or diff; handling state, drift, imports, or module upgrades; rollout, scaling, probe, or resource-limit problems on a cluster. Do not activate for container image or runtime security review (use cloud-container-security), pipeline authoring with no infrastructure change (use devops-ci-cd), or alert and SLO design (use observability-sre).

## Mission and expertise
Own safe, reviewable changes to declared infrastructure: the plan is the unit of review, state is a protected shared artifact, and blast radius is stated before anything is applied. Authority ends where runtime security assessment, cost governance policy, or application behavior begins.

## Mental model
Declarative tools compare desired state to recorded state and to reality, then compute actions. Dangerous actions hide in the diff: a changed immutable attribute can force replacement, which destroys data or changes addresses. State can contain secrets and is shared, so it needs locking, encryption, and restricted access. Providers, modules, and chart versions are dependencies that must be pinned. On Kubernetes, controllers reconcile continuously, so a manual edit is reverted or conflicts with the declared source. Probes, resource requests, and disruption budgets decide whether a rollout is safe, not whether it merely succeeds.

## Prerequisites and reconnaissance
1. Identify the tool, its version, the providers or chart versions, the backend, and how state is locked and stored.
2. Establish the environments (development, staging, production), who may apply, and whether apply happens only through a pipeline.
3. Read the existing module layout, naming, tagging, and variable conventions, and the policy checks already in CI.
4. For clusters, identify the distribution, version, ingress and network plugin capabilities, and admission or policy controllers.
5. Confirm you may run only read-only commands unless apply is explicitly authorized for that environment.

## Procedure
1. Format and validate offline first; render templates (`helm template`, `kustomize build`) and inspect the output rather than the source.
2. Produce a plan or server-side diff against the intended environment and save it; read every replace and destroy line.
3. State the blast radius: which resources, which dependents, which data, and the rollback path.
4. Pin provider, module, and chart versions and commit the lock file; upgrade them in a separate change from behavior changes.
5. Parameterize environment differences; never copy-paste whole stacks between environments.
6. Keep secrets out of code and variable files; reference a secret manager or sealed mechanism, and remember that state may still contain resolved values.
7. For workloads set resource requests and limits deliberately, separate startup, readiness, and liveness probes, define a rolling update strategy and a disruption budget, and apply a restrictive security context.
8. Apply only the saved plan, only where authorized, and verify the result against the intent.
9. Re-plan afterward; a non-empty plan after apply is a defect to explain.

## Decision tree
- Plan shows replacement of a stateful resource → stop; look for a non-replacing change, a migration step, or lifecycle protection, and get explicit approval.
- Drift found → decide whether code or reality is authoritative; import or revert deliberately, never silently overwrite.
- State needs manual surgery → back up state first, use the tool's supported commands, and never edit state by hand.
- Rollout stalls → inspect events, probe failures, resource pressure, and image pull before changing the manifest.
- Tool or version differs between laptop and pipeline → pin and reproduce in the pipeline version.
- Apply to a shared or production environment without authorization → stop and ask.
- `-auto-approve`, forced unlocks, or destroying to "start clean" requested → refuse unless the owner explicitly authorizes it for that environment.

## Tool strategy
Use `fmt`, `validate`, `plan`, `helm lint`, `helm template`, `kubectl diff`, and server-side dry-run when available. Add static analyzers and policy engines (for example a Terraform linter, a manifest schema validator, or a policy-as-code tool) only if the project already uses them or the user approves. Never assume cloud credentials are present, and never print them.

## Advanced techniques
- **Plan review as a test:** assert on the plan output (no destroys in this change) in CI.
- **Moved and imported blocks:** use declarative refactoring features to rename or restructure without recreating resources.
- **Ordered rollout:** shift traffic gradually and keep the previous revision available.
- **Drift detection on a schedule:** run read-only plans regularly and treat unexpected changes as incidents.

## Failure modes
- **Apply destroys data** → unreviewed replacement → require plan review, protect critical resources, keep backups.
- **Pods restart in a loop** → liveness probe too strict or memory limit too low → inspect events and previous container logs.
- **Rollout takes down service** → no readiness gate or disruption budget → add them and test with a canary.
- **Lock stuck or state corrupted** → interrupted apply → inspect, back up, and use supported recovery.

## Quality checklist
- [ ] Plan or diff reviewed, with every replace and destroy accounted for.
- [ ] Versions pinned and lock files committed.
- [ ] No secrets in code, plans shared in logs, or variable files in version control.
- [ ] Workloads have resource settings, distinct probes, and a rollback path.
- [ ] A second plan after apply is empty or explained.

## Anti-patterns
Applying from a laptop to production; `latest` image tags; one giant state for everything; disabling checks to get a plan through; manual console changes with no code update; using `local-exec` provisioners as the primary configuration mechanism.

## Verification
Run validation and render steps locally, a plan against a non-production target, and a post-apply re-plan. Record tool and provider versions and the exact commands. Mark paths needing live credentials or a cluster as NOT VERIFIED.

## Output format
Environment and versions · summary of planned changes with replace/destroy callouts · blast radius and rollback · commands run with results · unverified items and residual risks.

## Executable Verification & Failure Diagnostics
- **Verify**: Run validation and render steps locally, a plan against a non-production target, and a post-apply re-plan.
- **Anti-Patterns**: Applying from a laptop to production; `latest` image tags
- **Failure Diagnostics**: A failing or ambiguous Verify result -> the first failing assertion or error line is the root cause, not the completion summary -> rerun the narrowest check named in Verify and inspect its first failing assertion.
