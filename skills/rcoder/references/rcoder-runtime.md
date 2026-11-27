# RCoder Runtime — execution contracts

## Activate when

Use this reference when the local `rcoder-runtime` executable is available and a task spans multiple files, has elevated risk, or needs explicit acceptance criteria. It complements RCoder's engineering workflow and does not replace host permissions, repository rules, RFC, or RSaver.

## Mission and expertise

This reference explains how an agent creates and maintains a structured Runtime task contract. It covers objectives, acceptance criteria, constraints, risk classification, status transitions, evidence attestations, and honest handoff. It does not authorize actions.

## Mental model

A task contract is a durable project-local record, not model memory. Every model request still needs its relevant context injected by the host. Runtime guards contract state and completion prerequisites, while the agent performs work through authorized host tools.

## Prerequisites and reconnaissance

Confirm `rcoder-runtime` is installed and available on PATH. Inspect the repository instructions and Git state first. Choose the real project root, preserve unrelated changes, and never store credentials, tokens, private keys, or raw secrets in task fields.

## Procedure

1. Create a draft with one objective, observable acceptance criteria, constraints, and a risk level.
2. Read the returned UUID and inspect the persisted contract.
3. Move the task to active only when its scope matches the user's request.
4. Execute through the host's authorized tools and record concise evidence after checking each criterion.
5. Re-run checks after relevant changes; the latest attestation for a criterion controls its completion status.
6. Move the task to completed only after all criteria have a latest passing attestation. Otherwise keep it active or blocked with a reason.

## Decision tree

- If the Runtime executable is unavailable, continue using the normal RCoder workflow and report that the contract ledger is unavailable.
- If the request is multi-file or high-risk, create a contract before implementation.
- If the objective or criteria are ambiguous, refine the draft before activating it.
- If a blocker prevents progress, transition to blocked with a concrete reason.
- If any latest criterion outcome is fail or not-run, do not complete the task.
- If the Runtime rejects a transition, inspect the state and resolve the underlying condition rather than editing its JSON directly.

## Tool strategy

Use `rcoder-runtime task create`, `list`, `show`, `evidence`, and `transition`. Prefer `--json` for machine-readable output. Store short command or artifact references in evidence sources, not full logs. Use normal host tools for repository edits and verification.

## Advanced techniques

Split unrelated deliverables into separate contracts. Keep acceptance criteria small, observable, and independently checkable. A newer fail or not-run attestation intentionally supersedes an older pass. A completed task must first be reopened to active with a reason before new evidence can be recorded; repeat evidence capture after fixes and rerun the relevant check.

## Failure modes

A missing Runtime binary means no local task ledger is available. Invalid IDs, unknown criteria, oversized fields, symlinked state directories, and invalid transitions are rejected. A failed persistence operation must be treated as a task-recording failure, not as successful completion.

## Quality checklist

- Objective describes the requested outcome rather than a vague activity.
- Acceptance criteria can be checked independently.
- Constraints preserve repository and host boundaries.
- Risk classification reflects impact and reversibility.
- Evidence sources point to real checks or artifacts already inspected.
- The latest outcome for every criterion is pass before completion.

## Anti-patterns

Do not record pass before running the check. Do not treat a source string as proof that a command executed. Do not copy secrets or large logs into the contract. Do not mark the task completed to bypass a blocked criterion, and do not claim Runtime intercepted host tools.

## Verification

Inspect the actual test output, build result, repository diff, and relevant artifacts independently. Runtime checks the task schema and state machine but cannot validate the truth of a caller's evidence. Label external claims VERIFIED, INFERRED, or NOT VERIFIED according to observed evidence.

## Output format

Report the task UUID, final state, acceptance criteria outcomes, evidence source references, checks actually performed, remaining blockers, and limitations. Distinguish Runtime's stored attestations from independently verified results.

## Executable Verification & Failure Diagnostics

- **Verify**: Run `rcoder-runtime task show --project PATH --id TASK_UUID` and compare the stored criteria and evidence with actual test output and the final diff.
- **Anti-Patterns**: Never invent evidence, execute a command merely to populate a record without inspecting its result, or confuse a passing attestation with independent proof.
- **Failure Diagnostics**:
  - Transition rejected -> a prior state or completion prerequisite is unsatisfied -> inspect the task and record missing criterion evidence.
  - Reopen rejected -> no reason was supplied or the state is not completed -> provide a reason and confirm the current task state.
  - Task ID rejected -> the identifier is malformed or unavailable -> copy the UUID from `task create` or `task list`.
  - Task storage rejected -> a state path is unsafe or unwritable -> inspect `.rcoder/runtime/tasks` permissions and symlinks without bypassing the guard.
