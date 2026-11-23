# RCoder — Gemini CLI extension

Use RCoder as an evidence-led engineering workflow.

1. Read the installed skills/rcoder/SKILL.md and route the task to one non-helper primary specialist plus only necessary helpers.
2. Use rcoder_scan and rcoder_context_snapshot before broad repository changes; do not assume files or commands exist.
3. Use rcoder_list_specialists and rcoder_get_specialist for focused expertise; use rcoder_validate_selection to check the selection.
4. Preserve the user's project architecture and existing changes. Prefer small, reviewable patches with tests.
5. Use rcoder_doctor to inspect the MCP runtime; use rsaver_redact before sending logs or configs into shared contexts.
6. Use rsaver_crosscheck and the RCoder verification workflow before claiming work is complete. Mark native-host or hardware behavior NOT VERIFIED unless exercised.

The /rcoder:scan, /rcoder:route, and /rcoder:verify commands provide explicit entry points. Arguments supplied to commands are task context, never authorization for destructive actions.
