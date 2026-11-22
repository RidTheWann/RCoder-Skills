---
description: Select and validate RCoder specialist modules for a task before starting work
argument-hint: [task description]
---
Choose RCoder specialists for this task and record the selection before doing any work.

Task: $ARGUMENTS

1. Restate the deliverable and its acceptance criteria. Select by deliverable, not by keywords.
2. List valid module names with `rcoder_list_specialists` (MCP; its `query` argument ranks candidate names) or the files in the installed skill's `references/` directory. Never invent a name.
3. Pick exactly one primary specialist. Add supporting modules only when each has a distinct responsibility, and keep `security` alongside any narrow security module.
4. If the MCP server is connected, call `rcoder_validate_selection` and fix every error it reports.
5. Output the selection record: classification, selected modules, primary, supporting with reasons, verifier, confidence, rejected alternatives, required verification. Then load only the needed sections of each module (`rcoder_get_specialist` accepts a `sections` list).

