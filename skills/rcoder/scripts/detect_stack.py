#!/usr/bin/env python3
"""Read-only repository stack detector using Python standard library only."""
import argparse, json, os
from pathlib import Path

MAP = {
    'Cargo.toml':'Rust / Cargo','go.mod':'Go','package.json':'JavaScript / TypeScript (Node.js)',
    'pnpm-workspace.yaml':'JavaScript monorepo (pnpm)','pyproject.toml':'Python',
    'requirements.txt':'Python','Pipfile':'Python (Pipenv)','poetry.lock':'Python (Poetry)',
    'uv.lock':'Python (uv)','composer.json':'PHP / Composer','Gemfile':'Ruby / Bundler',
    'pom.xml':'Java / Maven','build.gradle':'JVM / Gradle','build.gradle.kts':'JVM / Kotlin / Gradle',
    'Package.swift':'Swift','Podfile':'Apple platforms','pubspec.yaml':'Dart / Flutter',
    'mix.exs':'Elixir','CMakeLists.txt':'C / C++ / CMake','meson.build':'C / C++ / Meson',
    'Makefile':'Make build','Dockerfile':'Docker','compose.yaml':'Docker Compose',
    'docker-compose.yml':'Docker Compose','Chart.yaml':'Helm','terraform.tf':'Terraform',
}
QUALITY = ['AGENTS.md','CLAUDE.md','CONTRIBUTING.md','Makefile','justfile','Taskfile.yml','.editorconfig','.pre-commit-config.yaml','.github/workflows','.gitlab-ci.yml','azure-pipelines.yml']
IGNORE = {'.git','.hg','.svn','node_modules','vendor','.venv','venv','target','dist','build','out','__pycache__'}
def detect(root, depth_limit):
    manifests, stacks = set(), set()
    for current, dirs, names in os.walk(str(root)):
        current_path = Path(current)
        depth = len(current_path.relative_to(root).parts)
        dirs[:] = sorted(d for d in dirs if d not in IGNORE and not d.startswith('.') and depth < depth_limit)
        for name in names:
            if name in MAP:
                manifests.add((current_path / name).relative_to(root).as_posix()); stacks.add(MAP[name])
            elif name.endswith('.csproj') or name.endswith('.sln'):
                manifests.add((current_path / name).relative_to(root).as_posix()); stacks.add('.NET')
            elif name.endswith('.tf'):
                manifests.add((current_path / name).relative_to(root).as_posix()); stacks.add('Terraform')
            elif name.endswith('.ipynb'):
                manifests.add((current_path / name).relative_to(root).as_posix()); stacks.add('Jupyter / data science')
    entry_points = [item for item in QUALITY if (root / item).exists()]
    return {'root':str(root.resolve()),'manifests':sorted(manifests),'candidate_stacks':sorted(stacks),'quality_entry_points':entry_points,
            'notes':['Read-only heuristic; verify actual commands and versions before running them.','Hidden and common generated/vendor directories are skipped.']}
def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('path',nargs='?',default='.'); p.add_argument('--max-depth',type=int,default=5); p.add_argument('--json',action='store_true'); a=p.parse_args()
    root=Path(a.path).expanduser().resolve()
    if not root.is_dir() or a.max_depth < 1: p.error('path must be a directory and --max-depth must be positive')
    result=detect(root,a.max_depth)
    if a.json: print(json.dumps(result,indent=2))
    else:
        print('Repository:',result['root']); print('Candidate stacks:')
        for x in result['candidate_stacks']: print('  -',x)
        print('Manifests:')
        for x in result['manifests']: print('  -',x)
        print('Quality entry points:')
        for x in result['quality_entry_points']: print('  -',x)
        for x in result['notes']: print('Note:',x)
    return 0
if __name__=='__main__': raise SystemExit(main())
