#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
INSTALLER="$ROOT/scripts/install.sh"
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
      codex|agents|zed|openclaw|amp) root=.agents;;
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
    sh "$INSTALLER" --target "$target" --scope "$scope" --project-dir "$project" --home-dir "$home" >/dev/null
    test -f "$dest/SKILL.md"
    test -f "$discovery/.rcoder-backups/rcoder"/install-*/original.txt
    sh "$INSTALLER" --target "$target" --scope "$scope" --project-dir "$project" --home-dir "$home" >/dev/null
    test "$(find "$discovery/.rcoder-backups/rcoder" -maxdepth 1 -type d -name 'install-*' | wc -l | tr -d ' ')" = 1
    sh "$INSTALLER" --target "$target" --scope "$scope" --project-dir "$project" --home-dir "$home" --uninstall >/dev/null
    test -f "$dest/original.txt"
    test ! -f "$dest/SKILL.md"
    echo "PASS $target / $scope"
  done
done
echo 'PASS all 40 POSIX target/scope combinations'
