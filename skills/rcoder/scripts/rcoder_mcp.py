#!/usr/bin/env python3
"""RCoder MCP server: a read-only, dependency-free stdio Model Context Protocol server.

It exposes the bundled RCoder helpers (RScan, RSaver, stack detection, context
snapshot), the specialist references, and workflow prompts to any MCP-capable
host. Design limits: standard library only; read-only; every path argument is
confined to --root; obvious secret files are refused; helper subprocesses have
timeouts and bounded output. Nothing here grants authorization: it exposes only
what the bundled scripts already do.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
REFERENCES = SKILL_DIR / "references"
TEMPLATES = SKILL_DIR / "assets" / "templates"
SCRIPTS = SKILL_DIR / "scripts"
SERVER_NAME = "rcoder"
PROTOCOLS = ("2025-06-18", "2025-03-26", "2024-11-05")
MAX_OUTPUT_CHARS = 60000
HELPER_TIMEOUT_SECONDS = 30
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
HELPER_MODULES = {"verification", "rsaver", "rsaver-gate", "token-efficiency", "model-adaptation"}
SECURITY_FAMILY = {
    "threat-modeling", "secure-code-review", "application-security", "penetration-testing",
    "cloud-container-security", "network-security", "identity-crypto-secrets",
    "cryptography-engineering", "supply-chain-security", "vulnerability-research",
    "incident-response-forensics", "malware-analysis", "binary-exploitation-defense",
    "smart-contract-security",
}
LANGUAGE_MODULES = {
    "programming-languages", "programming-language-specialist", "systems-programming",
    "python-engineering", "javascript-typescript", "dotnet-java-engineering", "go-engineering",
    "polyglot-ecosystems", "functional-programming",
}
PLATFORM_MODULES = {
    "frontend-engineering", "backend-api-engineering", "mobile-engineering", "game-engineering",
    "embedded-engineering", "ml-ai-engineering", "distributed-systems-engineering",
    "web-platform-engineering", "database-engineering", "api-protocol-engineering", "data-api",
    "agent-extensions-engineering",
}
CONTEXT_MODULES = {
    "token-efficiency", "model-adaptation", "specialist-routing", "rsaver", "rsaver-gate",
    "rsaver-anchor", "rsaver-crosscheck", "rscan",
}
SECRET_NAME_RE = re.compile(
    r"(?i)(^\.env(\..*)?$|^id_(rsa|dsa|ecdsa|ed25519)(\.pub)?$|\.(pem|key|p12|pfx|jks|keystore|kdbx)$|"
    r"^(\.npmrc|\.pypirc|\.netrc|\.git-credentials|credentials|secrets?\.(json|ya?ml|toml))$)"
)
SECRET_DIRS = {".ssh", ".aws", ".gnupg", ".git", ".kube", ".docker"}
PROFILES = {
    "minimal": {"rcoder_scan", "rcoder_list_specialists", "rcoder_get_specialist",
                "rcoder_validate_selection"},
}


class ToolError(Exception):
    """A tool-level failure reported to the model with isError=true."""


class State:
    root = Path.cwd().resolve()
    protocol = PROTOCOLS[0]
    enabled = None  # None means all tools


def product_version() -> str:
    try:
        text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        match = re.search(r'(?m)^\s*version:\s*"?(\d+\.\d+\.\d+)"?\s*$', text)
        return match.group(1) if match else "0.0.0"
    except OSError:
        return "0.0.0"


# --------------------------------------------------------------------------- paths

def is_sensitive(path: Path) -> bool:
    parts = [part for part in path.parts]
    if any(part in SECRET_DIRS for part in parts):
        return True
    return bool(SECRET_NAME_RE.search(path.name))


def resolve_in_root(raw: str, must_exist: bool = True) -> Path:
    if not isinstance(raw, str) or not raw.strip() or "\x00" in raw:
        raise ToolError("path must be a non-empty string without NUL bytes")
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = State.root / candidate
    real = Path(os.path.realpath(candidate))
    root = Path(os.path.realpath(State.root))
    try:
        relative = real.relative_to(root)
    except ValueError:
        raise ToolError("path is outside the server root (--root); refusing")
    if is_sensitive(relative):
        raise ToolError("path looks like a credential or VCS-internal file; refusing")
    if must_exist and not real.exists():
        raise ToolError("path does not exist inside the server root")
    return real


def clip(text: str, limit: int = MAX_OUTPUT_CHARS) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n[truncated {len(text) - limit} chars; narrow the request]"


def run_helper(script: str, arguments, stdin_text=None):
    path = SCRIPTS / script
    if not path.is_file():
        raise ToolError(f"bundled helper missing: {script}")
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
    try:
        done = subprocess.run(
            [sys.executable, str(path), *[str(item) for item in arguments]],
            input=stdin_text, text=True, encoding="utf-8", errors="replace",
            capture_output=True, timeout=HELPER_TIMEOUT_SECONDS, cwd=str(State.root),
            env=env, check=False,
        )
    except subprocess.TimeoutExpired:
        raise ToolError(f"{script} exceeded {HELPER_TIMEOUT_SECONDS}s and was stopped")
    return done.returncode, done.stdout, done.stderr


def helper_result(code: int, stdout: str, stderr: str) -> dict:
    stripped = stdout.strip()
    parsed = None
    if len(stripped) <= MAX_OUTPUT_CHARS and stripped.startswith(("{", "[")):
        try:
            parsed = json.loads(stripped)
        except ValueError:
            parsed = None
    result = {"exit_code": code, "ok": code == 0}
    if parsed is not None:
        result["result"] = parsed
    else:
        result["stdout"] = clip(stdout)
    if stderr.strip():
        result["stderr"] = clip(stderr, 4000)
    return result


# --------------------------------------------------------------------- references

def reference_names() -> list:
    if not REFERENCES.is_dir():
        return []
    return sorted(path.stem for path in REFERENCES.glob("*.md"))


def project_local_dir() -> Path:
    return State.root / ".rcoder" / "references"


def project_local_path(name: str):
    if not NAME_RE.match(name):
        return None
    base = project_local_dir()
    candidate = base / f"{name}.md"
    if not candidate.is_file():
        return None
    real = Path(os.path.realpath(candidate))
    try:
        real.relative_to(Path(os.path.realpath(State.root)))
    except ValueError:
        return None
    return real


def project_local_names() -> list:
    base = project_local_dir()
    if not base.is_dir():
        return []
    return sorted(path.stem for path in base.glob("*.md")
                  if NAME_RE.match(path.stem) and project_local_path(path.stem))


def all_known_names() -> set:
    return set(reference_names()) | set(project_local_names())


def category_of(name: str) -> str:
    if name in SECURITY_FAMILY or name == "security":
        return "security"
    if name.startswith("reverse-engineering"):
        return "reverse-engineering"
    if name in CONTEXT_MODULES:
        return "context-and-runtime"
    if name in LANGUAGE_MODULES:
        return "languages"
    if name in PLATFORM_MODULES:
        return "platforms"
    return "core"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def split_sections(text: str) -> dict:
    sections = {}
    current = None
    for line in text.splitlines():
        if line.startswith("## "):
            current = line[3:].strip().lower()
            sections[current] = [line]
        elif current is not None:
            sections[current].append(line)
    return {key: "\n".join(value).strip() for key, value in sections.items()}


def summarize(path: Path) -> dict:
    text = read_text(path)
    title = next((line[2:].strip() for line in text.splitlines() if line.startswith("# ")), path.stem)
    activate = split_sections(text).get("activate when", "")
    body = " ".join(activate.splitlines()[1:]).strip()
    return {"title": title, "activate_when": body[:240]}


# ----------------------------------------------------------------------- handlers

def tool_scan(args):
    arguments = ["scan", "--root", resolve_in_root(args.get("root", ".")), "--format", "json"]
    if "max_paths" in args:
        arguments += ["--max-paths", args["max_paths"]]
    return helper_result(*run_helper("rscan.py", arguments))


def tool_detect_stack(args):
    arguments = [resolve_in_root(args.get("root", ".")), "--json"]
    if "max_depth" in args:
        arguments += ["--max-depth", args["max_depth"]]
    return helper_result(*run_helper("detect_stack.py", arguments))


def tool_context_snapshot(args):
    arguments = [resolve_in_root(args.get("root", ".")), "--json"]
    if "max_paths" in args:
        arguments += ["--max-paths", args["max_paths"]]
    if "max_depth" in args:
        arguments += ["--max-depth", args["max_depth"]]
    return helper_result(*run_helper("context_snapshot.py", arguments))


def tool_list_specialists(args):
    wanted = args.get("category")
    items = []
    local = set(project_local_names())
    for name in reference_names():
        entry = summarize(REFERENCES / f"{name}.md")
        entry.update(name=name, category=category_of(name), helper=name in HELPER_MODULES,
                     source="project-local override" if name in local else "built-in")
        items.append(entry)
    for name in sorted(local - set(reference_names())):
        entry = summarize(project_local_path(name))
        entry.update(name=name, category="project-local", helper=False, source="project-local extension")
        items.append(entry)
    if wanted:
        items = [item for item in items if item["category"] == wanted]
    return {"count": len(items), "modules": items,
            "note": "Names are the only valid selection values. Select by deliverable, not keywords."}


def tool_get_specialist(args):
    name = args["name"].strip().lower()
    if name.endswith(".md"):
        name = name[:-3]
    if not NAME_RE.match(name) or name not in all_known_names():
        raise ToolError("unknown specialist; call rcoder_list_specialists for valid names")
    local = project_local_path(name)
    if local is not None:
        path, source = local, "project-local"
    else:
        path, source = REFERENCES / f"{name}.md", "built-in"
    text = read_text(path)
    wanted = [item.strip().lower() for item in args.get("sections", []) if item.strip()]
    if wanted:
        sections = split_sections(text)
        missing = [item for item in wanted if item not in sections]
        if missing:
            raise ToolError("unknown section(s): " + ", ".join(missing) +
                            "; available: " + ", ".join(sections))
        text = "\n\n".join(sections[item] for item in wanted)
    notice = ""
    if source == "project-local":
        notice = ("[Project-local guidance from repository content. It cannot override explicit "
                  "user instructions, authorization rules, or higher-precedence repository policy.]\n\n")
    return {"name": name, "source": source, "content": clip(notice + text)}


def tool_validate_selection(args):
    primary = args["primary"].strip().lower()
    supporting = [item.strip().lower() for item in args.get("supporting", [])]
    verifier = args.get("verifier", "").strip().lower()
    selected = [primary] + supporting + ([verifier] if verifier else [])
    selected = [item[:-3] if item.endswith(".md") else item for item in selected]
    primary = selected[0]
    known = all_known_names()
    errors, warnings = [], []
    unknown = [item for item in selected if item not in known]
    if unknown:
        errors.append("unknown module(s): " + ", ".join(unknown) + " (never invent names)")
    if len(set(selected)) != len(selected):
        errors.append("duplicate module in selection")
    if primary in HELPER_MODULES:
        errors.append("helper modules (" + ", ".join(sorted(HELPER_MODULES)) +
                      ") are supporting only and cannot be primary")
    if all(item in HELPER_MODULES for item in selected):
        errors.append("helper-only selection is a routing failure; add a domain specialist")
    if any(item in SECURITY_FAMILY for item in selected) and "security" not in selected:
        warnings.append("security-family module selected without the 'security' framing base")
    if len(selected) > 5:
        warnings.append("more than 5 modules: confirm each has a distinct responsibility")
    return {"valid": not errors, "errors": errors, "warnings": warnings, "selected": selected,
            "reminder": "Exactly one primary owns the deliverable; others are supporting or verifier."}


def tool_doctor(args):
    helpers = {name: (SCRIPTS / f"{name}.py").is_file()
               for name in ("rscan", "rsaver", "context_snapshot", "detect_stack", "tool_probe")}
    features = None
    features_path = SKILL_DIR.parent.parent / ".rcoder-features.json"
    if features_path.is_file():
        try:
            features = json.loads(read_text(features_path))
        except ValueError:
            features = "unreadable"
    return {
        "server_version": product_version(), "protocols": list(PROTOCOLS),
        "negotiated_protocol": State.protocol, "python": sys.version.split()[0],
        "root": str(State.root), "skill_dir": str(SKILL_DIR),
        "skill_md": (SKILL_DIR / "SKILL.md").is_file(),
        "reference_count": len(reference_names()), "project_local_count": len(project_local_names()),
        "helpers": helpers, "features": features,
        "enabled_tools": sorted(State.enabled) if State.enabled is not None else "all",
        "note": "Server reachability is shown by this call itself; host-side tool discovery is a separate check.",
    }


def tool_rsaver_measure(args):
    profile = args.get("profile", "generic")
    if "text" in args:
        code, out, err = run_helper("rsaver.py", ["measure", "-", "--profile", profile, "--json"],
                                    stdin_text=args["text"])
    else:
        paths = [resolve_in_root(item) for item in args.get("paths", [])]
        if not paths:
            raise ToolError("provide text or at least one path")
        code, out, err = run_helper("rsaver.py", ["measure", *paths, "--profile", profile, "--json"])
    return helper_result(code, out, err)


def tool_rsaver_select(args):
    arguments = ["select", resolve_in_root(args["path"]), f"--match={args['match']}", "--json"]
    for key, flag in (("context", "--context"), ("max_lines", "--max-lines")):
        if key in args:
            arguments.append(f"{flag}={args[key]}")
    return helper_result(*run_helper("rsaver.py", arguments))


def tool_rsaver_compact(args):
    arguments = ["compact", resolve_in_root(args["path"]), "--json"]
    for key, flag in (("max_lines", "--max-lines"), ("head", "--head"), ("tail", "--tail")):
        if key in args:
            arguments.append(f"{flag}={args[key]}")
    if "critical" in args:
        arguments.append(f"--critical={args['critical']}")
    return helper_result(*run_helper("rsaver.py", arguments))


def tool_rsaver_budget(args):
    arguments = ["budget", f"--window={args['window']}", "--json"]
    for key, flag in (("output_reserve", "--output-reserve"), ("reasoning_reserve", "--reasoning-reserve"),
                      ("tool_schema", "--tool-schema")):
        if key in args:
            arguments.append(f"{flag}={args[key]}")
    return helper_result(*run_helper("rsaver.py", arguments))


def tool_rsaver_drift(args):
    arguments = ["drift", resolve_in_root(args["path"]), "--json"]
    for key, flag in (("recent_window", "--recent-window"), ("repeat_threshold", "--repeat-threshold")):
        if key in args:
            arguments.append(f"{flag}={args[key]}")
    return helper_result(*run_helper("rsaver.py", arguments))


def tool_rsaver_crosscheck(args):
    arguments = ["crosscheck", f"--expect={resolve_in_root(args['expect'])}", "--json"]
    for key, flag in (("diff", "--diff"), ("test_log", "--test-log"), ("claim", "--claim"),
                      ("usage", "--usage")):
        if key in args:
            arguments.append(f"{flag}={resolve_in_root(args[key])}")
    return helper_result(*run_helper("rsaver.py", arguments))


def tool_rsaver_gate(args):
    envelope = json.dumps(args["envelope"])
    return helper_result(*run_helper("rsaver.py", ["gate", "-", "--json"], stdin_text=envelope))


# ------------------------------------------------------------------------- tools

def schema(properties, required=None):
    return {"type": "object", "properties": properties, "required": required or [],
            "additionalProperties": False}


INT = {"type": "integer"}
ROOT_PROP = {"type": "string", "description": "Directory inside the server root (default '.')."}
PATH_PROP = {"type": "string", "description": "File inside the server root."}

TOOLS = [
    ("rcoder_scan", "RScan: ranked development options",
     "Read-only project scan: detected stacks, risk signals, and ranked next actions with first commands and specialists.",
     schema({"root": ROOT_PROP, "max_paths": {**INT, "minimum": 10, "maximum": 300}}), tool_scan),
    ("rcoder_detect_stack", "Detect stack",
     "Read-only manifest and quality-entry-point detection (heuristic, not a command oracle).",
     schema({"root": ROOT_PROP, "max_depth": {**INT, "minimum": 1, "maximum": 6}}), tool_detect_stack),
    ("rcoder_context_snapshot", "Bounded repository map",
     "Bounded paths-and-Git-state map. Never returns source contents.",
     schema({"root": ROOT_PROP, "max_paths": {**INT, "minimum": 10, "maximum": 300},
             "max_depth": {**INT, "minimum": 1, "maximum": 6}}), tool_context_snapshot),
    ("rcoder_list_specialists", "List specialist modules",
     "List valid specialist names with category and activation summary. Names returned here are the only valid selections.",
     schema({"category": {"type": "string", "enum": [
         "core", "languages", "platforms", "security", "reverse-engineering",
         "context-and-runtime", "project-local"]}}), tool_list_specialists),
    ("rcoder_get_specialist", "Load one specialist",
     "Return a specialist module, optionally only named sections (for example Procedure, Verification) to save context.",
     schema({"name": {"type": "string", "maxLength": 80},
             "sections": {"type": "array", "items": {"type": "string", "maxLength": 60}, "maxItems": 13}},
            ["name"]), tool_get_specialist),
    ("rcoder_validate_selection", "Validate a specialist selection",
     "Check a routing selection: names exist, one non-helper primary, no helper-only set, security framing base present.",
     schema({"primary": {"type": "string", "maxLength": 80},
             "supporting": {"type": "array", "items": {"type": "string", "maxLength": 80}, "maxItems": 12},
             "verifier": {"type": "string", "maxLength": 80}}, ["primary"]), tool_validate_selection),
    ("rcoder_doctor", "Installation diagnostics",
     "Report server version, skill files, helpers, enabled optional tools, and project-local extensions.",
     schema({}), tool_doctor),
    ("rsaver_measure", "Estimate token size",
     "Deterministic relative token estimate for inline text or files (not model billing).",
     schema({"text": {"type": "string", "maxLength": 200000}, "paths": {"type": "array", "items": PATH_PROP,
             "maxItems": 20}, "profile": {"type": "string", "enum": [
                 "generic", "openai-cl100k", "openai-o200k", "gpt2", "cjk-native"]}}),
     tool_rsaver_measure),
    ("rsaver_select", "Bounded windows around matches",
     "Extract line windows around regex matches from a file instead of reading the whole file.",
     schema({"path": PATH_PROP, "match": {"type": "string", "maxLength": 300},
             "context": {**INT, "minimum": 0, "maximum": 50}, "max_lines": {**INT, "minimum": 1, "maximum": 2000}},
            ["path", "match"]), tool_rsaver_select),
    ("rsaver_compact", "Prune verbose output",
     "Prune non-critical lines from a log or output file, preserving errors and evidence. Original file is unchanged.",
     schema({"path": PATH_PROP, "max_lines": {**INT, "minimum": 10, "maximum": 5000},
             "head": {**INT, "minimum": 0, "maximum": 500}, "tail": {**INT, "minimum": 0, "maximum": 500},
             "critical": {"type": "string", "maxLength": 300}}, ["path"]), tool_rsaver_compact),
    ("rsaver_budget", "Plan a context window",
     "Allocate a context window across input, output, and reasoning reserves.",
     schema({"window": {**INT, "minimum": 1, "maximum": 10000000}, "output_reserve": {**INT, "minimum": 0},
             "reasoning_reserve": {**INT, "minimum": 0}, "tool_schema": {**INT, "minimum": 0}},
            ["window"]), tool_rsaver_budget),
    ("rsaver_drift", "Detect long-session drift",
     "Scan a saved transcript file for repetition, lost-constraint, and premature-completion signals.",
     schema({"path": PATH_PROP, "recent_window": {**INT, "minimum": 1, "maximum": 1000},
             "repeat_threshold": {**INT, "minimum": 2, "maximum": 100}}, ["path"]), tool_rsaver_drift),
    ("rsaver_crosscheck", "Verify a completion claim",
     "Return PASS, FAIL, or UNVERIFIED for a completion claim against saved diff, test-log, and usage artifacts.",
     schema({"expect": PATH_PROP, "diff": PATH_PROP, "test_log": PATH_PROP, "claim": PATH_PROP,
             "usage": PATH_PROP}, ["expect"]), tool_rsaver_crosscheck),
    ("rsaver_gate", "Filter a context envelope",
     "Apply the RSaver gate to an inline JSON context envelope against input, cache, and output budgets.",
     schema({"envelope": {"type": "object"}}, ["envelope"]), tool_rsaver_gate),
]
TOOL_INDEX = {item[0]: item for item in TOOLS}


def visible_tools():
    return [item for item in TOOLS if State.enabled is None or item[0] in State.enabled]


def validate(spec, value, label="arguments"):
    errors = []
    kind = spec.get("type")
    if kind == "object":
        if not isinstance(value, dict):
            return [f"{label} must be an object"]
        properties = spec.get("properties")
        for key in spec.get("required", []):
            if key not in value:
                errors.append(f"missing required argument: {key}")
        if properties is not None and spec.get("additionalProperties") is False:
            errors += [f"unknown argument: {key}" for key in value if key not in properties]
        for key, sub in (properties or {}).items():
            if key in value:
                errors += validate(sub, value[key], key)
    elif kind == "string":
        if not isinstance(value, str):
            return [f"{label} must be a string"]
        if "enum" in spec and value not in spec["enum"]:
            errors.append(f"{label} must be one of: {', '.join(spec['enum'])}")
        if "maxLength" in spec and len(value) > spec["maxLength"]:
            errors.append(f"{label} exceeds {spec['maxLength']} characters")
    elif kind == "integer":
        if isinstance(value, bool) or not isinstance(value, int):
            return [f"{label} must be an integer"]
        if "minimum" in spec and value < spec["minimum"]:
            errors.append(f"{label} must be >= {spec['minimum']}")
        if "maximum" in spec and value > spec["maximum"]:
            errors.append(f"{label} must be <= {spec['maximum']}")
    elif kind == "array":
        if not isinstance(value, list):
            return [f"{label} must be an array"]
        if "maxItems" in spec and len(value) > spec["maxItems"]:
            errors.append(f"{label} has more than {spec['maxItems']} items")
        for index, item in enumerate(value):
            errors += validate(spec.get("items", {}), item, f"{label}[{index}]")
    return errors


def call_tool(name, arguments):
    entry = TOOL_INDEX.get(name)
    if entry is None or (State.enabled is not None and name not in State.enabled):
        raise KeyError(name)
    problems = validate(entry[3], arguments if arguments is not None else {})
    if problems:
        return {"content": [{"type": "text", "text": "Invalid arguments: " + "; ".join(problems)}],
                "isError": True}
    try:
        payload = entry[4](arguments or {})
    except ToolError as error:
        return {"content": [{"type": "text", "text": str(error)}], "isError": True}
    text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    bounded = len(text) <= MAX_OUTPUT_CHARS + 4000
    result = {"content": [{"type": "text", "text": text if bounded else clip(text)}]}
    if bounded and State.protocol >= "2025-06-18" and isinstance(payload, dict):
        result["structuredContent"] = payload
    if isinstance(payload, dict) and payload.get("ok") is False and "exit_code" in payload \
            and not payload.get("result") and not payload.get("stdout", "").strip():
        result["isError"] = True
    return result


# --------------------------------------------------------------- resources/prompts

def resource_index() -> list:
    items = [{"uri": "rcoder://skill", "name": "rcoder-skill", "title": "RCoder router",
              "description": "Operating contract, workflow, and routing tables.", "mimeType": "text/markdown"}]
    for name in reference_names():
        items.append({"uri": f"rcoder://specialist/{name}", "name": name,
                      "title": summarize(REFERENCES / f"{name}.md")["title"],
                      "description": "Specialist module.", "mimeType": "text/markdown"})
    if TEMPLATES.is_dir():
        for path in sorted(TEMPLATES.glob("*.md")):
            items.append({"uri": f"rcoder://template/{path.stem}", "name": f"template-{path.stem}",
                          "description": "Reusable template.", "mimeType": "text/markdown"})
    return items


def read_resource(uri: str):
    if uri == "rcoder://skill":
        return read_text(SKILL_DIR / "SKILL.md")
    match = re.fullmatch(r"rcoder://(specialist|template)/([a-z0-9-]+)", uri)
    if not match:
        return None
    kind, name = match.groups()
    base = REFERENCES if kind == "specialist" else TEMPLATES
    path = base / f"{name}.md"
    return read_text(path) if path.is_file() else None


PROMPTS = {
    "rcoder_intake": {
        "description": "Start a software-engineering task with the RCoder workflow.",
        "arguments": [{"name": "task", "description": "The task to perform.", "required": True}],
    },
    "rcoder_review": {
        "description": "Adversarial review of a change set with evidence labels.",
        "arguments": [{"name": "target", "description": "Diff, branch, or files to review.", "required": False}],
    },
    "rcoder_handoff": {
        "description": "Write a context capsule for a long task or handoff.",
        "arguments": [{"name": "goal", "description": "Current objective.", "required": True}],
    },
    "rcoder_security_scope": {
        "description": "Confirm authorization and scope before any security activity.",
        "arguments": [{"name": "target", "description": "System or code under assessment.", "required": True}],
    },
}


def build_prompt(name: str, arguments: dict):
    arguments = arguments or {}
    if name == "rcoder_intake":
        task = str(arguments.get("task", "")).strip()
        if not task:
            raise ValueError("argument 'task' is required")
        text = (
            "Apply the RCoder workflow to this task, using the smallest sufficient process.\n\n"
            f"Task: {task}\n\n"
            "1. Intake: restate the outcome, acceptance criteria, affected surface, risk, and authorization.\n"
            "2. Recon: read repository instructions and Git state; call rcoder_scan for ranked options.\n"
            "3. Route: call rcoder_list_specialists, choose one primary and only the supporting modules with a "
            "distinct responsibility, then call rcoder_validate_selection. Load modules with rcoder_get_specialist "
            "(request only the sections you need).\n"
            "4. Plan only if the change is multi-file, risky, or architectural.\n"
            "5. Implement the smallest correct change, then run the narrowest relevant check first.\n"
            "6. Report outcome, exact commands run with observed results, assumptions, and residual risks. "
            "Label evidence VERIFIED, INFERRED, or NOT VERIFIED."
        )
    elif name == "rcoder_review":
        target = str(arguments.get("target", "the current change")).strip() or "the current change"
        text = (
            f"Review {target} adversarially. Load the review-refactor and verification specialists "
            "(rcoder_get_specialist) and add the narrow domain specialist the change touches.\n\n"
            "Check behavior preservation, edge cases, failure paths, security, accessibility, compatibility, and "
            "test adequacy. Inspect the final diff and untracked or generated files. Report findings by severity "
            "with file and line evidence, mark each VERIFIED, INFERRED, or NOT VERIFIED, and list checks that "
            "could not run."
        )
    elif name == "rcoder_handoff":
        goal = str(arguments.get("goal", "")).strip()
        if not goal:
            raise ValueError("argument 'goal' is required")
        template = read_resource("rcoder://template/context-capsule-template") or ""
        text = (
            f"Write a context capsule for this objective: {goal}\n\n"
            "Fill the template below from observed facts only. Keep exact verification evidence, hard "
            "constraints, and unresolved risks; separate decisions from unknowns.\n\n" + template
        )
    elif name == "rcoder_security_scope":
        target = str(arguments.get("target", "")).strip()
        if not target:
            raise ValueError("argument 'target' is required")
        text = (
            f"Before any security activity on {target}, establish and record: (1) who authorized it and "
            "in writing; (2) in-scope and out-of-scope assets; (3) permitted methods and prohibited actions; "
            "(4) rate limits, time windows, and stop conditions; (5) data-handling rules. If any item is "
            "unknown, stay passive: source and configuration review plus local fixtures only, with no active "
            "scanning, exploitation, credential testing, or external probing. Load the security specialist "
            "first and keep it alongside the narrow technical module."
        )
    else:
        raise KeyError(name)
    return {"description": PROMPTS[name]["description"],
            "messages": [{"role": "user", "content": {"type": "text", "text": text}}]}


# ----------------------------------------------------------------------- protocol

class RpcError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


def handle(method: str, params: dict):
    if method == "initialize":
        requested = params.get("protocolVersion")
        State.protocol = requested if requested in PROTOCOLS else PROTOCOLS[0]
        return {
            "protocolVersion": State.protocol,
            "capabilities": {"tools": {"listChanged": False}, "resources": {"listChanged": False},
                             "prompts": {"listChanged": False}},
            "serverInfo": {"name": SERVER_NAME, "title": "RCoder", "version": product_version()},
            "instructions": ("Read-only RCoder helpers. Call rcoder_scan at session start, route with "
                             "rcoder_list_specialists and rcoder_validate_selection, and load only the "
                             "specialist sections you need."),
        }
    if method == "ping":
        return {}
    if method == "tools/list":
        tools = []
        for name, title, description, input_schema, _ in visible_tools():
            tool = {"name": name, "description": description, "inputSchema": input_schema,
                    "annotations": {"readOnlyHint": True, "destructiveHint": False,
                                    "idempotentHint": True, "openWorldHint": False}}
            if State.protocol >= "2025-06-18":
                tool["title"] = title
            tools.append(tool)
        return {"tools": tools}
    if method == "tools/call":
        name = params.get("name")
        if not isinstance(name, str):
            raise RpcError(-32602, "tools/call requires a tool name")
        try:
            return call_tool(name, params.get("arguments"))
        except KeyError:
            raise RpcError(-32602, f"unknown tool: {name}")
    if method == "resources/list":
        return {"resources": resource_index()}
    if method == "resources/templates/list":
        return {"resourceTemplates": [
            {"uriTemplate": "rcoder://specialist/{name}", "name": "specialist", "mimeType": "text/markdown"},
            {"uriTemplate": "rcoder://template/{name}", "name": "template", "mimeType": "text/markdown"}]}
    if method == "resources/read":
        uri = params.get("uri")
        text = read_resource(uri) if isinstance(uri, str) else None
        if text is None:
            raise RpcError(-32002, f"resource not found: {uri}")
        return {"contents": [{"uri": uri, "mimeType": "text/markdown", "text": clip(text)}]}
    if method == "prompts/list":
        return {"prompts": [{"name": key, **value} for key, value in PROMPTS.items()]}
    if method == "prompts/get":
        name = params.get("name")
        try:
            return build_prompt(name, params.get("arguments") or {})
        except KeyError:
            raise RpcError(-32602, f"unknown prompt: {name}")
        except ValueError as error:
            raise RpcError(-32602, str(error))
    raise RpcError(-32601, f"method not found: {method}")


def respond(message: dict) -> None:
    sys.stdout.write(json.dumps(message, ensure_ascii=False, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def process_line(line: str) -> None:
    try:
        request = json.loads(line)
    except ValueError:
        respond({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "parse error"}})
        return
    if not isinstance(request, dict) or request.get("jsonrpc") != "2.0" or \
            not isinstance(request.get("method"), str):
        respond({"jsonrpc": "2.0", "id": request.get("id") if isinstance(request, dict) else None,
                 "error": {"code": -32600, "message": "invalid request"}})
        return
    request_id = request.get("id")
    is_notification = "id" not in request
    params = request.get("params")
    if params is None:
        params = {}
    if not isinstance(params, dict):
        if not is_notification:
            respond({"jsonrpc": "2.0", "id": request_id,
                     "error": {"code": -32602, "message": "params must be an object"}})
        return
    try:
        result = handle(request["method"], params)
    except RpcError as error:
        if not is_notification:
            respond({"jsonrpc": "2.0", "id": request_id,
                     "error": {"code": error.code, "message": error.message}})
        return
    except Exception as error:  # noqa: BLE001 - last-resort protocol guard
        sys.stderr.write(f"rcoder-mcp internal error: {error!r}\n")
        if not is_notification:
            respond({"jsonrpc": "2.0", "id": request_id,
                     "error": {"code": -32603, "message": "internal error"}})
        return
    if is_notification or request["method"].startswith("notifications/"):
        return
    respond({"jsonrpc": "2.0", "id": request_id, "result": result})


def serve() -> int:
    for stream in (sys.stdin, sys.stdout):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    sys.stdout.reconfigure(newline="\n")
    for line in sys.stdin:
        line = line.strip()
        if line:
            process_line(line)
    return 0


def render_config(host: str, command: str) -> str:
    script = str(Path(__file__).resolve())
    arguments = [script, "--root", "."]
    standard = {"mcpServers": {SERVER_NAME: {"command": command, "args": arguments}}}
    if host == "claude-code":
        quoted = " ".join([command, f'"{script}"', "--root", "."])
        return f"claude mcp add {SERVER_NAME} --scope project -- {quoted}"
    if host == "codex":
        joined = ", ".join(json.dumps(item) for item in arguments)
        return f"[mcp_servers.{SERVER_NAME}]\ncommand = {json.dumps(command)}\nargs = [{joined}]"
    if host in ("cursor", "gemini-cli", "generic"):
        return json.dumps(standard, indent=2)
    if host == "vscode":
        return json.dumps({"servers": {SERVER_NAME: {"type": "stdio", "command": command,
                                                       "args": arguments}}}, indent=2)
    if host == "opencode":
        return json.dumps({"$schema": "https://opencode.ai/config.json",
                           "mcp": {SERVER_NAME: {"type": "local", "command": [command, *arguments],
                                                 "enabled": True}}}, indent=2)
    raise SystemExit(f"unknown host: {host}")


CONFIG_HOSTS = ("claude-code", "codex", "cursor", "gemini-cli", "vscode", "opencode", "generic")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="RCoder read-only stdio MCP server. Speaks JSON-RPC on stdin/stdout.")
    parser.add_argument("--root", default=".", help="project root that path arguments are confined to")
    parser.add_argument("--profile", choices=("full", "minimal"), default="full",
                        help="tool set to expose (minimal: scan, list/get specialist, validate selection)")
    parser.add_argument("--tools", help="comma-separated tool allowlist (overrides --profile)")
    parser.add_argument("--print-config", choices=CONFIG_HOSTS, metavar="HOST",
                        help="print a host configuration snippet and exit: " + ", ".join(CONFIG_HOSTS))
    parser.add_argument("--command", default="python" if sys.platform == "win32" else "python3",
                        help="interpreter command used by --print-config")
    parser.add_argument("--version", action="version", version=f"rcoder-mcp {product_version()}")
    args = parser.parse_args(argv)
    if args.print_config:
        print(render_config(args.print_config, args.command))
        return 0
    root = Path(args.root).expanduser()
    if not root.is_dir():
        parser.error(f"--root is not a directory: {args.root}")
    State.root = root.resolve()
    if args.tools:
        requested = {item.strip() for item in args.tools.split(",") if item.strip()}
        unknown = requested - set(TOOL_INDEX)
        if unknown:
            parser.error("unknown tool(s): " + ", ".join(sorted(unknown)))
        State.enabled = requested
    elif args.profile == "minimal":
        State.enabled = set(PROFILES["minimal"])
    return serve()


if __name__ == "__main__":
    raise SystemExit(main())
