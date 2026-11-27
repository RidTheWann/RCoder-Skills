# Lifecycle hooks across Claude Code and Gemini CLI

RCoder uses one standard-library handler at `skills/rcoder/scripts/rcoder_hooks.py` (the repository entry point `scripts/rcoder-hooks.py` forwards to it). Host event names and output schemas differ, so the same policy is rendered through host-specific hook entries.

| Handler | Event | What it does |
|---|---|---|
| `guard` | Claude `PreToolUse`; Gemini `BeforeTool` | Denies credential access, credential staging, and catastrophic commands; asks for review before force pushes and remote-script execution |
| `post-tool` | Claude `PostToolUse`; Gemini `AfterTool` | Adds context when tool output contains a token-shaped secret |
| `pre-compact` | Claude `PreCompact` | Adds a short handoff reminder to the compaction summary |
| `stop-gate` | Claude `Stop` | Blocks once when a turn edited code, claimed completion, ran no check, and gave no evidence labels |
| RFC injection | Claude `UserPromptSubmit` | Builds a fresh session/prompt payload and injects it through `additionalContext` when the RFC store exists |
| RFC response capture | Claude `Stop` | Verifies the matching response canary and stores a token-free RFC transcript record |

The Claude plugin runs `SessionStart`, `PreToolUse`, `PostToolUse`, `PreCompact`, `UserPromptSubmit`, and RFC response capture on `Stop` from `hooks/hooks.json`. The separate completion `Stop` gate remains available through the explicit CLI installer. Gemini CLI uses `.gemini/settings.json`; install its documented before/after tool events separately. Gemini has no documented `PreCompact` or `Stop` equivalent, so those handlers are unavailable there.

## Enable

```sh
python3 skills/rcoder/scripts/rcoder_hooks.py print-config             # review the JSON first
python3 skills/rcoder/scripts/rcoder_hooks.py install --dry-run        # show the merged file, write nothing
python3 skills/rcoder/scripts/rcoder_hooks.py install                  # project: .claude/settings.json
python3 skills/rcoder/scripts/rcoder_hooks.py install --scope user     # user: ~/.claude/settings.json
python3 skills/rcoder/scripts/rcoder_hooks.py install --only guard --profile strict
python3 skills/rcoder/scripts/rcoder_hooks.py uninstall
python3 skills/rcoder/scripts/rcoder_hooks.py print-config --host gemini-cli
python3 skills/rcoder/scripts/rcoder_hooks.py install --host gemini-cli --scope project
```

The installed `rcoder` command exposes the same Claude Code settings actions. For Gemini CLI, invoke the skill handler directly with `--host gemini-cli`.

```sh
rcoder hooks print-config
rcoder hooks install --scope user --profile strict --dry-run
rcoder hooks uninstall --scope project
```

`install` writes the absolute interpreter and script path, merges without removing existing hooks, writes a timestamped backup beside an existing settings file, is idempotent, and refuses symbolic links and settings files that are not strict JSON (print the snippet and merge by hand in that case). Hooks run with your privileges: install them only for projects you trust. Set `RCODER_HOOKS_DISABLE=1` in the environment that launches the host to switch both handlers off without editing settings.

## RFC host injection

The bundled Claude Code plugin calls `context_fabric_host.py user-prompt-submit` on every submitted prompt and `context_fabric_host.py stop` when a turn stops. The adapter is inert until `.rcoder/context-fabric.sqlite3` exists; initialize it with `python scripts/context-fabric.py --root . stats`. Each prompt gets a unique canary file under `.rcoder/private/rfc-canaries`; the Stop hook checks the host's `last_assistant_message`, stores the token-free RFC transcript, and removes the file. A missing canary marks the delivery unacknowledged but never blocks the turn. Set `RCODER_RFC_DISABLE=1` to disable only RFC host injection.

This host path is Claude Code-specific. Local tests validate hook payloads and lifecycle pairing; native loading and invocation inside a live Claude Code process remain NOT VERIFIED.

## Guard rules

Profile `standard` (default):

- **Deny** `Read`, `Edit`, `Write`, `MultiEdit`, `NotebookEdit`, and `Grep` on credential files: `.env` and `.env.*` (but not `.env.example`, `.env.sample`, `.env.template`), private keys and certificates (`id_*`, `*.pem`, `*.key`, `*.p12`, `*.pfx`, `*.jks`, `*.keystore`, `*.kdbx`), `.npmrc`, `.pypirc`, `.netrc`, `.git-credentials`, `credentials*`, `secrets.*`, service-account JSON, Terraform state and `terraform.tfvars`, `.htpasswd`, `.docker/config.json`, and anything under `.ssh`, `.aws`, `.gnupg`, or `.kube`. Public keys (`*.pub`) are allowed.
- **Deny** writes inside `.git`.
- **Ask** before editing `.claude/settings.json` or `.claude/settings.local.json`, so the guard cannot be switched off silently.
- **Deny** shell commands that expose a credential file through a reader or copier (`cat`, `head`, `grep`, `sed`, `cp`, `scp`, `tar`, `curl -d @file`, and similar), including inside `bash -c` and command substitution; `git add`, `git diff`, `git show`, `git blame`, and `git cat-file` on a credential file; recursive deletes of `/`, `~`, `$HOME`, or a top-level system directory; `mkfs`, `dd of=/dev/...`, writes to raw disks, recursive `chmod`/`chown` of `/`, deleting a drive root on Windows, and fork bombs.
- **Ask** before `git push --force`, `-f`, `--force-with-lease`, `+refspec`, and before `curl`/`wget`/`irm` output is piped into `sh`, `bash`, `python`, `node`, `iex`, and similar.

Profile `strict` adds **ask** for `sudo`/`doas`, `rm -rf`, `git reset --hard`, `git clean -f`, `npm|pnpm|yarn publish`, `terraform|tofu apply|destroy`, `kubectl delete`, and destructive SQL (`DROP`, `TRUNCATE`).

A Claude denial returns `permissionDecision: "deny"`; Gemini receives its documented top-level `decision: "deny"` and `reason`. Gemini's published hook schema does not define an interactive permission prompt, so an action classified as `ask` is denied with a request for user review before retrying.

## Completion gate

The gate reads the tail of the session transcript (the last 256 KB) and blocks the stop only when all of these hold for the final turn: a code file (not `.md`, `.txt`, `.rst`, `.adoc`) was edited; the last assistant message claims completion; no test, lint, or build command ran; and the message contains none of `VERIFIED`, `INFERRED`, `NOT VERIFIED`, `UNVERIFIED`. The reason asks for the narrowest check or an evidence-labelled restatement. When Claude Code reports `stop_hook_active`, the gate always allows, so it can never loop.

## Strict objective stop gate

The default gate is heuristic and stays opt-in. Set `RCODER_STRICT_STOP=1` in the environment that launches the host, or add `.rcoder/policy.json` with `{"strict_stop": true, "target_files": ["path/to/required.py"]}` to enable a stricter objective check at `Stop` (and at `SubagentStop` if the host registers it). The strict gate cross-checks `git status --porcelain` against named objective targets and claimed edits. It blocks when a named target is untouched, a claimed edit is absent from git status, or the last recorded verification command exited nonzero. `RCODER_STRICT_STOP=0` overrides the policy file. The gate fails open when git is unavailable, so it is an evidence guard rather than a sandbox. Edit the missing target, correct the objective with operator confirmation, or rerun the real check before stopping again.

## Limits and evidence status

- **Fail open.** Malformed events, oversize events (over 1 MB), an unreadable transcript, and internal errors allow the action and print nothing. A guard that wedged a session would be worse than a missed block.
- **Guardrail, not sandbox.** The command analysis is lexical. `python -c "open('.env')"`, constructed or obfuscated names, and variable expansion are not detected. Use host permission rules and OS-level isolation for real containment.
- **Heuristic gate.** The completion gate depends on the transcript layout and on phrasing, so it can miss a claim or flag a harmless one.
- **Deterministic and local.** The handlers use no network, subprocess, or dynamic code; `scripts/test-hooks.py` checks this with an AST scan.
- **Host contract evidence.** Claude's current hook reference documents `PreToolUse` decisions, `PostToolUse` context, and plain-stdout `PreCompact` instructions. Gemini CLI's current hook reference documents `BeforeTool`/`AfterTool`, top-level deny output, `additionalContext`, and millisecond timeouts. The local regression test checks both output shapes. These are documentation and local payload checks, not proof that either host loaded the plugin or settings.
- **NOT VERIFIED.** Native discovery and invocation in live Claude Code or Gemini CLI; shell quoting and interpreter fallback on every supported Windows host; token redaction in all host-specific response formats; Gemini's current undocumented `ask` support; and any effect on model outcomes.
- **Not covered.** The handler does not guard Claude's `PowerShell` tool or arbitrary tools that use unknown argument shapes. Gemini `Stop` and compaction events have no documented equivalent in the checked hook reference.

## Sources

- Claude Code hooks: https://code.claude.com/docs/en/hooks
- Claude Code hook guide: https://code.claude.com/docs/en/hooks-guide/
- Gemini CLI hook reference: https://github.com/google-gemini/gemini-cli/blob/main/docs/hooks/reference.md
