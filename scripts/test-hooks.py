#!/usr/bin/env python3
"""Self-test for the opt-in RCoder hook handlers (guard, stop-gate, settings merge)."""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "skills" / "rcoder" / "scripts" / "rcoder_hooks.py"
WRAPPER = ROOT / "scripts" / "rcoder-hooks.py"
MCP = ROOT / "skills" / "rcoder" / "scripts" / "rcoder_mcp.py"
CHECKS = 0


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


hooks = load(SCRIPT, "rcoder_hooks_under_test")


def check(condition, message):
    global CHECKS
    CHECKS += 1
    if not condition:
        raise AssertionError(message)


def run(args, stdin="", env=None, cwd=None):
    merged = dict(os.environ)
    merged.pop(hooks.DISABLE_ENV, None)
    merged.update(env or {})
    return subprocess.run([sys.executable, str(SCRIPT), *args], input=stdin, capture_output=True, text=True,
                          timeout=30, env=merged, cwd=cwd)


def bash(command, profile="standard"):
    return hooks.decide_tool({"tool_name": "Bash", "tool_input": {"command": command}}, profile)


def kind(decision):
    return decision[0] if decision else None


# ----------------------------------------------------------------- guard: file tools
for path in (".env", "app/.env.local", "~/.ssh/id_rsa", "C:\\Users\\me\\.ssh\\id_ed25519", "certs/server.pem",
             "deploy/server.key", ".npmrc", "infra/terraform.tfstate", "config/service-account-prod.json",
             "secrets.yaml", "/home/me/.aws/credentials", ".kube/config", "credentials.json",
             "/home/me/.docker/config.json"):
    check(kind(hooks.decide_tool({"tool_name": "Read", "tool_input": {"file_path": path}})) == "deny",
          f"Read of {path} must be denied")
for path in (".env.example", ".env.sample", "id_rsa.pub", "README.md", "src/envelope.py", ".envrc",
             "docs/secrets-policy.md", ".docker/Dockerfile", "src/credentials_test.py", "keys.md"):
    check(kind(hooks.decide_tool({"tool_name": "Read", "tool_input": {"file_path": path}})) is None,
          f"Read of {path} must be allowed")
check(kind(hooks.decide_tool({"tool_name": "Write", "tool_input": {"file_path": ".git/config"}})) == "deny",
      "writing inside .git must be denied")
check(kind(hooks.decide_tool({"tool_name": "Read", "tool_input": {"file_path": ".git/HEAD"}})) is None,
      "reading .git metadata is allowed")
check(kind(hooks.decide_tool({"tool_name": "Edit", "tool_input": {"file_path": ".claude/settings.json"}})) == "ask",
      "editing hook settings must ask")
check(kind(hooks.decide_tool({"tool_name": "Grep", "tool_input": {"path": ".env", "pattern": "KEY"}})) == "deny",
      "Grep on a credential file must be denied")
check(kind(hooks.decide_tool({"tool_name": "NotebookEdit", "tool_input": {"notebook_path": "a.ipynb"}})) is None,
      "ordinary notebook edit is allowed")

# ---------------------------------------------------------------- guard: shell commands
# The hostile commands live in a data file: scripts/validate-all (G5) forbids risky command literals in
# scripts/*, and these strings are only ever classified, never executed.
CASES = json.loads((ROOT / "scripts" / "fixtures" / "hook-guard-cases.json").read_text(encoding="utf-8"))
for command in CASES["deny"]:
    check(kind(bash(command)) == "deny", f"command must be denied: {command}")
for command in CASES["allow"]:
    check(bash(command) is None, f"command must be allowed: {command}")
for command in CASES["ask"]:
    check(kind(bash(command)) == "ask", f"command must ask: {command}")
nested_depth = "bash -c \"" * 5 + "cat .env"
check(bash(nested_depth) is None or kind(bash(nested_depth)) == "deny", "deep nesting must not crash")
for command in CASES["strict_ask"]:
    check(bash(command, "standard") is None, f"standard profile must allow: {command}")
    check(kind(bash(command, "strict")) == "ask", f"strict profile must ask: {command}")
check(kind(bash("cat .env", "strict")) == "deny", "strict keeps every standard denial")

# --------------------------------------------------------------- guard: process contract
denied = run(["guard"], json.dumps({"hook_event_name": "PreToolUse", "tool_name": "Read",
                                    "tool_input": {"file_path": ".env"}}))
check(denied.returncode == 0, "guard exits zero even when it denies")
payload = json.loads(denied.stdout)["hookSpecificOutput"]
check(payload["hookEventName"] == "PreToolUse" and payload["permissionDecision"] == "deny", "deny payload shape")
check("RCoder guard" in payload["permissionDecisionReason"] and ".env.example" in payload["permissionDecisionReason"],
      "deny reason must explain and offer an alternative")
asked = run(["guard", "--profile", "strict"], json.dumps({"tool_name": "Bash", "tool_input": {"command": "sudo ls"}}))
check(json.loads(asked.stdout)["hookSpecificOutput"]["permissionDecision"] == "ask", "ask payload shape")
for hostile in ("", "not json", "[]", "null", '{"tool_name": 5, "tool_input": []}', '{"tool_name": "Bash"}',
                '{"tool_name": "Bash", "tool_input": {"command": 7}}', "\x00\x01", "{" * 10):
    result = run(["guard"], hostile)
    check(result.returncode == 0 and result.stdout == "", f"guard must fail open on {hostile!r}")
big = run(["guard"], "{" + '"x":"' + "a" * 1_100_000 + '"}')
check(big.returncode == 0 and big.stdout == "", "oversized events fail open")
disabled = run(["guard"], json.dumps({"tool_name": "Read", "tool_input": {"file_path": ".env"}}),
               env={hooks.DISABLE_ENV: "1"})
check(disabled.returncode == 0 and disabled.stdout == "", "the disable variable must switch handlers off")
via_wrapper = subprocess.run([sys.executable, str(WRAPPER), "guard"], input=json.dumps(
    {"tool_name": "Bash", "tool_input": {"command": CASES["wrapper_deny"]}}), capture_output=True, text=True, timeout=30)
check("deny" in via_wrapper.stdout, "repository-root wrapper must reach the canonical script")

# ------------------------------------------------------------------ secret regex parity
mcp = load(MCP, "rcoder_mcp_for_hook_parity")
for sample in (".env", ".env.production", "id_rsa", "id_ed25519", "server.pem", "tls.key", "store.p12", "a.pfx",
               "b.jks", "c.keystore", "d.kdbx", ".npmrc", ".pypirc", ".netrc", ".git-credentials", "credentials",
               "secrets.json", "secret.yaml", "secrets.toml"):
    if mcp.SECRET_NAME_RE.search(sample):
        check(hooks.SECRET_NAME_RE.search(sample), f"hook regex must cover the MCP credential name {sample}")
check(set(mcp.SECRET_DIRS) - {".git", ".docker"} <= hooks.SECRET_DIRS, "hook must cover the MCP secret directories")

# ------------------------------------------------------------------------- stop gate
def user(text):
    return {"type": "user", "message": {"role": "user", "content": text}}


def tool_result():
    return {"type": "user", "message": {"role": "user", "content": [{"type": "tool_result", "content": "ok"}]}}


def assistant(*blocks):
    return {"type": "assistant", "message": {"role": "assistant", "content": list(blocks)}}


def text(value):
    return {"type": "text", "text": value}


def edit(path):
    return {"type": "tool_use", "name": "Edit", "input": {"file_path": path, "old_string": "a", "new_string": "b"}}


def shell(command):
    return {"type": "tool_use", "name": "Bash", "input": {"command": command}}


claim = "I've fixed the parser bug and everything is working now."
cases = {
    "block: code edited, claim, no check, no labels": ([user("fix it"), assistant(edit("src/a.py")),
                                                          tool_result(), assistant(text(claim))], True),
    "allow: a test command ran": ([user("fix it"), assistant(edit("src/a.py"), shell("python3 -m pytest -q")),
                                    tool_result(), assistant(text(claim))], False),
    "allow: evidence labels present": ([user("fix it"), assistant(edit("src/a.py")), tool_result(),
                                         assistant(text(claim + " Tests: NOT VERIFIED."))], False),
    "allow: only docs edited": ([user("doc it"), assistant(edit("README.md")), tool_result(),
                                  assistant(text(claim))], False),
    "allow: nothing edited": ([user("explain"), assistant(text(claim))], False),
    "allow: no completion claim": ([user("fix it"), assistant(edit("src/a.py")), tool_result(),
                                     assistant(text("Here is the diff for review."))], False),
    "allow: earlier turn edited, this turn did not": ([user("fix it"), assistant(edit("src/a.py")),
                                                        tool_result(), assistant(text(claim)),
                                                        user("thanks, what next?"), assistant(text(claim))], False),
}
for label, (entries, expect_block) in cases.items():
    reason = hooks.decide_stop({}, entries)
    check(bool(reason) == expect_block, f"stop gate: {label}")
check(hooks.decide_stop({"stop_hook_active": True}, cases["block: code edited, claim, no check, no labels"][0])
      is None, "stop_hook_active must always allow, which prevents loops")
check(hooks.decide_stop({"transcript_path": "/nonexistent/transcript.jsonl"}) is None, "missing transcript allows")

with tempfile.TemporaryDirectory() as tmp:
    transcript = Path(tmp) / "t.jsonl"
    lines = ["garbage not json"] + [json.dumps(item) for item in cases["block: code edited, claim, no check, no labels"][0]]
    transcript.write_text("\n".join(lines) + "\n", encoding="utf-8")
    event = {"hook_event_name": "Stop", "transcript_path": str(transcript), "stop_hook_active": False}
    blocked = run(["stop-gate"], json.dumps(event))
    body = json.loads(blocked.stdout)
    check(blocked.returncode == 0 and body["decision"] == "block" and "completion gate" in body["reason"],
          "stop-gate process must emit a block decision")
    again = run(["stop-gate"], json.dumps({**event, "stop_hook_active": True}))
    check(again.returncode == 0 and again.stdout == "", "second stop must pass")
    padded = Path(tmp) / "big.jsonl"
    filler = json.dumps(assistant(text("x" * 5000)))
    padded.write_text("\n".join([filler] * 120 + lines[1:]) + "\n", encoding="utf-8")
    check(json.loads(run(["stop-gate"], json.dumps({**event, "transcript_path": str(padded)})).stdout)["decision"] == "block",
          "a transcript larger than the tail window must still be evaluated from its tail")

    # --------------------------------------------------------------- settings merge
    project = Path(tmp) / "proj"
    project.mkdir()
    snippet = run(["print-config"])
    config = json.loads(snippet.stdout)["hooks"]
    check(set(config) == {"PreToolUse", "Stop"}, "print-config covers both handlers")
    command = config["PreToolUse"][0]["hooks"][0]["command"]
    check(sys.executable in command and "rcoder_hooks.py" in command and command.endswith("guard"),
          "print-config uses the absolute interpreter and script")
    check(json.loads(run(["print-config", "--only", "guard", "--profile", "strict"]).stdout)["hooks"]["PreToolUse"][0]
          ["hooks"][0]["command"].endswith("guard --profile strict"), "profile and --only are honored")
    check(run(["print-config", "--host", "cursor"]).returncode == 2, "unsupported hosts are refused")
    check(run(["print-config", "--only", "nope"]).returncode == 2, "unknown handler names are refused")

    dry = run(["install", "--root", str(project), "--dry-run"])
    check(dry.returncode == 0 and "dry run" in dry.stdout and not (project / ".claude").exists(),
          "dry run must not write")
    first = run(["install", "--root", str(project)])
    settings = project / ".claude" / "settings.json"
    check(first.returncode == 0 and settings.is_file(), "install writes project settings")
    check(not list(settings.parent.glob("*.rcoder-backup-*")), "no backup when no file existed")
    second = run(["install", "--root", str(project)])
    check("already installed" in second.stdout, "install is idempotent")
    check(len(json.loads(settings.read_text())["hooks"]["PreToolUse"]) == 1, "idempotent install adds no duplicate")

    other = {"permissions": {"allow": ["Bash(ls:*)"]},
             "hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "echo mine"}]}],
                       "SessionStart": [{"matcher": "startup", "hooks": [{"type": "command", "command": "echo s"}]}]}}
    settings.write_text(json.dumps(other), encoding="utf-8")
    merged = run(["install", "--root", str(project), "--only", "guard"])
    data = json.loads(settings.read_text())
    check(merged.returncode == 0 and "backup" in merged.stdout and list(settings.parent.glob("*.rcoder-backup-*")),
          "install over an existing file writes a backup")
    check(data["permissions"] == other["permissions"] and data["hooks"]["SessionStart"] == other["hooks"]["SessionStart"],
          "install must preserve unrelated settings and hooks")
    check(len(data["hooks"]["PreToolUse"]) == 2 and "Stop" not in data["hooks"], "install appends only what was asked")
    removed = run(["uninstall", "--root", str(project)])
    after = json.loads(settings.read_text())
    check(removed.returncode == 0 and after["hooks"]["PreToolUse"] == other["hooks"]["PreToolUse"]
          and after["hooks"]["SessionStart"] == other["hooks"]["SessionStart"] and after["permissions"] == other["permissions"],
          "uninstall removes only RCoder entries")
    check("no change" in run(["uninstall", "--root", str(project)]).stdout, "uninstall is idempotent")

    broken = Path(tmp) / "broken"
    (broken / ".claude").mkdir(parents=True)
    (broken / ".claude" / "settings.json").write_text('{ // comment\n "hooks": {} }', encoding="utf-8")
    refused = run(["install", "--root", str(broken)])
    check(refused.returncode == 2 and "not strict JSON" in refused.stderr, "non-strict JSON is left untouched")
    check((broken / ".claude" / "settings.json").read_text(encoding="utf-8").startswith("{ // comment"),
          "a refused install must not modify the file")
    wrong = Path(tmp) / "wrong"
    (wrong / ".claude").mkdir(parents=True)
    (wrong / ".claude" / "settings.json").write_text('{"hooks": {"Stop": "nope"}}', encoding="utf-8")
    check(run(["install", "--root", str(wrong)]).returncode == 2, "an unexpected hooks shape is refused")

    home = Path(tmp) / "home"
    home.mkdir()
    user_scope = run(["install", "--scope", "user", "--home", str(home), "--only", "stop-gate"])
    check(user_scope.returncode == 0 and "Stop" in json.loads((home / ".claude" / "settings.json").read_text())["hooks"],
          "user scope writes under the chosen home")

    try:
        linked = Path(tmp) / "linked"
        (linked / ".claude").mkdir(parents=True)
        (Path(tmp) / "real.json").write_text("{}", encoding="utf-8")
        (linked / ".claude" / "settings.json").symlink_to(Path(tmp) / "real.json")
    except (OSError, NotImplementedError):
        pass
    else:
        check(run(["install", "--root", str(linked)]).returncode == 2, "symbolic links are refused")

# ------------------------------------------------------------------ static safety
import ast

tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
imported = set()
for node in ast.walk(tree):
    if isinstance(node, ast.Import):
        imported.update(alias.name.split(".")[0] for alias in node.names)
    elif isinstance(node, ast.ImportFrom):
        imported.add((node.module or "").split(".")[0])
    elif isinstance(node, ast.Call):
        target = node.func
        name = target.id if isinstance(target, ast.Name) else getattr(target, "attr", "")
        check(name not in {"eval", "exec", "system", "popen", "Popen", "run", "call", "check_output", "__import__"},
              f"rcoder_hooks.py must not call {name}")
        check(not any(kw.arg == "shell" for kw in node.keywords), "rcoder_hooks.py must not pass shell=")
check(not imported & {"subprocess", "socket", "ssl", "urllib", "http", "requests", "asyncio", "ctypes", "pickle"},
      f"rcoder_hooks.py imports a forbidden module: {sorted(imported)}")
check(not (ROOT / "hooks" / "hooks.json").read_text(encoding="utf-8").count("rcoder_hooks"),
      "the bundled plugin hook file must not enable the opt-in handlers (D-019, D-021)")

print(f"rcoder_hooks: {CHECKS} checks passed")
