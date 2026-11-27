# RCoder Runtime — execution contracts

## Activate when

Use this reference when the local `rcoder-runtime` executable is available and a task spans multiple files, has explicit acceptance criteria, or carries elevated implementation risk. It complements the RCoder execution kernel; it does not replace repository instructions, host permissions, RFC, or RSaver.

## Task lifecycle

1. **Create a draft contract** before execution. State one objective, observable acceptance criteria, constraints, and an honest risk level.
2. **Inspect the contract** and start it only when the objective and criteria match the user's request.
3. **Execute within the contract.** Keep unrelated changes out of scope. Record a criterion's evidence only after actually checking it.
4. **Record evidence per criterion.** Use concise summaries and stable source references such as a test command, CI run, or artifact path. Do not copy credentials, raw secrets, or large logs into the contract.
5. **Complete only after all criteria pass.** The Runtime rejects completion if any criterion lacks a latest `pass` attestation. A later `fail` or `not-run` reopens that completion blocker.
6. **Block honestly.** A blocked task requires a reason. Resume it only when the blocker is resolved.

## CLI pattern

```sh
rcoder-runtime task create --project . \
  --objective "Deliver the requested implementation" \
  --acceptance "Focused tests pass" \
  --acceptance "Final diff is scoped" \
  --constraint "Preserve existing host permissions" \
  --risk high --json

rcoder-runtime task transition --project . --id TASK_UUID --to active
rcoder-runtime task evidence --project . --id TASK_UUID \
  --criterion AC-001 --outcome pass \
  --summary "Focused tests passed" --source "cargo test -p runtime-core"
rcoder-runtime task show --project . --id TASK_UUID
rcoder-runtime task transition --project . --id TASK_UUID --to completed
```

Use the task UUID returned by `task create`. Criteria are identified as `AC-001`, `AC-002`, and so on. The `task list` and `task show` commands expose the current persisted state.

## Evidence and enforcement boundaries

- Runtime validates the task schema, ID, state-transition graph, evidence-to-criterion linkage, and latest-outcome completion gate.
- An evidence record is a **caller attestation**. Runtime does not execute the referenced shell command, inspect the referenced artifact, prove a test ran, or establish that a claim is truthful.
- The agent must independently run the referenced check, inspect the actual output and diff, and label material conclusions `VERIFIED`, `INFERRED`, or `NOT VERIFIED`.
- The Task Controller does not intercept editor, shell, filesystem, or Git operations and does not grant permissions. Only a future policy-aware Tool Gateway can enforce operations routed through it.
- Keep durable cross-request facts in RFC and use RSaver for measurement, redaction, reduction, packing, recovery, and cross-checking. Do not duplicate the RFC SQLite store in Runtime.

