# Opt-in hooks: guard and completion gate

RCoder ships two optional Claude Code hook handlers in `skills/rcoder/scripts/rcoder_hooks.py` (repository wrapper: `scripts/rcoder-hooks.py`). They are **not enabled** by installing the skill or the plugin. The bundled `hooks/hooks.json` still contains only the read-only `SessionStart` hook (D-019); these handlers are a separate, deliberate choice (D-021).

| Handler | Event | What it does |
|---|---|---|
| `guard` | `PreToolUse` | Denies reading, searching, or writing credential files; denies catastrophic commands; asks before force pushes and before piping a download into an interpreter |
| `stop-gate` | `Stop` | Blocks a stop once when a turn edited code, claimed completion, ran no check, and gave no evidence labels |

## Enable

```sh
python3 skills/rcoder/scripts/rcoder_hooks.py print-config             # review the JSON first
python3 skills/rcoder/scripts/rcoder_hooks.py install --dry-run        # show the merged file, write nothing
python3 skills/rcoder/scripts/rcoder_hooks.py install                  # project: .claude/settings.json
python3 skills/rcoder/scripts/rcoder_hooks.py install --scope user     # user: ~/.claude/settings.json
python3 skills/rcoder/scripts/rcoder_hooks.py install --only guard --profile strict
python3 skills/rcoder/scripts/rcoder_hooks.py uninstall
```

The installed `RCoder` command exposes the same actions, so you do not need to remember the script path:

```sh
RCoder hooks print-config
RCoder hooks install --scope user --profile strict --dry-run
RCoder hooks uninstall --scope project
```

`install` writes the absolute interpreter and script path, merges without removing existing hooks, writes a timestamped backup beside an existing settings file, is idempotent, and refuses symbolic links and settings files that are not strict JSON (print the snippet and merge by hand in that case). Hooks run with your privileges: install them only for projects you trust. Set `RCODER_HOOKS_DISABLE=1` in the environment that launches the host to switch both handlers off without editing settings.

## Guard rules

Profile `standard` (default):

- **Deny** `Read`, `Edit`, `Write`, `MultiEdit`, `NotebookEdit`, and `Grep` on credential files: `.env` and `.env.*` (but not `.env.example`, `.env.sample`, `.env.template`), private keys and certificates (`id_*`, `*.pem`, `*.key`, `*.p12`, `*.pfx`, `*.jks`, `*.keystore`, `*.kdbx`), `.npmrc`, `.pypirc`, `.netrc`, `.git-credentials`, `credentials*`, `secrets.*`, service-account JSON, Terraform state and `terraform.tfvars`, `.htpasswd`, `.docker/config.json`, and anything under `.ssh`, `.aws`, `.gnupg`, or `.kube`. Public keys (`*.pub`) are allowed.
- **Deny** writes inside `.git`.
- **Ask** before editing `.claude/settings.json` or `.claude/settings.local.json`, so the guard cannot be switched off silently.
- **Deny** shell commands that expose a credential file through a reader or copier (`cat`, `head`, `grep`, `sed`, `cp`, `scp`, `tar`, `curl -d @file`, and similar), including inside `bash -c` and command substitution; `git add`, `git diff`, `git show`, `git blame`, and `git cat-file` on a credential file; recursive deletes of `/`, `~`, `$HOME`, or a top-level system directory; `mkfs`, `dd of=/dev/...`, writes to raw disks, recursive `chmod`/`chown` of `/`, deleting a drive root on Windows, and fork bombs.
- **Ask** before `git push --force`, `-f`, `--force-with-lease`, `+refspec`, and before `curl`/`wget`/`irm` output is piped into `sh`, `bash`, `python`, `node`, `iex`, and similar.

Profile `strict` adds **ask** for `sudo`/`doas`, `rm -rf`, `git reset --hard`, `git clean -f`, `npm|pnpm|yarn publish`, `terraform|tofu apply|destroy`, `kubectl delete`, and destructive SQL (`DROP`, `TRUNCATE`).

A denial returns `permissionDecision: "deny"` with a reason that tells the model what to do instead. It does not stop the session.

## Completion gate

The gate reads the tail of the session transcript (the last 256 KB) and blocks the stop only when all of these hold for the final turn: a code file (not `.md`, `.txt`, `.rst`, `.adoc`) was edited; the last assistant message claims completion; no test, lint, or build command ran; and the message contains none of `VERIFIED`, `INFERRED`, `NOT VERIFIED`, `UNVERIFIED`. The reason asks for the narrowest check or an evidence-labelled restatement. When Claude Code reports `stop_hook_active`, the gate always allows, so it can never loop.

## Limits and evidence status

- **Fail open.** Malformed events, oversize events (over 1 MB), an unreadable transcript, and internal errors allow the action and print nothing. A guard that wedged a session would be worse than a missed block.
- **Guardrail, not sandbox.** The command analysis is lexical. `python -c "open('.env')"`, constructed or obfuscated names, and variable expansion are not detected. Use host permission rules and OS-level isolation for real containment.
- **Heuristic gate.** The completion gate depends on the transcript layout and on phrasing, so it can miss a claim or flag a harmless one.
- **Deterministic and local.** The handlers use no network, subprocess, or dynamic code; `scripts/test-hooks.py` checks this with an AST scan.
- **Host evidence.** Checked on 2026-11-24 against the Claude Code hooks reference (read directly): the `PreToolUse` output object `hookSpecificOutput` with `hookEventName` and `permissionDecision` plus `permissionDecisionReason` (the reference lists `allow`, `deny`, `ask`, and `defer`; RCoder emits only `deny` and `ask`); exact-name matcher lists written with `|`; hook `timeout` in seconds; exit code 0 with JSON for structured control; top-level `decision: "block"` with `reason` for `Stop` and `SubagentStop`; and `stop_hook_active` as a documented input field (read in the `SubagentStop` example). Rule behavior and payload shapes are VERIFIED locally by `scripts/test-hooks.py`.
- **NOT VERIFIED.** The `Stop` section itself and its `stop_hook_active` text were not read (the page was truncated); the `MultiEdit` tool name did not appear in the part of the reference that was read (an unknown name in a matcher never matches, so it is harmless); the transcript line layout in current releases (the reference recommends `last_assistant_message` on `Stop` instead of reading the transcript, which this gate does not yet use); shell quoting of the interpreter path on Windows hosts (`install` writes `"<python>" "<script>" <handler>`); loading by a live Claude Code session; and any effect on model outcomes.
- **Not covered.** The host also exposes a `PowerShell` tool. The guard inspects only `Bash` commands, and the `PowerShell` input shape was not checked, so PowerShell commands are not guarded. Other hosts are not supported.

## Sources

- Claude Code hooks: https://code.claude.com/docs/en/hooks
- Claude Code hook guide: https://code.claude.com/docs/en/hooks-guide/
