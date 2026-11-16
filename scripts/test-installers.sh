#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd); INSTALLER="$ROOT/scripts/install.sh"; TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT HUP INT TERM
for target in claude-code codex cursor gemini-cli copilot agents; do for scope in project user; do
 project="$TMP/project-$target-$scope"; home="$TMP/home-$target-$scope"; mkdir -p "$project" "$home"; base=$project; [ "$scope" = user ] && base=$home
 case "$target:$scope" in claude-code:*) r="$base/.claude";; codex:*|agents:*) r="$base/.agents";; cursor:*) r="$base/.cursor";; gemini-cli:*) r="$base/.gemini";; copilot:project) r="$base/.github";; copilot:user) r="$base/.copilot";; esac
 dest="$r/skills/rcoder"; mkdir -p "$dest"; echo old > "$dest/original.txt"
 "$INSTALLER" --target "$target" --scope "$scope" --project-dir "$project" --home-dir "$home" --dry-run >/dev/null
 test -f "$dest/original.txt"; test ! -f "$dest/SKILL.md"
 "$INSTALLER" --target "$target" --scope "$scope" --project-dir "$project" --home-dir "$home" >/dev/null
 test -f "$dest/SKILL.md"; test -f "$r/.rcoder-backups/$target"/install-*/original.txt
 "$INSTALLER" --target "$target" --scope "$scope" --project-dir "$project" --home-dir "$home" >/dev/null
 test "$(find "$r/.rcoder-backups/$target" -maxdepth 1 -type d -name 'install-*' | wc -l | tr -d ' ')" = 1
 "$INSTALLER" --target "$target" --scope "$scope" --project-dir "$project" --home-dir "$home" --uninstall >/dev/null
 test -f "$dest/original.txt"; test ! -f "$dest/SKILL.md"; echo "PASS $target / $scope"
done; done
echo 'PASS all 12 POSIX target/scope combinations'
