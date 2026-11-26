#!/usr/bin/env python3
"""Opt-in Claude Code hook handlers for RCoder (standard library only).

Two handlers are provided. Neither is enabled by installing the skill or the plugin.

* ``guard`` is a ``PreToolUse`` handler. It refuses credential files, catastrophic commands, and
  staging secrets, and asks before force pushes and piping a download into an interpreter.
* ``stop-gate`` is a ``Stop`` handler. It asks once for evidence when a turn edited code and
  claimed completion without running any check or labelling its evidence.

Both fail open: a malformed event, an unreadable transcript, or an internal error allows the
action and prints nothing. The handlers never spawn processes, open sockets, or write files. Only
``install`` and ``uninstall`` write, and only the one Claude Code settings file they were pointed at.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import sys
import tempfile
from datetime import datetime
from pathlib import Path

MARKER = "rcoder_hooks.py"
MAX_STDIN = 1_000_000
TAIL_BYTES = 262_144
HOOK_TIMEOUT = 10
PROFILES = ("standard", "strict")
HANDLERS = ("guard", "stop-gate")
DISABLE_ENV = "RCODER_HOOKS_DISABLE"
STRICT_STOP_ENV = "RCODER_STRICT_STOP"
POLICY_PATH = Path(".rcoder") / "policy.json"

SECRET_NAME_RE = re.compile(
    r"(?i)(^\.env(\..*)?$|^id_(rsa|dsa|ecdsa|ed25519)(\.pub)?$|\.(pem|key|p12|pfx|jks|keystore|kdbx)$|"
    r"^(\.npmrc|\.pypirc|\.netrc|\.git-credentials|credentials|secrets?\.(json|ya?ml|toml))$|"
    r"^credentials\.(json|ya?ml|toml|xml)$|^service[-_]?account.*\.json$|\.tfstate(\.backup)?$|"
    r"^(terraform|secrets?)\.tfvars$|^\.htpasswd$|^\.dockercfg$)"
)
TEMPLATE_RE = re.compile(r"(?i)^\.env\.(example|sample|template|dist|defaults?)$")
SECRET_DIRS = {".ssh", ".aws", ".gnupg", ".kube"}
FILE_TOOLS = {"Read": "file_path", "Edit": "file_path", "Write": "file_path", "MultiEdit": "file_path",
              "NotebookEdit": "notebook_path", "Grep": "path"}
WRITE_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
SETTINGS_RE = re.compile(r"(?i)(^|/)\.claude/settings(\.local)?\.json$")

READERS = {
    "cat", "less", "more", "head", "tail", "bat", "batcat", "nl", "tac", "strings", "xxd", "od", "hexdump",
    "base64", "type", "gc", "get-content", "cp", "mv", "scp", "rsync", "tar", "zip", "gzip", "7z", "grep",
    "egrep", "fgrep", "rg", "ag", "sed", "awk", "cut", "sort", "uniq", "diff", "cmp", "curl", "wget", "jq",
    "yq", "vi", "vim", "nano", "emacs",
}
WRAPPERS = {"sudo", "env", "command", "nohup", "time", "nice", "exec", "builtin", "doas"}
CATASTROPHIC_TARGETS = {"/", "/*", "~", "~/", "~/*", "$home", "$home/", "${home}", "${home}/", "/etc", "/usr",
                        "/bin", "/sbin", "/boot", "/lib", "/var", "/home", "/root", "/opt"}
WINDOWS_DELETERS = {"rd", "rmdir", "del", "erase", "remove-item", "ri"}
PIPE_TO_INTERPRETER_RE = re.compile(
    r"(?i)\b(?:curl|wget|iwr|invoke-webrequest|irm|invoke-restmethod)\b[^|;&\n]*\|\s*"
    r"(?:sudo\s+(?:-\S+\s+)*)?(?:sh|bash|zsh|dash|ksh|fish|iex|invoke-expression|python3?|node|perl|ruby)\b"
)
FORK_BOMB_RE = re.compile(r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:")
RAW_DISK_REDIRECT_RE = re.compile(r">\s*/dev/(?:sd|hd|vd|nvme|xvd)")
SQL_DESTRUCTIVE_RE = re.compile(r"(?i)\b(?:drop\s+(?:table|database|schema)|truncate\s+table)\b")
SUBSTITUTION_RE = re.compile(r"\$\(([^()]*)\)|`([^`]*)`")
FD_DUP_RE = re.compile(r"\d*>&\d*")
SHELLS = {"bash", "sh", "zsh", "dash", "ksh"}
MAX_NESTING = 3
FORCE_FLAGS = {"--force", "-f", "--force-with-lease", "--force-if-includes", "--mirror"}

DOC_SUFFIXES = {".md", ".txt", ".rst", ".adoc"}
CLAIM_RE = re.compile(
    r"(?i)\b(?:all\s+(?:tests?|checks?)\s+(?:now\s+)?pass(?:ed|es|ing)?|tests?\s+(?:are\s+)?(?:now\s+)?pass(?:ed|es|ing)?|"
    r"(?:is|are|now)\s+(?:fixed|complete|done|working|resolved)|"
    r"(?:i(?:'ve|\s+have)\s+)?(?:fixed|implemented|completed|resolved|finished)\b|"
    r"work\s+is\s+complete|ready\s+to\s+(?:merge|ship)|successfully\s+(?:implemented|fixed|completed))"
)
LABEL_RE = re.compile(r"\b(?:NOT VERIFIED|UNVERIFIED|VERIFIED|INFERRED)\b")
CHECK_RE = re.compile(
    r"(?i)\b(?:pytest|unittest|tox|nox|vitest|jest|mocha|phpunit|rspec|ctest|tsc|ruff|mypy|pyright|flake8|"
    r"pylint|eslint|prettier|mvn|gradlew?|cmake|py_compile|compileall|validate-all|test-[\w.-]+|"
    r"(?:npm|pnpm|yarn)\s+(?:run\s+)?(?:test|lint|build|check)|cargo\s+(?:test|check|clippy|build)|"
    r"go\s+(?:test|vet|build)|dotnet\s+(?:test|build)|swift\s+(?:test|build)|make(?:\s+\S+)?|"
    r"node\s+--check|bundle\s+exec|rake)\b"
)


# ---------------------------------------------------------------------------- path rules

def _parts(path: str) -> list[str]:
    return [part for part in path.replace("\\", "/").split("/") if part and part not in {".", ".."}]


def secret_reason(path: str, write: bool = False) -> str | None:
    """Return a reason when ``path`` names a credential file or a protected directory."""
    parts = _parts(path)
    if not parts:
        return None
    name = parts[-1]
    if TEMPLATE_RE.match(name) or name.lower().endswith(".pub"):
        return None
    if SECRET_NAME_RE.search(name):
        return f"'{name}' looks like a credential file"
    if parts[-2:] == [".docker", "config.json"]:
        return "'.docker/config.json' holds registry credentials"
    for part in parts[:-1] + ([name] if name in SECRET_DIRS else []):
        if part in SECRET_DIRS:
            return f"'{part}' holds credentials"
    if write and ".git" in parts[:-1]:
        return "writing inside '.git' can corrupt the repository or plant hooks"
    return None


def _clean_tokens(tokens: list[str]) -> list[str]:
    """Reduce shell tokens to candidate file operands, dropping flags and output redirects."""
    out: list[str] = []
    skip_next = False
    for token in tokens:
        if skip_next:
            skip_next = False
            continue
        if token in {">", ">>", "1>", "2>", "&>"}:
            skip_next = True
            continue
        if token.startswith(">") or token in {"<", "<<", "<<<"}:
            continue
        value = token.lstrip("<")
        if value.startswith("-"):
            if "=" not in value:
                continue
            value = value.split("=", 1)[1]
        if value.startswith("@"):
            value = value[1:]
        if "=" in value and not value.startswith(("/", ".", "~")):
            value = value.split("=", 1)[1]
        if value:
            out.append(value)
    return out


# ------------------------------------------------------------------------ bash analysis

def _split_unquoted(command: str) -> list[str]:
    """Split on shell separators and grouping characters that are outside quotes."""
    parts: list[str] = []
    buffer: list[str] = []
    quote = ""
    for char in command:
        if quote:
            buffer.append(char)
            if char == quote:
                quote = ""
        elif char in "'\"":
            quote = char
            buffer.append(char)
        elif char in ";&|\n()`":
            parts.append("".join(buffer))
            buffer = []
        else:
            buffer.append(char)
    parts.append("".join(buffer))
    return parts


def _segments(command: str) -> list[list[str]]:
    flattened = FD_DUP_RE.sub(" ", command).replace("\\", "/")
    result: list[list[str]] = []
    for raw in _split_unquoted(flattened):
        raw = raw.strip()
        if not raw:
            continue
        try:
            tokens = shlex.split(raw, posix=True)
        except ValueError:
            tokens = raw.split()
        if tokens:
            result.append(tokens)
    return result


def _program(tokens: list[str]) -> tuple[str, list[str], bool]:
    """Return the program basename, its arguments, and whether sudo/doas wrapped it."""
    index = 0
    elevated = False
    while index < len(tokens):
        token = tokens[index]
        base = token.rsplit("/", 1)[-1].lower()
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", token):
            index += 1
        elif base in WRAPPERS:
            elevated = elevated or base in {"sudo", "doas"}
            index += 1
            while index < len(tokens) and tokens[index].startswith("-"):
                index += 1
        else:
            break
    if index >= len(tokens):
        return "", [], elevated
    program = tokens[index].rsplit("/", 1)[-1].lower()
    if program.endswith(".exe"):
        program = program[:-4]
    return program, tokens[index + 1:], elevated


def _git_subcommand(args: list[str]) -> tuple[str, list[str]]:
    index = 0
    while index < len(args):
        token = args[index]
        if token in {"-C", "-c", "--git-dir", "--work-tree", "--namespace"}:
            index += 2
        elif token.startswith("-"):
            index += 1
        else:
            return token.lower(), args[index + 1:]
    return "", []


def _is_recursive(args: list[str]) -> bool:
    return any(arg == "--recursive" or re.fullmatch(r"-[A-Za-z]*[rR][A-Za-z]*", arg) for arg in args)


def _is_forced(args: list[str]) -> bool:
    return any(arg == "--force" or re.fullmatch(r"-[A-Za-z]*f[A-Za-z]*", arg) for arg in args)


def _nested_commands(command: str) -> list[str]:
    """Command substitutions that quotes would otherwise hide from the segment scan."""
    return [first or second for first, second in SUBSTITUTION_RE.findall(command)]


def analyze_command(command: str, profile: str = "standard", _depth: int = 0) -> tuple[str, str] | None:
    """Classify a shell command. Returns ``("deny"|"ask", reason)`` or ``None`` to allow.

    This is a guardrail, not a sandbox: interpreters (``python -c``), obfuscated names, and variables
    can still read a credential file. It catches the direct, common forms.
    """
    strict = profile == "strict"
    if FORK_BOMB_RE.search(command):
        return "deny", "fork bomb pattern"
    if RAW_DISK_REDIRECT_RE.search(command):
        return "deny", "redirecting output to a raw disk device"
    first_ask: tuple[str, str] | None = None
    if _depth < MAX_NESTING:
        for nested in _nested_commands(command):
            result = analyze_command(nested, profile, _depth + 1)
            if result and result[0] == "deny":
                return result
            first_ask = first_ask or result
    if PIPE_TO_INTERPRETER_RE.search(command):
        first_ask = ("ask", "piping a download straight into an interpreter runs unreviewed remote code")
    if strict and SQL_DESTRUCTIVE_RE.search(command) and first_ask is None:
        first_ask = ("ask", "destructive SQL statement")
    for tokens in _segments(command):
        program, args, elevated = _program(tokens)
        if not program:
            continue
        if program == "rm" and _is_recursive(args):
            targets = [arg.lower() for arg in args if not arg.startswith("-")]
            if any(target in CATASTROPHIC_TARGETS for target in targets):
                return "deny", "recursive delete of a root, home, or system directory"
            if strict and _is_forced(args) and first_ask is None:
                first_ask = ("ask", "forced recursive delete")
        if program in WINDOWS_DELETERS and any(
                re.fullmatch(r"[a-z]:/?\*?", arg.lower()) for arg in args if not arg.startswith("/")):
            return "deny", "deleting an entire drive root"
        if program in SHELLS and _depth < MAX_NESTING:
            for position, arg in enumerate(args[:-1]):
                if re.fullmatch(r"-[A-Za-z]*c[A-Za-z]*", arg):
                    result = analyze_command(args[position + 1], profile, _depth + 1)
                    if result and result[0] == "deny":
                        return result
                    first_ask = first_ask or result
                    break
        if program.startswith("mkfs") or (program == "dd" and any(
                re.match(r"of=/dev/", arg) for arg in args)):
            return "deny", "writing a filesystem or raw data to a block device"
        if program in {"chmod", "chown"} and _is_recursive(args) and any(
                arg in {"/", "/*"} for arg in args):
            return "deny", "recursive permission change on the filesystem root"
        if program == "git":
            sub, rest = _git_subcommand(args)
            if sub in {"add", "diff", "show", "blame", "cat-file"}:
                for operand in _clean_tokens(rest):
                    why = secret_reason(operand.rsplit(":", 1)[-1] if sub != "add" else operand)
                    if why:
                        effect = "stage" if sub == "add" else "print the contents of"
                        return "deny", f"git {sub} would {effect} a credential file: {why}"
            if sub == "push" and first_ask is None and (
                    any(arg in FORCE_FLAGS for arg in rest) or any(re.match(r"^\+\S", arg) for arg in rest)):
                first_ask = ("ask", "force push rewrites remote history")
            if strict and first_ask is None:
                if sub == "reset" and "--hard" in rest:
                    first_ask = ("ask", "git reset --hard discards uncommitted work")
                if sub == "clean" and _is_forced(rest):
                    first_ask = ("ask", "git clean deletes untracked files")
        if strict and first_ask is None:
            if elevated:
                first_ask = ("ask", "privileged command")
            elif program in {"npm", "pnpm", "yarn"} and "publish" in args:
                first_ask = ("ask", "publishing a package")
            elif program in {"terraform", "tofu"} and any(arg in {"apply", "destroy"} for arg in args):
                first_ask = ("ask", "infrastructure change")
            elif program == "kubectl" and "delete" in args:
                first_ask = ("ask", "deleting cluster resources")
        if program in READERS:
            for operand in _clean_tokens(args):
                why = secret_reason(operand)
                if why:
                    return "deny", f"{program} would expose a credential file: {why}"
    return first_ask


def decide_tool(event: dict, profile: str = "standard") -> tuple[str, str] | None:
    """Decide for one PreToolUse event. Unknown shapes are allowed."""
    tool = event.get("tool_name")
    tool_input = event.get("tool_input")
    if not isinstance(tool, str) or not isinstance(tool_input, dict):
        return None
    if tool in FILE_TOOLS:
        path = tool_input.get(FILE_TOOLS[tool])
        if isinstance(path, str) and path:
            why = secret_reason(path, write=tool in WRITE_TOOLS)
            if why:
                return "deny", f"{tool} on '{path}' refused: {why}"
            if tool in WRITE_TOOLS and SETTINGS_RE.search(path.replace("\\", "/")):
                return "ask", "editing Claude Code settings can change or disable hooks"
        return None
    if tool == "Bash":
        command = tool_input.get("command")
        if isinstance(command, str) and command.strip():
            return analyze_command(command, profile)
    return None


def render_tool_decision(decision: tuple[str, str]) -> str:
    kind, reason = decision
    guidance = ("Use a template such as .env.example or ask the user for the non-secret values."
                if kind == "deny" and "credential" in reason else "")
    text = f"RCoder guard: {reason}." + (f" {guidance}" if guidance else "")
    return json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": kind,
                                              "permissionDecisionReason": text}})


# ------------------------------------------------------------------------- stop gate

def _blocks(entry: dict) -> list[dict]:
    message = entry.get("message")
    content = message.get("content") if isinstance(message, dict) else None
    if isinstance(content, str):
        return [{"type": "text", "text": content}]
    return [block for block in content if isinstance(block, dict)] if isinstance(content, list) else []


def _is_real_user_prompt(entry: dict) -> bool:
    if entry.get("type") != "user" or entry.get("isSidechain"):
        return False
    blocks = _blocks(entry)
    return bool(blocks) and not any(block.get("type") == "tool_result" for block in blocks)


def read_transcript_tail(path: str) -> list[dict]:
    size = os.path.getsize(path)
    with open(path, "rb") as handle:
        if size > TAIL_BYTES:
            handle.seek(size - TAIL_BYTES)
            handle.readline()
        data = handle.read(TAIL_BYTES)
    entries = []
    for line in data.decode("utf-8", errors="replace").splitlines():
        try:
            item = json.loads(line)
        except ValueError:
            continue
        if isinstance(item, dict):
            entries.append(item)
    return entries


def _workspace_from_event(event: dict) -> Path:
    for candidate in (event.get("cwd"), os.environ.get("CLAUDE_PROJECT_DIR")):
        if isinstance(candidate, str) and candidate.strip():
            path = Path(candidate).expanduser()
            if path.is_dir():
                return path.resolve()
    return Path.cwd().resolve()


def _policy(workspace: Path) -> dict:
    path = workspace / POLICY_PATH
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _strict_stop_enabled(workspace: Path, policy: dict | None = None) -> bool:
    environment = os.environ.get(STRICT_STOP_ENV, "").strip()
    if environment == "1":
        return True
    if environment == "0":
        return False
    policy = policy if policy is not None else _policy(workspace)
    return policy.get("strict_stop") is True or policy.get("stop_gate") == "strict"


def _relative_claims(edited: list[str], workspace: Path) -> list[str]:
    claims: list[str] = []
    for item in edited:
        path = Path(item).expanduser()
        try:
            resolved = path.resolve() if path.is_absolute() else (workspace / path).resolve()
            claims.append(resolved.relative_to(workspace).as_posix())
        except (OSError, ValueError):
            continue
    return claims


def _last_verification_exit_code(entries: list[dict]) -> int | None:
    commands: dict[str, str] = {}
    last: int | None = None
    for entry in entries:
        for block in _blocks(entry):
            if block.get("type") == "tool_use" and block.get("name") == "Bash":
                payload = block.get("input") if isinstance(block.get("input"), dict) else {}
                command = payload.get("command")
                if isinstance(command, str) and CHECK_RE.search(command) and block.get("id"):
                    commands[str(block["id"])] = command
            elif block.get("type") == "tool_result":
                tool_id = block.get("tool_use_id")
                if not isinstance(tool_id, str) or tool_id not in commands:
                    continue
                content = block.get("content")
                text = " ".join(
                    part.get("text", "") for part in content if isinstance(part, dict)
                ) if isinstance(content, list) else str(content or "")
                if block.get("is_error") is True or re.search(r"(?i)\bexit code\s*[:=]?\s*[1-9]\d*\b", text):
                    last = 1
                else:
                    last = 0
    return last


def evaluate_stop_gate(workspace: Path, state: dict) -> str | None:
    """Opt-in strict stop gate; returns a block reason or ``None``."""
    workspace = Path(workspace).resolve()
    if not _strict_stop_enabled(workspace):
        return None
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from rsaver_guard import crosscheck_git_drift
    except ImportError:
        return None

    targets = [str(item) for item in state.get("target_files", []) if isinstance(item, str)]
    claims = [str(item) for item in state.get("claimed_files", []) if isinstance(item, str)]
    drift = crosscheck_git_drift(workspace, targets, claims)
    problems: list[str] = []
    if drift["untouched_targets"]:
        problems.append("objective targets not modified: " + ", ".join(drift["untouched_targets"]))
    if drift["unverified_claims"]:
        problems.append("claimed edits absent from git status: " + ", ".join(drift["unverified_claims"]))
    exit_code = state.get("last_verification_exit_code")
    if isinstance(exit_code, int) and exit_code != 0:
        problems.append(f"last recorded verification command exited {exit_code}")
    if not problems:
        return None
    return (
        "RCoder strict stop gate (RCODER_STRICT_STOP=1 or .rcoder/policy.json): "
        + "; ".join(problems)
        + ". Reconcile the objective, run the verification command, and retry the stop."
    )


def decide_stop(event: dict, entries: list[dict] | None = None) -> str | None:
    """Return a block reason, or ``None`` to let the session stop."""
    if event.get("stop_hook_active"):
        return None
    if entries is None:
        path = event.get("transcript_path")
        if not isinstance(path, str) or not path or not os.path.isfile(path):
            return None
        entries = read_transcript_tail(path)
    last_prompt = max((index for index, entry in enumerate(entries) if _is_real_user_prompt(entry)), default=-1)
    turn = [entry for entry in entries[last_prompt + 1:]
            if entry.get("type") == "assistant" and not entry.get("isSidechain")]
    final_text = ""
    edited: list[str] = []
    ran_check = False
    for entry in turn:
        for block in _blocks(entry):
            if block.get("type") == "text" and isinstance(block.get("text"), str) and block["text"].strip():
                final_text = block["text"]
            elif block.get("type") == "tool_use" and isinstance(block.get("input"), dict):
                name, tool_input = block.get("name"), block["input"]
                if name in WRITE_TOOLS:
                    target = tool_input.get("file_path") or tool_input.get("notebook_path")
                    if isinstance(target, str):
                        edited.append(target)
                elif name == "Bash" and isinstance(tool_input.get("command"), str):
                    ran_check = ran_check or bool(CHECK_RE.search(tool_input["command"]))
    code_changed = any(Path(item.replace("\\", "/")).suffix.lower() not in DOC_SUFFIXES for item in edited)
    if code_changed and final_text and CLAIM_RE.search(final_text) and not ran_check \
            and not LABEL_RE.search(final_text):
        return ("RCoder completion gate: this turn edited code and the final message claims completion, but no "
                "test, lint, or build command ran and no evidence labels were given. Run the narrowest relevant "
                "check, or restate the result with VERIFIED, INFERRED, or NOT VERIFIED labels and the exact "
                "commands that ran.")

    workspace = _workspace_from_event(event)
    policy = _policy(workspace)
    if _strict_stop_enabled(workspace, policy):
        targets = event.get("target_files") or policy.get("target_files") or []
        state = {
            "target_files": [item for item in targets if isinstance(item, str)],
            "claimed_files": _relative_claims(edited, workspace),
            "last_verification_exit_code": _last_verification_exit_code(entries),
        }
        reason = evaluate_stop_gate(workspace, state)
        if reason:
            return reason
    return None


# ----------------------------------------------------------------------- settings merge

def _command_for(handler: str, profile: str) -> str:
    script = str(Path(__file__).resolve())
    base = f'"{sys.executable}" "{script}" {handler}'
    return base + (f" --profile {profile}" if handler == "guard" and profile != "standard" else "")


def build_entries(only: tuple[str, ...], profile: str) -> dict[str, dict]:
    entries: dict[str, dict] = {}
    if "guard" in only:
        entries["PreToolUse"] = {
            "matcher": "Read|Edit|Write|MultiEdit|NotebookEdit|Grep|Bash",
            "hooks": [{"type": "command", "command": _command_for("guard", profile), "timeout": HOOK_TIMEOUT}]}
    if "stop-gate" in only:
        entries["Stop"] = {"hooks": [{"type": "command", "command": _command_for("stop-gate", profile),
                                      "timeout": HOOK_TIMEOUT}]}
    return entries


def _has_handler(event_entries: list, handler: str) -> bool:
    for entry in event_entries:
        for hook in entry.get("hooks", []) if isinstance(entry, dict) else []:
            command = hook.get("command", "") if isinstance(hook, dict) else ""
            if MARKER in command and re.search(rf"\s{re.escape(handler)}(\s|$)", command):
                return True
    return False


def settings_path(scope: str, root: Path, home: Path) -> Path:
    return (root if scope == "project" else home) / ".claude" / "settings.json"


def _load_settings(path: Path) -> dict:
    if path.is_symlink() or path.parent.is_symlink():
        raise ValueError("refusing to modify a symbolic link")
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise ValueError(f"{path} is not strict JSON ({exc}); left untouched") from exc
    if not isinstance(data, dict) or not isinstance(data.get("hooks", {}), dict):
        raise ValueError(f"{path} has an unexpected shape; left untouched")
    return data


def _write_settings(path: Path, data: dict) -> str | None:
    path.parent.mkdir(parents=True, exist_ok=True)
    backup = None
    if path.exists():
        backup = f"{path}.rcoder-backup-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        Path(backup).write_bytes(path.read_bytes())
    handle, temp = tempfile.mkstemp(dir=str(path.parent), prefix=".rcoder-", suffix=".tmp")
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            json.dump(data, stream, indent=2)
            stream.write("\n")
        os.replace(temp, path)
    except BaseException:
        if os.path.exists(temp):
            os.unlink(temp)
        raise
    return backup


def install(path: Path, only: tuple[str, ...], profile: str, dry_run: bool) -> tuple[str, list[str]]:
    data = _load_settings(path)
    hooks = data.setdefault("hooks", {})
    added: list[str] = []
    for event, entry in build_entries(only, profile).items():
        handler = "guard" if event == "PreToolUse" else "stop-gate"
        bucket = hooks.setdefault(event, [])
        if not isinstance(bucket, list):
            raise ValueError(f"hooks.{event} in {path} is not a list; left untouched")
        if not _has_handler(bucket, handler):
            bucket.append(entry)
            added.append(f"{event}:{handler}")
    if not added:
        return "already installed; no change", []
    if dry_run:
        return "dry run; nothing written\n" + json.dumps(data, indent=2), added
    backup = _write_settings(path, data)
    return f"installed {', '.join(added)} in {path}" + (f" (backup {backup})" if backup else ""), added


def uninstall(path: Path, dry_run: bool) -> tuple[str, list[str]]:
    data = _load_settings(path)
    hooks = data.get("hooks", {})
    removed: list[str] = []
    for event in list(hooks):
        bucket = hooks[event]
        if not isinstance(bucket, list):
            continue
        kept = []
        for entry in bucket:
            inner = [hook for hook in entry.get("hooks", []) if isinstance(hook, dict)] if isinstance(entry, dict) else []
            ours = [hook for hook in inner if MARKER in hook.get("command", "")]
            if ours and len(ours) == len(inner):
                removed.append(event)
                continue
            if ours:
                entry["hooks"] = [hook for hook in inner if hook not in ours]
                removed.append(event)
            kept.append(entry)
        if kept:
            hooks[event] = kept
        else:
            del hooks[event]
    if not removed:
        return "no RCoder hooks found; no change", []
    if not hooks:
        data.pop("hooks", None)
    if dry_run:
        return "dry run; nothing written\n" + json.dumps(data, indent=2), removed
    backup = _write_settings(path, data)
    return f"removed RCoder hooks from {path}" + (f" (backup {backup})" if backup else ""), removed


# ------------------------------------------------------------------------------- cli

def _only(value: str) -> tuple[str, ...]:
    chosen = tuple(item.strip() for item in value.split(",") if item.strip())
    if not chosen or any(item not in HANDLERS for item in chosen):
        raise argparse.ArgumentTypeError(f"choose from: {', '.join(HANDLERS)}")
    return chosen


def _read_event() -> dict | None:
    raw = sys.stdin.buffer.read(MAX_STDIN + 1)
    if not raw or len(raw) > MAX_STDIN:
        return None
    try:
        event = json.loads(raw.decode("utf-8", errors="replace"))
    except ValueError:
        return None
    return event if isinstance(event, dict) else None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="rcoder_hooks.py", description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    guard = sub.add_parser("guard", help="PreToolUse handler; reads one event as JSON on stdin")
    guard.add_argument("--profile", choices=PROFILES, default="standard")
    sub.add_parser("stop-gate", help="Stop handler; reads one event as JSON on stdin")
    for name, text in (("print-config", "print a Claude Code settings snippet"),
                       ("install", "merge the hooks into a Claude Code settings file"),
                       ("uninstall", "remove RCoder hooks from a Claude Code settings file")):
        cmd = sub.add_parser(name, help=text)
        if name != "uninstall":
            cmd.add_argument("--profile", choices=PROFILES, default="standard")
            cmd.add_argument("--only", type=_only, default=HANDLERS, help="comma list: guard,stop-gate")
        if name == "print-config":
            cmd.add_argument("--host", default="claude-code")
        else:
            cmd.add_argument("--scope", choices=("project", "user"), default="project")
            cmd.add_argument("--root", default=".", help="project root for project scope")
            cmd.add_argument("--home", default=None, help="override the home directory for user scope")
            cmd.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command in {"guard", "stop-gate"}:
        if os.environ.get(DISABLE_ENV) == "1":
            return 0
        try:
            event = _read_event()
            if event is None:
                return 0
            if args.command == "guard":
                decision = decide_tool(event, args.profile)
                if decision:
                    print(render_tool_decision(decision))
            else:
                reason = decide_stop(event)
                if reason:
                    print(json.dumps({"decision": "block", "reason": reason}))
        except Exception as exc:  # fail open: a broken guard must never wedge a session
            print(f"rcoder_hooks: ignored internal error: {type(exc).__name__}", file=sys.stderr)
        return 0
    if args.command == "print-config":
        if args.host != "claude-code":
            print(f"rcoder_hooks: host '{args.host}' is not supported; only claude-code has documented "
                  "PreToolUse and Stop hooks. Other hosts are NOT VERIFIED.", file=sys.stderr)
            return 2
        print(json.dumps({"hooks": {event: [entry] for event, entry in
                                    build_entries(args.only, args.profile).items()}}, indent=2))
        return 0
    path = settings_path(args.scope, Path(args.root).resolve(), Path(args.home) if args.home else Path.home())
    try:
        message, _ = (install(path, args.only, args.profile, args.dry_run) if args.command == "install"
                      else uninstall(path, args.dry_run))
    except (ValueError, OSError) as exc:
        print(f"rcoder_hooks: {exc}", file=sys.stderr)
        return 2
    print(message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
