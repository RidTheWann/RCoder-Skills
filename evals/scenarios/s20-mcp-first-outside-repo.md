# Fixture: RCoder used from an external project or Git worktree

RCoder is installed at user scope. The agent's working directory is an isolated Git worktree of an unrelated project (for example `.worktrees/feature-x`). The directory `skills/rcoder/` does not exist there. The `rcoder` MCP server is connected and `mcp__rcoder__rcoder_scan` and `mcp__rcoder__rcoder_doctor` are in the tool list. The user asks for an RScan and an RSaver budget plan.

Expected behavior: call the MCP tools first and pass an absolute project path as `root`. If MCP tools were absent, locate the installed skill directory and run helpers by absolute path with an explicit `--root`. Never run `python3 skills/rcoder/scripts/rscan.py` relative to the working directory, and never conclude that RCoder is not installed because `skills/rcoder/` is missing. If neither route works, report the tools and paths checked and mark RScan/RSaver NOT VERIFIED.

Fails the rubric: executing a cwd-relative script path, treating the resulting `No such file or directory` error as proof that the skill is unavailable, or ignoring connected MCP tools.
