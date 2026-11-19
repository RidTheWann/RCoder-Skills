#!/usr/bin/env python3
"""RScan: bounded, read-only project scan with prioritized development options.

RScan never edits the scanned project. Hook installation is a separate explicit
command that merges a session-start hook into supported host settings files.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

VERSION = "1.10.0"
SKIP = {
    ".git", ".hg", ".svn", "node_modules", "vendor", "dist", "build", "target",
    ".venv", "venv", "__pycache__", ".pytest_cache", ".mypy_cache", ".next",
    ".nuxt", ".turbo", "coverage", "DerivedData", ".gradle", ".idea", ".cache",
}
STACK_MARKERS = {
    "package.json": "Node.js / JavaScript / TypeScript",
    "tsconfig.json": "TypeScript",
    "Cargo.toml": "Rust",
    "go.mod": "Go",
    "pyproject.toml": "Python",
    "requirements.txt": "Python",
    "pom.xml": "Java / Maven",
    "build.gradle": "JVM / Gradle",
    "CMakeLists.txt": "C / C++ / CMake",
    "Package.swift": "Swift",
    "pubspec.yaml": "Dart / Flutter",
    "composer.json": "PHP",
    "Gemfile": "Ruby",
    "mix.exs": "Elixir",
    "Makefile": "Make builds",
    "Dockerfile": "Containers",
    "terraform.tf": "Terraform",
}
LOCKFILES = {"package-lock.json", "yarn.lock", "pnpm-lock.yaml", "Cargo.lock",
             "go.sum", "poetry.lock", "uv.lock", "Pipfile.lock", "composer.lock", "Gemfile.lock"}
KEY_FILES = {"AGENTS.md", "CLAUDE.md", "README.md", "CONTRIBUTING.md", "LICENSE",
             "CHANGELOG.md", "package.json", "pyproject.toml", "Cargo.toml", "go.mod"}
BINARY_SUFFIXES = {".so", ".dll", ".dylib", ".exe", ".o", ".a", ".wasm", ".bin", ".pyc"}
SECURITY_MARKERS = ("auth", "crypto", "secret", "token", "login", "permission", "session")


def git_summary(root: Path) -> dict:
    def run(*args: str) -> str:
        try:
            result = subprocess.run(["git", *args], cwd=root, text=True,
                                    capture_output=True, timeout=3, check=False)
            return result.stdout.strip() if result.returncode == 0 else ""
        except (OSError, subprocess.TimeoutExpired):
            return ""
    branch = run("branch", "--show-current")
    status = run("status", "--short")
    commits = [line for line in run("log", "--oneline", "-5").splitlines() if line]
    return {
        "is_repository": bool(branch or run("rev-parse", "--is-inside-work-tree")),
        "branch": branch or "detached-or-unavailable",
        "changed_files": [line[3:] for line in status.splitlines() if len(line) > 3][:80],
        "recent_commits": commits,
    }


def collect_paths(root: Path, max_paths: int) -> tuple[list[str], bool]:
    paths: list[str] = []
    truncated = False
    stack = [(root, 0)]
    while stack:
        folder, depth = stack.pop()
        try:
            entries = sorted(os.scandir(folder), key=lambda entry: entry.name.lower())
        except OSError:
            continue
        children: list[Path] = []
        for entry in entries:
            if entry.is_symlink():
                continue
            relative = Path(entry.path).relative_to(root).as_posix()
            if entry.is_dir(follow_symlinks=False):
                if entry.name not in SKIP and depth < 4:
                    children.append(Path(entry.path))
            elif entry.is_file(follow_symlinks=False):
                paths.append(relative)
                if len(paths) >= max_paths:
                    truncated = True
                    return sorted(paths), truncated
        for child in reversed(children):
            stack.append((child, depth + 1))
    return sorted(paths), truncated


def build_options(root: Path, paths: list[str], stacks: list[str], key_files: list[str],
                  quality: dict, risks: list[dict], git: dict) -> list[dict]:
    options = []

    def add(identifier: str, title: str, why: str, commands: list[str],
            specialists: list[str], score: int, risk_ids: list[str]) -> None:
        options.append({"id": identifier, "title": title, "why": why,
                        "first_commands": commands, "specialists": specialists,
                        "priority": score, "triggered_by": risk_ids})

    signals = {item["id"] for item in risks}
    if "no_readme" in signals or "no_agent_instructions" in signals or "unfamiliar_repository" in signals:
        add("ONBOARD", "Build a bounded repository map and onboard",
            "Entry points or agent instructions are missing/not evidenced.",
            ["python3 skills/rcoder/scripts/context_snapshot.py . --max-paths 80",
             "python3 skills/rcoder/scripts/rsaver.py measure README.md"],
            ["token-efficiency", "documentation", "verification"], 70,
            sorted(signals & {"no_readme", "no_agent_instructions", "unfamiliar_repository"}))
    if "no_ci" in signals or "no_test_entry_point" in signals:
        add("QUALITY_GATES", "Add minimal tests and CI gates",
            "No CI workflow or test entry point was detected.",
            ["python3 scripts/validate-all", "python3 scripts/test-context-snapshot.py"],
            ["testing-qa", "devops-ci-cd"], 85,
            sorted(signals & {"no_ci", "no_test_entry_point"}))
    if "dependency_without_lock" in signals:
        add("DEPENDENCY_SECURITY", "Review dependency provenance and lockfiles",
            "A package manifest exists without a detected lockfile.",
            ["python3 skills/rcoder/scripts/detect_stack.py . --json"],
            ["supply-chain-security", "build-toolchain-engineering"], 80,
            ["dependency_without_lock"])
    if git["changed_files"]:
        add("FINISH_CHANGE", "Finish and verify the in-progress change",
            "The working tree already contains uncommitted changes.",
            ["git status --short", "git diff --stat", "python3 scripts/validate-all"],
            ["coding", "review-refactor", "verification"], 90, ["uncommitted_changes"])
    if "no_readme" in signals or "docs_stale" in signals:
        add("DOCUMENTATION", "Refresh onboarding documentation",
            "Documentation is missing or does not match observed commands.",
            ["python3 skills/rcoder/scripts/context_snapshot.py . --json"],
            ["documentation"], 55, sorted(signals & {"no_readme", "docs_stale"}))
    if any(marker in " ".join(paths).lower() for marker in SECURITY_MARKERS):
        add("SECURITY_REVIEW", "Map trust boundaries and review security-sensitive paths",
            "Paths suggest authentication, tokens, or permission handling.",
            ["python3 skills/rcoder/scripts/context_snapshot.py . --max-paths 80"],
            ["security", "threat-modeling", "secure-code-review"], 75, ["security_surface"])
    if "large_source_files" in signals:
        add("REFACTOR", "Decompose oversized modules behind stable contracts",
            "At least one file exceeds 300 lines in the bounded sample.",
            ["python3 skills/rcoder/scripts/context_snapshot.py . --max-paths 120"],
            ["review-refactor", "architecture"], 50, ["large_source_files"])
    if "binary_artifacts" in signals:
        add("REVERSE_ENGINEERING", "Analyze binary artifacts with evidence provenance",
            "Binary artifacts were found in the bounded sample.",
            ["python3 skills/rcoder/scripts/rsaver.py measure <artifact>"],
            ["reverse-engineering", "reverse-engineering-file-formats"], 60,
            ["binary_artifacts"])
    if "benchmark_markers" in signals:
        add("PERFORMANCE", "Profile measured bottlenecks before optimizing",
            "Benchmark or profiling entry points were detected.",
            ["python3 skills/rcoder/scripts/context_snapshot.py . --max-paths 80"],
            ["performance", "test-engineering"], 45, ["benchmark_markers"])
    if not git["changed_files"] and "no_ci" not in signals and quality["ci"]:
        add("RELEASE", "Prepare a release with reproducible packages",
            "Clean tree, CI, and build metadata are present.",
            ["python3 scripts/package", "npm pack --dry-run --json"],
            ["devops-ci-cd", "documentation"], 40, [])
    return sorted(options, key=lambda item: (-item["priority"], item["id"]))


def scan_project(root: Path, max_paths: int) -> dict:
    git = git_summary(root)
    paths, truncated = collect_paths(root, max_paths)
    by_name = {Path(path).name: path for path in paths}
    stacks = sorted({label for name, label in STACK_MARKERS.items() if name in by_name})
    key_files = sorted(name for name in KEY_FILES if name in by_name)
    has_lock = any(name in by_name for name in LOCKFILES)
    ci = any(path.startswith(".github/workflows/") or "/.github/workflows/" in path
             or path.endswith(".gitlab-ci.yml") for path in paths)
    tests = any("test" in Path(path).name.lower() or "tests/" in path.lower() for path in paths)
    large = []
    for path in paths:
        if Path(path).suffix in {".py", ".js", ".ts", ".go", ".rs", ".java", ".md"}:
            try:
                if len((root / path).read_text(encoding="utf-8", errors="replace").splitlines()) > 300:
                    large.append(path)
            except OSError:
                continue
    binaries = [path for path in paths if Path(path).suffix.lower() in BINARY_SUFFIXES]
    benchmarks = [path for path in paths if "bench" in Path(path).name.lower()
                  or "profil" in Path(path).name.lower()]

    risks = []
    if not by_name.get("README.md"):
        risks.append({"id": "no_readme", "severity": "medium", "detail": "README.md not found in sample"})
    if not (by_name.get("AGENTS.md") or by_name.get("CLAUDE.md")):
        risks.append({"id": "no_agent_instructions", "severity": "low",
                      "detail": "No AGENTS.md or CLAUDE.md in sample"})
    if not git["is_repository"]:
        risks.append({"id": "not_a_git_repository", "severity": "medium", "detail": "Git metadata unavailable"})
    if git["changed_files"]:
        risks.append({"id": "uncommitted_changes", "severity": "low",
                      "detail": f"{len(git['changed_files'])} changed file(s)"})
    if not ci:
        risks.append({"id": "no_ci", "severity": "high", "detail": "No CI workflow detected in sample"})
    if not tests:
        risks.append({"id": "no_test_entry_point", "severity": "high", "detail": "No test file detected in sample"})
    if any(name in by_name for name in STACK_MARKERS if name != "Makefile") and not has_lock:
        risks.append({"id": "dependency_without_lock", "severity": "medium",
                      "detail": "Manifest without a detected lockfile"})
    if large:
        risks.append({"id": "large_source_files", "severity": "low",
                      "detail": f"{len(large)} file(s) over 300 lines (sample: {large[:5]})"})
    if binaries:
        risks.append({"id": "binary_artifacts", "severity": "medium",
                      "detail": f"{len(binaries)} binary artifact(s) (sample: {binaries[:5]})"})
    if benchmarks:
        risks.append({"id": "benchmark_markers", "severity": "low",
                      "detail": f"benchmark/profiling paths: {benchmarks[:5]}"})
    risks.append({"id": "unfamiliar_repository", "severity": "info",
                  "detail": "First scan in this session; treat findings as bounded evidence"})

    quality = {"ci": ci, "tests": tests, "agent_instructions": bool(by_name.get("AGENTS.md") or by_name.get("CLAUDE.md")),
               "readme": bool(by_name.get("README.md")), "lockfile": has_lock}
    options = build_options(root, paths, stacks, key_files, quality, risks, git)
    return {
        "tool": "RScan", "version": VERSION,
        "root": str(root.resolve()), "git": git,
        "scan": {"max_paths": max_paths, "paths_sampled": len(paths),
                 "truncated": truncated, "source_contents_read_for_line_counts_only": True},
        "stacks": stacks, "key_files": key_files, "quality": quality,
        "risk_signals": risks, "development_options": options[:6],
        "limits": ["Heuristic detection; verify commands and versions in project files.",
                   "No files are modified by scan.",
                   "Binary and non-text contents are not inspected."],
    }


def render_menu(report: dict) -> str:
    lines = [f"RScan: {report['root']}", f"Branch: {report['git']['branch']}",
             f"Stacks: {', '.join(report['stacks']) or 'undetected'}",
             f"Sampled paths: {report['scan']['paths_sampled']} (truncated={report['scan']['truncated']})",
             f"Risk signals: {len(report['risk_signals'])}", "", "Development options:"]
    for index, option in enumerate(report["development_options"], 1):
        lines.append(f"  {index}. [{option['id']}] {option['title']} (priority {option['priority']})")
        lines.append(f"     why: {option['why']}")
        lines.append(f"     first: {option['first_commands'][0]}")
    lines.append("")
    lines.append("Ask the agent to choose an option ID; RScan does not modify the project.")
    return "\n".join(lines)


def render_markdown(report: dict) -> str:
    lines = [f"# RScan report — {report['root']}", "",
             f"- Branch: `{report['git']['branch']}`",
             f"- Stacks: {', '.join(report['stacks']) or 'undetected'}",
             f"- Sampled paths: {report['scan']['paths_sampled']}",
             "", "## Risk signals", ""]
    for risk in report["risk_signals"]:
        lines.append(f"- **{risk['severity']}** `{risk['id']}`: {risk['detail']}")
    lines.extend(["", "## Development options", ""])
    for option in report["development_options"]:
        lines.append(f"### {option['id']} — {option['title']}")
        lines.append(f"Priority: {option['priority']}. Why: {option['why']}")
        for command in option["first_commands"]:
            lines.append(f"- `{command}`")
        lines.append(f"- Specialists: {', '.join(option['specialists'])}")
        lines.append("")
    return "\n".join(lines)


def hook_payload(report: dict, host: str) -> str:
    if host == "claude":
        payload = {"hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": render_menu(report),
            "sessionTitle": "RScan " + Path(report["root"]).name,
        }}
    elif host == "gemini":
        payload = {"systemMessage": f"RScan found {len(report['development_options'])} development options.",
                   "hookSpecificOutput": {"additionalContext": render_menu(report)}}
    elif host == "opencode":
        return render_menu(report)
    else:
        raise ValueError(f"unsupported hook host: {host}")
    return json.dumps(payload, ensure_ascii=True)


def command_scan(args: argparse.Namespace) -> int:
    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"root is not a directory: {root}")
    report = scan_project(root, args.max_paths)
    if args.hook:
        print(hook_payload(report, args.hook))
    elif args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    elif args.format == "markdown":
        print(render_markdown(report))
    else:
        print(render_menu(report))
    return 0


HOST_SETTINGS = {
    "claude-code": {".claude/settings.json": "startup", "~/.claude/settings.json": "startup"},
    "gemini-cli": {".gemini/settings.json": "startup", "~/.gemini/settings.json": "startup"},
}
HOOK_EVENT = {"claude-code": "SessionStart", "gemini-cli": "SessionStart"}


def hook_command(host: str) -> str:
    script = Path(__file__).resolve()
    payload_host = "claude" if host == "claude-code" else "gemini"
    return f'"{sys.executable}" "{script}" scan --root . --hook {payload_host}'


def build_hook_config(host: str, settings: dict) -> dict:
    event = HOOK_EVENT[host]
    hooks = dict(settings.get("hooks", {}))
    entries = list(hooks.get(event, []))
    command = hook_command(host)
    for entry in entries:
        for handler in entry.get("hooks", []):
            if "rscan.py" in handler.get("command", "") and "scan" in handler.get("command", ""):
                return settings
    handler = {"type": "command", "command": command, "name": "rscan-session-scan"}
    if host == "claude-code":
        handler["shell"] = "powershell" if os.name == "nt" else "bash"
        entries.append({"matcher": "startup", "hooks": [handler]})
    else:
        entries.append({"matcher": "startup", "hooks": [handler], "timeout": 15000})
    hooks[event] = entries
    updated = dict(settings)
    updated["hooks"] = hooks
    return updated


def opencode_plugin_source(api: str) -> str:
    python = sys.executable
    script = Path(__file__).resolve()
    if api == "v1":
        body = '''
export const RScanPlugin = async ({ $, directory }) => {
  const seen = new Set();
  const python = "__PY__";
  const rscan = "__RS__";
  return {
    "experimental.chat.system.transform": async (input, output) => {
      if (!input.sessionID || seen.has(input.sessionID)) return;
      seen.add(input.sessionID);
      try {
        const text = await $`${python} ${rscan} scan --root ${directory} --hook opencode`.text();
        output.system.push({ type: "text", text });
      } catch (error) {
        console.error("RScan skipped:", error);
      }
    }
  };
};
'''
    else:
        body = '''
import { Plugin } from "@opencode/plugin";
export default Plugin.define({
  id: "rcoder.rscan",
  async setup(ctx) {
    const python = "__PY__";
    const rscan = "__RS__";
    let injected = false;
    await ctx.session.hook("context", async (event) => {
      if (injected) return;
      injected = true;
      const proc = Bun.spawn([python, rscan, "scan", "--root", ctx.location.directory, "--hook", "opencode"], {
        stdout: "pipe", stderr: "pipe"
      });
      const text = await new Response(proc.stdout).text();
      event.system.push({ type: "text", text });
    });
  }
});
'''
    return body.replace("__PY__", python).replace("__RS__", str(script))


def command_hooks(args: argparse.Namespace) -> int:
    if args.action == "adapter":
        if args.host != "opencode":
            raise ValueError("adapter generation is only available for OpenCode")
        root = Path(args.root).expanduser().resolve()
        relative = (".opencode/plugins/rscan.js" if args.scope == "project"
                    else ".config/opencode/plugins/rscan.js")
        target = (root / relative) if args.scope == "project" else (Path.home() / relative)
        source = opencode_plugin_source(args.api)
        if target.is_file() and target.read_text(encoding="utf-8") == source:
            print(f"RScan adapter already current: {target}")
            return 0
        if args.dry_run:
            print(source)
            return 0
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.is_file():
            backup = target.with_name(target.name + f".rscan-backup-{int(time.time())}")
            shutil.copy2(target, backup)
            print(f"RScan adapter backup: {backup}")
        target.write_text(source, encoding="utf-8")
        print(f"RScan OpenCode {args.api} adapter installed: {target}")
        print("RScan adapter: NOT VERIFIED until tested with the exact installed OpenCode CLI", file=sys.stderr)
        return 0
    if args.action == "preview":
        print(json.dumps(build_hook_config(args.host, {}), indent=2, sort_keys=True))
        return 0
    templates = [key for key in HOST_SETTINGS[args.host] if (not key.startswith("~") if args.scope == "project" else key.startswith("~"))]
    if not templates:
        raise ValueError("no settings path for the requested scope")
    relative = templates[0]
    target = (Path.home() / relative[2:]) if relative.startswith("~/") else (Path(args.root).expanduser().resolve() / relative)
    original = target.read_text(encoding="utf-8") if target.is_file() else "{}"
    settings = json.loads(original)
    updated = build_hook_config(args.host, settings)
    if updated == settings:
        print(f"RSaver-hook: already installed in {target}")
        return 0
    if args.dry_run:
        print(json.dumps(updated, indent=2, sort_keys=True))
        print(f"RSaver-hook: dry run; would update {target}", file=sys.stderr)
        return 0
    target.parent.mkdir(parents=True, exist_ok=True)
    backup = target.with_name(target.name + f".rscan-backup-{int(time.time())}")
    shutil.copy2(target, backup)
    temporary = target.with_name(target.name + ".rscan-tmp")
    temporary.write_text(json.dumps(updated, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, target)
    print(f"RScan hook installed: {target}")
    print(f"RScan hook backup: {backup}")
    return 0


def main() -> int:
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", action="version", version=f"RScan {VERSION}")
    sub = parser.add_subparsers(dest="command", required=True)

    scan = sub.add_parser("scan", help="scan the project and offer development options")
    scan.add_argument("--root", default=".")
    scan.add_argument("--max-paths", type=int, default=80)
    scan.add_argument("--format", choices=("text", "json", "markdown"), default="text")
    scan.add_argument("--hook", choices=("claude", "gemini", "opencode"),
                      help="emit a session-start hook payload")
    scan.set_defaults(func=command_scan)

    hooks = sub.add_parser("hooks", help="preview or install session-start hooks")
    hooks.add_argument("action", choices=("preview", "install", "adapter"))
    hooks.add_argument("--host", choices=(*HOST_SETTINGS, "opencode"), default="claude-code")
    hooks.add_argument("--api", choices=("v1", "v2"), default="v1")
    hooks.add_argument("--scope", choices=("project", "user"), default="project")
    hooks.add_argument("--root", default=".")
    hooks.add_argument("--dry-run", action="store_true")
    hooks.set_defaults(func=command_hooks)

    args = parser.parse_args()
    if hasattr(args, "max_paths") and args.max_paths < 10:
        parser.error("--max-paths must be >= 10")
    try:
        return args.func(args)
    except (OSError, ValueError, json.JSONDecodeError, KeyError) as error:
        print(f"RScan ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
