#!/usr/bin/env python3
"""Zero-dependency semantic dependency graph, hotspot, and risk analyzer for RScan.

The analyzer is read-only and deliberately conservative: it parses Python with the
standard-library ``ast`` module, uses bounded heuristics for JavaScript/TypeScript,
Go, and Rust, resolves only repository-local edges, and never executes project code.
Results are deterministic for the same tree so agents and tests can compare runs.
"""
from __future__ import annotations

import ast
import math
import os
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

SKIP_DIRS = {
    ".git", ".hg", ".svn", "node_modules", "__pycache__", ".venv", "venv",
    "dist", "build", "target", ".next", ".nuxt", ".pytest_cache", ".mypy_cache",
    ".turbo", "coverage", "DerivedData", ".gradle", ".idea", ".cache", ".worktrees",
}
CODE_SUFFIXES = {".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".go", ".rs"}
MAX_FILES = 6000

JS_IMPORT_RE = re.compile(
    r"""(?:\bimport\s+(?:[^'"]*?\sfrom\s+)?|\bexport\s+[^'"]*?\sfrom\s+|\brequire\s*\(\s*)['"]([^'"]+)['"]"""
)
GO_IMPORT_RE = re.compile(r"""^\s*(?:[\w.]+\s+)?["']([^"']+)["']""", re.MULTILINE)
RUST_USE_RE = re.compile(r"""^\s*(?:pub\s+)?(?:use|mod)\s+([a-zA-Z0-9_:]+)""", re.MULTILINE)

SECRET_FILENAME_RE = re.compile(
    r"(^|/)\.env(\.|$)|credentials|secret|id_rsa|\.pem$|\.p12$|\.pfx$|\.key$", re.I
)
SECRET_TEMPLATE_SUFFIXES = (".example", ".sample", ".template", ".dist", ".defaults")
LOCKFILE_PAIRS = [
    ("package.json", ("package-lock.json", "yarn.lock", "pnpm-lock.yaml", "bun.lockb")),
    ("pyproject.toml", ("poetry.lock", "uv.lock", "pdm.lock")),
    ("requirements.txt", ("requirements.lock", "uv.lock", "poetry.lock")),
    ("Cargo.toml", ("Cargo.lock",)),
    ("go.mod", ("go.sum",)),
]
ENTRY_NAMES = {
    "main.py", "__main__.py", "app.py", "server.py", "manage.py", "wsgi.py", "asgi.py",
    "index.ts", "index.tsx", "index.js", "index.jsx", "main.ts", "main.js",
    "main.go", "main.rs", "lib.rs",
}
TEST_PATH_RE = re.compile(
    r"(^|/)(?:tests?|__tests__|spec)/|(?:^|/)(?:test|spec)[^/]*$|"
    r"_test\.go$|\.(?:test|spec)\.[cm]?[jt]sx?$|_spec\.rb$",
    re.I,
)

_BRANCH_TYPES = tuple(
    getattr(ast, name)
    for name in (
        "If", "For", "AsyncFor", "While", "ExceptHandler", "With", "AsyncWith",
        "BoolOp", "IfExp", "Match",
    )
    if hasattr(ast, name)
)


def _python_metrics(source: str) -> tuple[list[str], int, int]:
    """Return (imports, complexity_score, symbol_count) using stdlib ast."""
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError, RecursionError):
        return [], 1, 0

    imports: list[str] = []
    complexity = 1
    symbols = 0

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append("." * node.level + node.module)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            symbols += 1
        elif _BRANCH_TYPES and isinstance(node, _BRANCH_TYPES):
            complexity += 1

    return imports, complexity, symbols


def _heuristic_metrics(ext: str, source: str) -> tuple[list[str], int, int]:
    """Return (imports, complexity_score, symbol_count) for JS/TS, Go, and Rust."""
    imports: list[str] = []
    if ext in {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}:
        imports = JS_IMPORT_RE.findall(source)
        symbols = len(re.findall(r"\b(?:function|class|interface|type|enum)\s+\w+", source))
    elif ext == ".go":
        imports = GO_IMPORT_RE.findall(source)
        symbols = len(
            re.findall(r"\bfunc\s+(?:\([^)]+\)\s+)?\w+|\btype\s+\w+\s+(?:struct|interface)", source)
        )
    elif ext == ".rs":
        imports = [match.replace("::", "/") for match in RUST_USE_RE.findall(source)]
        symbols = len(re.findall(r"\b(?:pub\s+)?(?:async\s+)?(?:fn|struct|enum|trait)\s+\w+", source))
    else:
        symbols = 0

    branches = len(
        re.findall(r"\b(?:if|else\s+if|for|while|match|switch|case|catch)\b|&&|\|\|", source)
    )
    return imports, 1 + branches, symbols


def _probe_candidates(base: Path, known_files: set[str], source_rel: str) -> str | None:
    """Probe common source extensions for a resolved base path."""
    probes = [base.as_posix()]
    for suffix in (".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".go", ".rs"):
        probes.append((base.parent / (base.name + suffix)).as_posix())
    probes.extend(
        [
            (base / "__init__.py").as_posix(),
            (base / "index.ts").as_posix(),
            (base / "index.tsx").as_posix(),
            (base / "index.js").as_posix(),
            (base / "index.jsx").as_posix(),
            (base / "mod.rs").as_posix(),
        ]
    )
    for probe in probes:
        normalized = os.path.normpath(probe).replace("\\", "/").lstrip("./")
        if normalized in known_files and normalized != source_rel:
            return normalized
    return None


def _resolve_local_edge(src_rel: str, raw_import: str, known_files: set[str]) -> str | None:
    """Resolve relative or repository-local module specifiers to a tracked file path."""
    if not raw_import or raw_import.startswith(("http://", "https://", "data:", "node:")):
        return None
    source = Path(src_rel)
    src_dir = source.parent
    suffix = source.suffix.lower()

    if raw_import.startswith("."):
        if suffix == ".py":
            dots = len(raw_import) - len(raw_import.lstrip("."))
            module = raw_import[dots:]
            base = src_dir
            for _ in range(max(0, dots - 1)):
                base = base.parent
            if module:
                base = base.joinpath(*module.split("."))
            return _probe_candidates(base, known_files, src_rel)

        dots = len(raw_import) - len(raw_import.lstrip("."))
        tail = raw_import[dots:].lstrip("/")
        base = src_dir
        for _ in range(max(0, dots - 1)):
            base = base.parent
        if tail:
            base = base / tail
        return _probe_candidates(base, known_files, src_rel)

    # Bare Python module path, e.g. ``pkg.mod`` imported as ``pkg.mod``.
    if suffix == ".py" and "/" not in raw_import:
        dotted = Path(*raw_import.split("."))
        direct = _probe_candidates(dotted, known_files, src_rel)
        if direct:
            return direct
        return _probe_candidates(src_dir / dotted, known_files, src_rel)

    # Repository-relative path such as ``src/util`` used by JS or Go.
    normalized = os.path.normpath(raw_import).replace("\\", "/").lstrip("./")
    if normalized and normalized in known_files and normalized != src_rel:
        return normalized
    if normalized:
        direct = _probe_candidates(Path(normalized), known_files, src_rel)
        if direct:
            return direct
    return None


def find_cycles(adj: dict[str, list[str]]) -> list[list[str]]:
    """Tarjan's strongly connected components algorithm to detect circular dependencies."""
    index = 0
    indices: dict[str, int] = {}
    lowlink: dict[str, int] = {}
    stack: list[str] = []
    on_stack: set[str] = set()
    cycles: list[list[str]] = []

    def strongconnect(node: str) -> None:
        nonlocal index
        indices[node] = index
        lowlink[node] = index
        index += 1
        stack.append(node)
        on_stack.add(node)

        for nxt in adj.get(node, ()):
            if nxt not in indices:
                strongconnect(nxt)
                lowlink[node] = min(lowlink[node], lowlink[nxt])
            elif nxt in on_stack:
                lowlink[node] = min(lowlink[node], indices[nxt])

        if lowlink[node] == indices[node]:
            component: list[str] = []
            while True:
                member = stack.pop()
                on_stack.remove(member)
                component.append(member)
                if member == node:
                    break
            if len(component) > 1:
                cycles.append(sorted(component))

    for vertex in sorted(adj):
        if vertex not in indices:
            strongconnect(vertex)
    for vertex in sorted(adj):
        if vertex in adj.get(vertex, ()):
            cycles.append([vertex])
    return sorted(cycles)


def _walk_files(root: Path) -> list[str]:
    files: list[str] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(
            name for name in dirnames if name not in SKIP_DIRS and not name.startswith(".")
        )
        for filename in sorted(filenames):
            full = Path(dirpath) / filename
            try:
                if full.is_symlink():
                    continue
            except OSError:
                continue
            try:
                files.append(full.relative_to(root).as_posix())
            except ValueError:
                continue
            if len(files) >= MAX_FILES:
                return files
    return files


def _has_matching_test(file_path: str, test_files: list[str]) -> bool:
    stem = Path(file_path).stem.lower()
    if not stem:
        return False
    for test_file in test_files:
        test_stem = Path(test_file).stem.lower()
        if stem in test_stem or test_stem in {f"test_{stem}", f"{stem}_test", f"{stem}.test", f"{stem}.spec"}:
            return True
    return False


def analyze_repository_graph(
    root: Path,
    token_budget: int | None = None,
    max_file_bytes: int = 256_000,
) -> dict[str, Any]:
    """Build a semantic dependency graph, hotspots, risks, and a budgeted slice."""
    root = root.resolve()
    rel_files = _walk_files(root)
    known_set = set(rel_files)
    raw_imports: dict[str, list[str]] = {}
    metrics: dict[str, dict[str, int]] = {}

    for rel in rel_files:
        full = root / rel
        suffix = full.suffix.lower()
        if suffix not in CODE_SUFFIXES:
            continue
        try:
            if full.stat().st_size > max_file_bytes:
                continue
            source = full.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        if suffix == ".py":
            imports, complexity, symbols = _python_metrics(source)
        else:
            imports, complexity, symbols = _heuristic_metrics(suffix, source)

        raw_imports[rel] = imports
        metrics[rel] = {"lines": source.count("\n") + 1, "complexity": complexity, "symbols": symbols}

    adjacency: dict[str, list[str]] = defaultdict(list)
    in_degree: dict[str, int] = defaultdict(int)
    for source_file, imports in raw_imports.items():
        seen_targets: set[str] = set()
        for raw_import in imports:
            target = _resolve_local_edge(source_file, raw_import, known_set)
            if target and target not in seen_targets:
                seen_targets.add(target)
                adjacency[source_file].append(target)
                in_degree[target] += 1

    cycles = find_cycles(adjacency)
    entry_points = sorted(
        file_path
        for file_path in metrics
        if in_degree[file_path] == 0
        and (
            Path(file_path).name in ENTRY_NAMES
            or file_path.startswith(("bin/", "cmd/", "cli/"))
        )
    )

    hotspots: list[dict[str, Any]] = []
    for file_path, metric in metrics.items():
        fan_in = in_degree[file_path]
        fan_out = len(adjacency.get(file_path, ()))
        score = round(
            metric["complexity"] * (1.0 + math.log1p(fan_in)) + fan_out * 1.5, 2
        )
        hotspots.append(
            {
                "file": file_path,
                "hotspot_score": score,
                "complexity": metric["complexity"],
                "fan_in": fan_in,
                "fan_out": fan_out,
                "lines": metric["lines"],
            }
        )
    hotspots.sort(key=lambda item: (-item["hotspot_score"], item["file"]))

    test_files = [item for item in rel_files if TEST_PATH_RE.search(item)]
    risks: list[dict[str, Any]] = []
    for hotspot in hotspots[:8]:
        if hotspot["hotspot_score"] >= 10.0 and not _has_matching_test(hotspot["file"], test_files):
            risks.append(
                {
                    "severity": "high",
                    "code": "UNTESTED_HOTSPOT",
                    "file": hotspot["file"],
                    "detail": (
                        f"High-centrality file (score={hotspot['hotspot_score']}) lacks a matching test file."
                    ),
                    "recommended_reference": "references/test-engineering.md",
                }
            )

    for cycle in cycles:
        risks.append(
            {
                "severity": "medium",
                "code": "CIRCULAR_DEPENDENCY",
                "files": cycle,
                "detail": f"Strongly connected import cycle across {len(cycle)} module(s).",
                "recommended_reference": "references/architecture.md",
            }
        )

    for rel in rel_files:
        if Path(rel).suffix.lower() in {".md", ".txt", ".rst", ".adoc", ".html"}:
            continue
        if SECRET_FILENAME_RE.search(rel) and not rel.endswith(SECRET_TEMPLATE_SUFFIXES):
            risks.append(
                {
                    "severity": "high",
                    "code": "SENSITIVE_CONFIG_PATH",
                    "file": rel,
                    "detail": "Potential secret or credential artifact tracked in the workspace tree.",
                    "recommended_reference": "references/identity-crypto-secrets.md",
                }
            )

    for manifest, lockfiles in LOCKFILE_PAIRS:
        if manifest in known_set and not any(lock in known_set for lock in lockfiles):
            risks.append(
                {
                    "severity": "medium",
                    "code": "MISSING_LOCKFILE",
                    "file": manifest,
                    "detail": (
                        f"{manifest} is present without a deterministic lockfile "
                        f"({', '.join(lockfiles)})."
                    ),
                    "recommended_reference": "references/supply-chain-security.md",
                }
            )

    file_count = len(rel_files)
    if token_budget is None:
        token_budget = 1600 if file_count > 500 else (2800 if file_count > 120 else 4500)
    token_budget = max(400, min(int(token_budget), 16000))
    if token_budget <= 1800:
        budget_mode = "compact"
    elif token_budget <= 3200:
        budget_mode = "standard"
    else:
        budget_mode = "deep"
    hotspot_cap = {"compact": 5, "standard": 12, "deep": 25}[budget_mode]
    risk_cap = {"compact": 6, "standard": 15, "deep": 30}[budget_mode]

    return {
        "budget_mode": budget_mode,
        "token_budget": token_budget,
        "summary": {
            "total_files": file_count,
            "analyzed_code_files": len(metrics),
            "dependency_edges": sum(len(targets) for targets in adjacency.values()),
            "circular_dependency_groups": len(cycles),
            "entry_points": entry_points[:10],
        },
        "adjacency": {key: list(value) for key, value in sorted(adjacency.items())},
        "hotspots": hotspots[:hotspot_cap],
        "cycles": cycles[:5],
        "risks": risks[:risk_cap],
    }
