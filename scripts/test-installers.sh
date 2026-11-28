#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
INSTALLER="$ROOT/install.sh"
export RCODER_RUNTIME_DISABLE=1
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT HUP INT TERM
for target in claude-code codex cursor gemini-cli copilot agents qoder opencode antigravity amp zed pi openclaw autohand warp kilocode cline roo-code trae factory; do
  for scope in project user; do
    project="$TMP/project-$target-$scope"
    home="$TMP/home-$target-$scope"
    mkdir -p "$project" "$home"
    base=$project
    [ "$scope" = user ] && base=$home
    case "$target" in
      claude-code) root=.claude;;
      codex|agents|zed|openclaw) root=.agents;;
      amp) [ "$scope" = user ] && root=.config/agents || root=.agents;;
      cursor) root=.cursor;;
      gemini-cli) root=.gemini;;
      copilot) [ "$scope" = user ] && root=.copilot || root=.github;;
      qoder) root=.qoder;;
      opencode) [ "$scope" = user ] && root=.config/opencode || root=.opencode;;
      antigravity) [ "$scope" = user ] && root=.gemini/config || root=.agents;;
      pi) [ "$scope" = user ] && root=.pi/agent || root=.pi;;
      autohand) root=.autohand;;
      warp) root=.warp;;
      kilocode) root=.kilo;;
      cline) root=.cline;;
      roo-code) root=.roo;;
      trae) root=.trae;;
      factory) root=.factory;;
      *) echo "Test target missing mapping: $target" >&2; exit 1;;
    esac
    discovery="$base/$root"
    dest="$discovery/skills/rcoder"
    mkdir -p "$dest"
    echo old > "$dest/original.txt"
    sh "$INSTALLER" --target "$target" --scope "$scope" --project-dir "$project" --home-dir "$home" --dry-run >/dev/null
    test -f "$dest/original.txt"
    test ! -f "$dest/SKILL.md"
    sh "$INSTALLER" --target "$target" --scope "$scope" --project-dir "$project" --home-dir "$home" --yes >/dev/null
    test -f "$dest/SKILL.md"
    test -f "$discovery/.rcoder-backups/rcoder"/install-*/original.txt
    sh "$INSTALLER" --target "$target" --scope "$scope" --project-dir "$project" --home-dir "$home" --yes >/dev/null
    test "$(find "$discovery/.rcoder-backups/rcoder" -maxdepth 1 -type d -name 'install-*' | wc -l | tr -d ' ')" = 1
    sh "$INSTALLER" --target "$target" --scope "$scope" --project-dir "$project" --home-dir "$home" --uninstall >/dev/null
    test -f "$dest/original.txt"
    test ! -f "$dest/SKILL.md"
    echo "PASS $target / $scope"
  done
done
echo 'PASS all 40 POSIX target/scope combinations'
sh "$INSTALLER" --list-features | grep -q 'RSaver:'
sh "$INSTALLER" --list-features | grep -q 'RScan:'
sh "$INSTALLER" --help | grep -q -- '--doctor'
sh "$INSTALLER" --help | grep -q -- '--host'
ALIAS_PROJECT="$TMP/alias-project"
ALIAS_HOME="$TMP/alias-home"
mkdir -p "$ALIAS_PROJECT" "$ALIAS_HOME"
sh "$INSTALLER" --host claude --scope project --project-dir "$ALIAS_PROJECT" --home-dir "$ALIAS_HOME" --dry-run >/dev/null
if sh "$INSTALLER" --host all --scope project --project-dir "$ALIAS_PROJECT" >/dev/null 2>&1; then
  echo 'invalid --host all value was accepted' >&2
  exit 1
fi
sh "$INSTALLER" --doctor >/dev/null
echo 'PASS root POSIX entrypoint, compatibility flags, and doctor dispatch'

FEATURE_PROJECT="$TMP/feature-project"
FEATURE_HOME="$TMP/feature-home"
mkdir -p "$FEATURE_PROJECT" "$FEATURE_HOME"
sh "$INSTALLER" --target agents --scope project --project-dir "$FEATURE_PROJECT" --home-dir "$FEATURE_HOME" --features rsaver >/dev/null
FEATURE_MANIFEST="$FEATURE_PROJECT/.agents/.rcoder-features.json"
test -f "$FEATURE_MANIFEST"
grep -q '"rsaver": true' "$FEATURE_MANIFEST"
grep -q '"rscan": false' "$FEATURE_MANIFEST"
python3 - "$FEATURE_MANIFEST" <<'PY'
import json, sys
with open(sys.argv[1], encoding="utf-8") as handle:
    json.load(handle)
PY
sh "$INSTALLER" --target agents --scope project --project-dir "$FEATURE_PROJECT" --home-dir "$FEATURE_HOME" --features rscan >/dev/null
grep -q '"rsaver": false' "$FEATURE_MANIFEST"
grep -q '"rscan": true' "$FEATURE_MANIFEST"
test -f "$FEATURE_PROJECT/.rcoder/context-fabric.sqlite3"
CLEAN_OUT=$(sh "$INSTALLER" --target agents --scope project --project-dir "$FEATURE_PROJECT" --home-dir "$FEATURE_HOME" --features rscan --clean 2>&1)
printf '%s\n' "$CLEAN_OUT" | grep -q 'Clean install:'
printf '%s\n' "$CLEAN_OUT" | grep -q 'Install target:'
grep -q '"rscan": true' "$FEATURE_MANIFEST"
echo 'PASS POSIX optional tools, RFC store, and clean reinstall of an already-current install'

if command -v python3 >/dev/null 2>&1 || command -v python >/dev/null 2>&1; then
  MCP_PROJECT="$TMP/mcp-project"
  MCP_HOME="$TMP/mcp-home"
  mkdir -p "$MCP_PROJECT" "$MCP_HOME"
  sh "$INSTALLER" --target cursor --scope project --project-dir "$MCP_PROJECT" --home-dir "$MCP_HOME" --mcp install >/dev/null
  grep -q '"rcoder"' "$MCP_PROJECT/.cursor/mcp.json"
  if sh "$INSTALLER" --mcp bogus 2>/dev/null; then
    echo 'invalid --mcp value was accepted' >&2
    exit 1
  fi
  echo 'PASS POSIX MCP auto-setup'
fi
