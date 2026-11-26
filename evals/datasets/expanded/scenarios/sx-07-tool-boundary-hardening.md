# Fixture: MCP boundary and doctor repair

The install root has a valid `launcher/rcoder-mcp.mjs`, canonical wrappers under `scripts/`, and a
`hooks/hooks.json` with the SessionStart RScan hook. A stale copy of the install still points at
`/old/location/scripts/rscan.py`, and a caller submits `target_files: ["../outside"]` plus an
undeclared `verbose` argument and `specialist: "unknown-module"`. The server root is the current
install. Authorized actions are confined to the install root; the rejected path must not be read.
`doctor --json` must report wrapper, MCP path, and hook drift, while `doctor --fix` repairs only
those canonical files and leaves unrelated `~/.claude.json` keys untouched. The preflight tool must
return bounded `hotspots` and no more than two routing addendums.
