---
description: Verify a completion claim against the diff and test output
argument-hint: [claim to verify, or paths to saved artifacts]
---
Verify this completion claim independently: $ARGUMENTS

1. Capture the observed diff and the output of the narrowest relevant test command into files inside the project. Do not trust earlier summaries.
2. If the `rcoder` MCP server is connected and an expectations file exists, call `rsaver_crosscheck`. Otherwise compare the claim to the diff and test output by hand.
3. Report PASS, FAIL, or UNVERIFIED with line-referenced evidence for each claimed item. Anything not observed is UNVERIFIED, never PASS.
4. Do not modify source files while verifying.

