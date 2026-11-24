#!/usr/bin/env python3
"""Build a compact, token-budgeted repository structural map for coding agents.

Deterministic, standard library only (tree-sitter optional via subprocess if installed).
Outputs a ranked map of public symbols, imports, and entry points designed to fit
in a small context window. No function bodies, no source dumping.

Algorithm: discover -> parse -> link -> rank -> budget -> render
- Discover: git-tracked files, respect .gitignore
- Parse: extract classes, functions, methods, imports per file (tree-sitter if available, regex fallback)
- Link: build file-to-file edges from resolved imports
- Rank: PageRank over import graph + entry-point + export signals
- Budget: pack top-ranked files until token budget exhausted
- Render: compact format with symbols, signatures, import edges, dependents

Usage:
  python3 repo_map.py [--root DIR] [--budget TOKENS] [--max-files N] [--json] [--format FORMAT]
  Formats: compact (names only), default (signatures), detail (full signatures + fields)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import defaultdict, deque
from pathlib import Path

# ---------------------------------------------------------------------------- constants

MAX_FILES_DEFAULT = 200
BUDGET_DEFAULT = 2048
IGNORE_DIRS = {
    ".git", ".hg", ".svn", "node_modules", "vendor", "dist", "build",
    "target", ".venv", "venv", "__pycache__", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", ".next", ".nuxt", ".turbo",
    "coverage", "DerivedData", ".gradle", ".idea", ".vscode",
    ".atlas", ".sinter", "out", "bin", "obj", ".svelte-kit",
}
IGNORE_FILES = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "Cargo.lock",
    "go.sum", "composer.lock", "poetry.lock", "Pipfile.lock",
    "uv.lock", "requirements.txt", "mix.lock",
}
LANGUAGE_EXTENSIONS = {
    ".py": "python",
    ".js": "javascript", ".jsx": "javascript", ".mjs": "javascript", ".cjs": "javascript",
    ".ts": "typescript", ".tsx": "typescript",
    ".rs": "rust",
    ".go": "go",
    ".java": "java",
    ".cpp": "cpp", ".cc": "cpp", ".cxx": "cpp", ".hpp": "cpp", ".h": "cpp", ".c": "cpp",
    ".cs": "csharp",
    ".php": "php",
    ".rb": "ruby",
    ".swift": "swift",
    ".kt": "kotlin", ".kts": "kotlin",
    ".scala": "scala",
    ".zig": "zig",
}
ENTRY_POINT_PATTERNS = [
    r"^main\.py$", r"^__main__\.py$", r"^cli\.py$", r"^app\.py$", r"^run\.py$",
    r"^main\.js$", r"^index\.js$", r"^server\.js$", r"^app\.js$",
    r"^main\.ts$", r"^index\.ts$", r"^server\.ts$", r"^app\.ts$",
    r"^main\.go$", r"^cmd/.*/main\.go$",
    r"^main\.rs$", r"^src/main\.rs$", r"^src/bin/.*\.rs$",
    r"^Main\.java$", r"^Application\.java$",
    r"^Program\.cs$", r"^Program\.fs$",
    r"^main\.cpp$", r"^main\.c$",
    r"^main\.php$", r"^index\.php$",
    r"^main\.rb$", r"^app\.rb$",
]
BOUNDARY_IMPORT_PATTERNS = [
    r"\b(?:import|require|from|use|using)\s+[^;]*\b(?:http|sql|database|db|redis|kafka|grpc|protobuf|thrift|aws|gcp|azure|k8s|kubernetes|docker|shell|subprocess|os\.system|exec|spawn|child_process)\b",
    r"\b(?:SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP|TRUNCATE)\b",
]

# ---------------------------------------------------------------------------- data classes

class Symbol:
    __slots__ = ("name", "kind", "signature", "file", "line", "is_exported", "doc")
    def __init__(self, name: str, kind: str, signature: str, file: str, line: int, is_exported: bool, doc: str = ""):
        self.name = name
        self.kind = kind          # class, function, method, interface, struct, type, const, var
        self.signature = signature
        self.file = file
        self.line = line
        self.is_exported = is_exported
        self.doc = doc

class FileInfo:
    __slots__ = ("path", "language", "symbols", "imports", "resolved_imports", "loc", "hash")
    def __init__(self, path: str, language: str):
        self.path = path
        self.language = language
        self.symbols: list[Symbol] = []
        self.imports: list[str] = []     # raw import strings
        self.resolved_imports: list[str] = []  # target file paths
        self.loc = 0
        self.hash = ""

# ---------------------------------------------------------------------------- tree-sitter integration (optional)

TREE_SITTER_LANGS = {"python", "javascript", "typescript", "go", "rust", "cpp", "java", "csharp", "php", "ruby"}

def have_tree_sitter() -> bool:
    try:
        subprocess.run(["tree-sitter", "--version"], capture_output=True, check=False, timeout=2)
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False

def run_tree_sitter(path: Path, lang: str) -> tuple[list[Symbol], list[str]] | None:
    """Run tree-sitter CLI to extract symbols and imports. Returns None if unavailable."""
    if lang not in TREE_SITTER_LANGS:
        return None
    try:
        # tree-sitter parse <file> --json (requires tree-sitter-cli with queries)
        # Fallback: try a Python binding if available, else return None
        import importlib.util
        if importlib.util.find_spec("tree_sitter"):
            import tree_sitter
            import tree_sitter_languages
            parser = tree_sitter.Parser()
            parser.set_language(tree_sitter.Language(tree_sitter_languages.get_language(lang)))
            text = path.read_bytes()
            tree = parser.parse(text)
            # Simplified extraction - real impl would use language-specific queries
            return extract_with_python_binding(tree, text, lang, str(path))
    except Exception:
        pass
    return None

def extract_with_python_binding(tree, text: bytes, lang: str, filepath: str) -> tuple[list[Symbol], list[str]]:
    """Extract symbols using Python tree-sitter bindings. Simplified."""
    symbols = []
    imports = []
    # Language-agnostic simple query
    query_code = {
        "python": """
        (function_definition name: (identifier) @name) @func
        (class_definition name: (identifier) @name) @class
        (import_statement) @import
        (import_from_statement) @import
        """,
        "javascript": """
        (function_declaration name: (identifier) @name) @func
        (method_definition name: (property_identifier) @name) @method
        (class_declaration name: (identifier) @name) @class
        (import_statement) @import
        """,
        "typescript": """
        (function_declaration name: (identifier) @name) @func
        (method_definition name: (property_identifier) @name) @method
        (class_declaration name: (identifier) @name) @class
        (interface_declaration name: (type_identifier) @name) @interface
        (import_statement) @import
        """,
        "go": """
        (function_declaration name: (identifier) @name) @func
        (method_declaration name: (field_identifier) @name) @method
        (type_declaration (type_spec name: (type_identifier) @name)) @type
        (import_declaration) @import
        """,
        "rust": """
        (function_item name: (identifier) @name) @func
        (struct_item name: (type_identifier) @name) @struct
        (enum_item name: (type_identifier) @name) @enum
        (trait_item name: (type_identifier) @name) @trait
        (impl_item) @impl
        (use_declaration) @import
        """,
    }
    lang_query = query_code.get(lang)
    if not lang_query:
        return [], []
    try:
        from tree_sitter import Query
        query = Query(tree_sitter.Language(tree_sitter_languages.get_language(lang)), lang_query)
        captures = query.captures(tree.root_node)
        for node, name in captures:
            if name in ("func", "method", "class", "interface", "struct", "enum", "trait", "type"):
                snippet = text[node.start_byte:node.end_byte].decode("utf-8", errors="replace")
                line = node.start_point[0] + 1
                signature = snippet.split("\n")[0][:120]
                sym = Symbol(
                    name=node.text.decode("utf-8", errors="replace") if name == "name" else "unknown",
                    kind=name,
                    signature=signature,
                    file=filepath,
                    line=line,
                    is_exported=True,  # simplified
                    doc=""
                )
                symbols.append(sym)
            elif name == "import":
                imports.append(text[node.start_byte:node.end_byte].decode("utf-8", errors="replace").strip())
    except Exception:
        pass
    return symbols, imports

# ---------------------------------------------------------------------------- regex fallback parsers

PYTHON_FUNC = re.compile(r"^\s*(?:async\s+)?def\s+([a-zA-Z_]\w*)\s*\(([^)]*)\)\s*(?:->\s*[^:]+)?:")
PYTHON_CLASS = re.compile(r"^\s*class\s+([a-zA-Z_]\w*)\s*(?:\([^)]*\))?:")
PYTHON_IMPORT = re.compile(r"^\s*(?:from\s+([\w.]+)\s+)?import\s+([\w.,\s*]+)")

JS_FUNC = re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+([a-zA-Z_$]\w*)\s*\(([^)]*)\)")
JS_CLASS = re.compile(r"^\s*(?:export\s+)?class\s+([a-zA-Z_$]\w*)")
JS_ARROW = re.compile(r"^\s*(?:export\s+)?(?:const|let|var)\s+([a-zA-Z_$]\w*)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>")
JS_IMPORT = re.compile(r"^\s*import\s+(?:.*?\s+from\s+)?['\"]([^'\"]+)['\"]")
TS_INTERFACE = re.compile(r"^\s*(?:export\s+)?interface\s+([a-zA-Z_$]\w*)")

GO_FUNC = re.compile(r"^\s*func\s+(?:\([^)]*\)\s+)?([a-zA-Z_]\w*)\s*\(([^)]*)\)")
GO_STRUCT = re.compile(r"^\s*type\s+([a-zA-Z_]\w*)\s+struct\s*{")
GO_IMPORT = re.compile(r"^\s*import\s+(?:\(\s*)?['\"]([^'\"]+)['\"]")

RUST_FUNC = re.compile(r"^\s*(?:pub\s+)?(?:async\s+)?fn\s+([a-zA-Z_]\w*)\s*\(([^)]*)\)")
RUST_STRUCT = re.compile(r"^\s*(?:pub\s+)?struct\s+([a-zA-Z_]\w*)")
RUST_IMPORT = re.compile(r"^\s*use\s+([\w:]+)")

def parse_python(text: str, filepath: str) -> tuple[list[Symbol], list[str]]:
    symbols, imports = [], []
    lines = text.splitlines()
    for i, line in enumerate(lines):
        m = PYTHON_FUNC.match(line)
        if m:
            name, params = m.groups()
            symbols.append(Symbol(name, "function", f"def {name}({params})", filepath, i+1, not name.startswith("_")))
            continue
        m = PYTHON_CLASS.match(line)
        if m:
            symbols.append(Symbol(m.group(1), "class", f"class {m.group(1)}", filepath, i+1, not m.group(1).startswith("_")))
            continue
        m = PYTHON_IMPORT.match(line)
        if m:
            mod, names = m.groups()
            if mod: imports.append(mod)
            for n in names.replace("*", "").split(","):
                n = n.strip().split(" as ")[0].strip()
                if n and n != "*": imports.append(n)
    return symbols, imports

def parse_javascript(text: str, filepath: str) -> tuple[list[Symbol], list[str]]:
    symbols, imports = [], []
    lines = text.splitlines()
    for i, line in enumerate(lines):
        m = JS_FUNC.match(line)
        if m:
            name, params = m.groups()
            symbols.append(Symbol(name, "function", f"function {name}({params})", filepath, i+1, True))
            continue
        m = JS_CLASS.match(line)
        if m:
            symbols.append(Symbol(m.group(1), "class", f"class {m.group(1)}", filepath, i+1, True))
            continue
        m = JS_ARROW.match(line)
        if m:
            symbols.append(Symbol(m.group(1), "function", f"const {m.group(1)} = (...) => ...", filepath, i+1, True))
            continue
        m = JS_IMPORT.match(line)
        if m:
            imports.append(m.group(1))
    return symbols, imports

def parse_typescript(text: str, filepath: str) -> tuple[list[Symbol], list[str]]:
    symbols, imports = [], []
    lines = text.splitlines()
    for i, line in enumerate(lines):
        m = JS_FUNC.match(line)
        if m:
            name, params = m.groups()
            symbols.append(Symbol(name, "function", f"function {name}({params})", filepath, i+1, True))
            continue
        m = JS_CLASS.match(line)
        if m:
            symbols.append(Symbol(m.group(1), "class", f"class {m.group(1)}", filepath, i+1, True))
            continue
        m = TS_INTERFACE.match(line)
        if m:
            symbols.append(Symbol(m.group(1), "interface", f"interface {m.group(1)}", filepath, i+1, True))
            continue
        m = JS_IMPORT.match(line)
        if m:
            imports.append(m.group(1))
    return symbols, imports

def parse_go(text: str, filepath: str) -> tuple[list[Symbol], list[str]]:
    symbols, imports = [], []
    lines = text.splitlines()
    for i, line in enumerate(lines):
        m = GO_FUNC.match(line)
        if m:
            name, params = m.groups()
            symbols.append(Symbol(name, "function", f"func {name}({params})", filepath, i+1, name[0].isupper()))
            continue
        m = GO_STRUCT.match(line)
        if m:
            symbols.append(Symbol(m.group(1), "struct", f"type {m.group(1)} struct", filepath, i+1, m.group(1)[0].isupper()))
            continue
        m = GO_IMPORT.match(line)
        if m:
            imports.append(m.group(1))
    return symbols, imports

def parse_rust(text: str, filepath: str) -> tuple[list[Symbol], list[str]]:
    symbols, imports = [], []
    lines = text.splitlines()
    for i, line in enumerate(lines):
        m = RUST_FUNC.match(line)
        if m:
            name, params = m.groups()
            symbols.append(Symbol(name, "function", f"fn {name}({params})", filepath, i+1, line.strip().startswith("pub")))
            continue
        m = RUST_STRUCT.match(line)
        if m:
            symbols.append(Symbol(m.group(1), "struct", f"struct {m.group(1)}", filepath, i+1, line.strip().startswith("pub")))
            continue
        m = RUST_IMPORT.match(line)
        if m:
            imports.append(m.group(1))
    return symbols, imports

PARSERS = {
    "python": parse_python,
    "javascript": parse_javascript,
    "typescript": parse_typescript,
    "go": parse_go,
    "rust": parse_rust,
}

# ---------------------------------------------------------------------------- graph + ranking

def build_import_graph(files: list[FileInfo]) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    """Return (out_edges, in_edges) where edges are file paths."""
    path_to_idx = {f.path: i for i, f in enumerate(files)}
    out_edges = defaultdict(set)
    in_edges = defaultdict(set)
    for f in files:
        for imp in f.imports:
            # Try to resolve import to a file in the repo
            target = resolve_import(imp, f.path, path_to_idx, files)
            if target and target != f.path:
                out_edges[f.path].add(target)
                in_edges[target].add(f.path)
    return out_edges, in_edges

def resolve_import(imp: str, from_file: str, path_to_idx: dict[str, int], files: list[FileInfo]) -> str | None:
    """Best-effort import resolution to a repo file."""
    imp = imp.strip().strip('"').strip("'")
    if imp.startswith("."):
        base_dir = Path(from_file).parent
        target = base_dir / imp
        stem = target.stem
        # Match by resolved path, by parent+stem, or by repo-wide stem fallback
        for f in files:
            if Path(f.path).parent == base_dir and Path(f.path).stem == stem:
                return f.path
        for f in files:
            if Path(f.path).stem == stem:
                return f.path
        return None
    # Absolute/module import: match by stem or suffix
    for f in files:
        stem = Path(f.path).stem
        if imp == stem or imp.endswith(stem):
            return f.path
    return None

def pagerank(out_edges: dict[str, set[str]], in_edges: dict[str, set[str]], damping: float = 0.85, iterations: int = 20) -> dict[str, float]:
    # Iterate nodes in sorted order so results are deterministic across Python hash seeds.
    nodes = sorted(set(out_edges) | set(in_edges))
    if not nodes:
        return {}
    n = len(nodes)
    rank = {node: 1.0 / n for node in nodes}
    for _ in range(iterations):
        new_rank = {}
        for node in nodes:
            s = (1 - damping) / n
            for m in sorted(in_edges.get(node, [])):
                out_deg = len(out_edges.get(m, [])) or 1
                s += damping * rank[m] / out_deg
            new_rank[node] = s
        rank = new_rank
    return rank

def compute_scores(files: list[FileInfo], ranks: dict[str, float], root: Path,
                   in_edges: dict[str, set[str]]) -> dict[str, float]:
    scores = {}
    for f in files:
        s = ranks.get(f.path, 0.0)
        # Entry point boost
        rel = f.path
        for pat in ENTRY_POINT_PATTERNS:
            if re.search(pat, rel):
                s += 50
                break
        # Exported symbol count
        exported = sum(1 for sym in f.symbols if sym.is_exported)
        s += exported * 2
        # Direct importers (fan-in)
        s += len(in_edges.get(f.path, [])) * 1.5
        # Boundary imports boost
        for imp in f.imports:
            for pat in BOUNDARY_IMPORT_PATTERNS:
                if re.search(pat, imp, re.I):
                    s += 10
                    break
        # Deep path penalty
        depth = len(Path(f.path).parts)
        s -= depth * 0.5
        scores[f.path] = max(0.0, s)
    return scores

# ---------------------------------------------------------------------------- rendering

def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)

MAX_SYMBOLS_PER_FILE_DEFAULT = 8

def _file_block(f: FileInfo, score: float, fmt: str, limit: int) -> list[str]:
    lines = [f"{f.path} [score {score:.0f}]"]
    shown = 0
    if fmt == "compact":
        for sym in f.symbols:
            if not sym.is_exported:
                continue
            lines.append(f"  {sym.kind}: {sym.name}")
            shown += 1
            if shown >= limit:
                break
        if not f.symbols and f.imports:
            lines.append(f"  imports: {', '.join(f.imports[:3])}")
    elif fmt == "detail":
        for sym in f.symbols:
            lines.append(f"  {sym.kind}: {sym.name} {sym.signature}")
            shown += 1
            if shown >= limit:
                break
        if f.imports:
            lines.append(f"  imports: {', '.join(f.imports[:5])}")
    else:  # default: exported first, then non-exported if room
        for sym in f.symbols:
            if not sym.is_exported:
                continue
            lines.append(f"  {sym.kind}: {sym.name} {sym.signature}")
            shown += 1
            if shown >= limit:
                break
        if shown < limit:
            for sym in f.symbols:
                if sym.is_exported:
                    continue
                lines.append(f"  {sym.kind}: {sym.name} {sym.signature}")
                shown += 1
                if shown >= limit:
                    break
        if f.resolved_imports:
            lines.append(f"  imports: {', '.join([Path(p).name for p in f.resolved_imports[:3]])}")
        elif f.imports and not f.symbols:
            lines.append(f"  imports: {', '.join(f.imports[:3])}")
    return lines

def render_map(files: list[FileInfo], scores: dict[str, float], budget: int, fmt: str = "default") -> tuple[str, int]:
    sorted_files = sorted(files, key=lambda f: (-scores.get(f.path, 0.0), f.path))
    out_lines = []
    used = 0
    for f in sorted_files:
        if f.path not in scores or (not f.symbols and not f.imports):
            continue
        score = scores[f.path]
        limit = 2 if fmt == "compact" else MAX_SYMBOLS_PER_FILE_DEFAULT
        block_lines = _file_block(f, score, fmt, limit)
        block = "\n".join(block_lines) + "\n"
        if used + estimate_tokens(block) > budget:
            break
        out_lines.append(block)
        used += estimate_tokens(block)
    return "\n".join(out_lines), used

# ---------------------------------------------------------------------------- main pipeline

def _is_source(name: str) -> bool:
    return Path(name).suffix.lower() in LANGUAGE_EXTENSIONS and Path(name).name not in IGNORE_FILES

def discover_files(root: Path) -> list[Path]:
    """Return source files only (supported language extensions), honoring .gitignore."""
    candidates: list[Path] = []
    try:
        result = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
            cwd=root, capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            candidates = [root / line for line in result.stdout.splitlines()
                          if line.strip() and _is_source(line)]
    except Exception:
        candidates = []
    if not candidates:
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS and not d.startswith(".")]
            for fname in filenames:
                if _is_source(fname):
                    candidates.append(Path(dirpath) / fname)
    # Skip anything inside an ignored directory even if git-tracked listings sneak it in.
    return [p for p in candidates if not (set(p.relative_to(root).parts) & IGNORE_DIRS)]

def process_file(path: Path, root: Path, use_ts: bool) -> FileInfo | None:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None
    rel = path.relative_to(root).as_posix()
    lang = LANGUAGE_EXTENSIONS.get(path.suffix.lower(), "")
    if not lang:
        return None
    f = FileInfo(rel, lang)
    f.loc = len(text.splitlines())
    f.hash = hashlib.sha256(text.encode()).hexdigest()[:16]
    # Parse
    parser = PARSERS.get(lang)
    if parser:
        symbols, imports = parser(text, rel)
        f.symbols = symbols
        f.imports = imports
    # tree-sitter attempt
    if use_ts and lang in TREE_SITTER_LANGS:
        ts_result = run_tree_sitter(path, lang)
        if ts_result:
            ts_symbols, ts_imports = ts_result
            if ts_symbols:
                f.symbols = ts_symbols
            if ts_imports:
                f.imports = list(dict.fromkeys(f.imports + ts_imports))
    return f

def main() -> int:
    parser = argparse.ArgumentParser(description="Build a compact repository structural map")
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument("--budget", type=int, default=BUDGET_DEFAULT, help="Token budget for output")
    parser.add_argument("--max-files", type=int, default=MAX_FILES_DEFAULT, help="Max files to process")
    parser.add_argument("--json", action="store_true", help="Machine-readable JSON output")
    parser.add_argument("--format", choices=["compact", "default", "detail"], default="default")
    parser.add_argument("--no-tree-sitter", action="store_true", help="Disable tree-sitter even if available")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    use_ts = not args.no_tree_sitter and have_tree_sitter()

    # Discover
    all_paths = discover_files(root)
    all_paths = all_paths[:args.max_files]

    # Process
    files = []
    for p in all_paths:
        finfo = process_file(p, root, use_ts)
        if finfo:
            files.append(finfo)

    # Graph + rank
    out_edges, in_edges = build_import_graph(files)
    ranks = pagerank(out_edges, in_edges)
    for f in files:
        f.resolved_imports = sorted(out_edges.get(f.path, []))
    scores = compute_scores(files, ranks, root, in_edges)

    # Render
    map_text, used = render_map(files, scores, args.budget, args.format)

    if args.json:
        payload = {
            "root": str(root),
            "budget": args.budget,
            "used_tokens": used,
            "files_processed": len(files),
            "map": map_text,
        }
        print(json.dumps(payload))
    else:
        print(map_text)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())