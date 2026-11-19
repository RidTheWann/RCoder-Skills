# RScan host hook evidence

RScan can be invoked manually or wired to a host's session-start mechanism. A skill file alone cannot auto-run on IDE launch; automatic behavior requires a host feature that is actually present and enabled. This table records evidence, not intent.

| Host | Mechanism | Evidence | RScan support |
|---|---|---|---|
| Claude Code | `SessionStart` command hook in `.claude/settings.json` (project) or `~/.claude/settings.json` (user); matcher `startup`; stdout plain text or `hookSpecificOutput.additionalContext` is added to context | Official hooks reference documents the event, command hooks, matchers, and context injection | `rscan hooks install --host claude-code --scope project|user`; payload uses `additionalContext` and `sessionTitle` |
| Gemini CLI | `SessionStart` command hook in `.gemini/settings.json` (project) or `~/.gemini/settings.json` (user); matcher `startup`; strict JSON on stdout with `hookSpecificOutput.additionalContext` | Official hooks documentation documents the event, schema, exit codes, and JSON-only stdout | `rscan hooks install --host gemini-cli --scope project|user`; payload is JSON only |
| OpenCode | Plugins subscribe to `session.created`; V1 offers `experimental.chat.system.transform`, V2 uses `ctx.session.hook("context", ...)` | Official plugin docs and event list show plugin-based events rather than JSON settings hooks | No installer generated. Manual adapter possible but version-specific and **NOT VERIFIED** in this repository |
| Other catalog hosts | Hook support varies by product version and UI surface | No verified evidence collected here | No auto-install; invoke `rscan scan` manually from the agent prompt |

## Installer behavior

`rscan hooks install` is explicit and state-changing:

- Merges a single `SessionStart` entry without removing existing hooks.
- Writes a timestamped backup beside the settings file before replacing it.
- Uses `sys.executable` and the absolute path to the bundled `skills/rcoder/scripts/rscan.py`, so no `python3` alias is assumed.
- Is idempotent: a second install detects the existing RScan command and makes no change.
- Supports `--dry-run` and `hooks preview` for review before writing.

Project scope writes into the current project; user scope writes into the home directory. Only the two hosts in the table above are installable. Host settings may be gated by trust prompts or disabled by policy; enable hooks in the host and confirm the first session shows the RScan menu.

## Safety and limits

- RScan is read-only; the installer only edits the host settings file it was told to edit.
- Hooks execute with user privileges. Install them only for projects you trust.
- The scan samples a bounded number of paths and never reads binary contents.
- A hook that produces no menu is not proof that the host discovered RCoder; check host logs and settings.
- Cache/re-anchoring behavior for the scan result remains subject to `docs/TOKEN-ECONOMICS.md` and `docs/CONTEXT-DRIFT.md`.

## Sources

- Claude Code hooks: https://code.claude.com/docs/en/hooks
- Claude Code hook guide: https://code.claude.com/docs/en/hooks-guide/
- Gemini CLI hooks: https://geminicli.com/docs/hooks/ and https://geminicli.com/docs/hooks/reference/
- OpenCode plugin events: https://github.com/anomalyco/opencode/blob/dev/packages/web/src/content/docs/plugins.mdx
