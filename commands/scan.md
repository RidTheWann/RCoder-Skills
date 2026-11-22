---
description: Run RScan and present ranked development options for this repository
argument-hint: [optional focus area]
---
Run RScan, the read-only project scan, for the current repository and present its ranked development options.

Focus requested by the user (may be empty): $ARGUMENTS

1. If the `rcoder` MCP server is connected, call `rcoder_scan`. Otherwise run `rscan.py scan --root . --format json` from the installed RCoder skill's `scripts/` directory.
2. Present the options in priority order with, for each, the evidence that triggered it, the first command to run, and the specialist modules it names.
3. If a focus area was given, rank matching options first and say why.
4. Do not edit files and do not run any option's first command until the user chooses one. Label anything you did not run as NOT VERIFIED.

