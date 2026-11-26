---
description: Check that RCoder is installed correctly and which optional tools are enabled
# AUTO-GENERATED — DO NOT EDIT DIRECTLY
---
Diagnose the RCoder installation.

1. If the `rcoder` MCP server is connected, call `rcoder_doctor` and report its output. A successful call proves the server runs, not that the host discovers the skill.
2. Otherwise confirm that `skills/rcoder/SKILL.md` exists in an installed skill root and that its `references/` directory and `scripts/` helpers are present.
3. Read `.rcoder-features.json` in the target root, if present, to report whether RScan and RSaver were enabled.
4. State separately what was observed (files, server reachability) and what was not (native skill discovery, automatic RScan launch).

