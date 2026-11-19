#!/bin/sh
set -eu
usage(){ echo 'Usage: install.sh [--target ID] [--scope project|user] [--project-dir PATH] [--home-dir PATH] [--features CSV] [--dry-run] [--uninstall] [--list-features]'; }
TARGET=agents; SCOPE=project; PROJECT_DIR=$(pwd); HOME_DIR=${HOME:-}; DRY=0; REMOVE=0; FEATURES=rsaver,rscan
while [ "$#" -gt 0 ]; do case "$1" in
  --target) [ "$#" -ge 2 ] || { usage >&2; exit 2; }; TARGET=$2; shift 2;;
  --scope) [ "$#" -ge 2 ] || { usage >&2; exit 2; }; SCOPE=$2; shift 2;;
  --project-dir) [ "$#" -ge 2 ] || { usage >&2; exit 2; }; PROJECT_DIR=$2; shift 2;;
  --home-dir) [ "$#" -ge 2 ] || { usage >&2; exit 2; }; HOME_DIR=$2; shift 2;;
  --features) [ "$#" -ge 2 ] || { usage >&2; exit 2; }; FEATURES=$2; shift 2;;
  --list-features) echo 'RSaver: Context pruning, budgeting, and re-anchoring for long sessions'; echo 'RScan: Read-only project scan with ranked development options at session start'; exit 0;;
  --dry-run) DRY=1; shift;; --uninstall) REMOVE=1; shift;; -h|--help) usage; exit 0;;
  *) echo "Unknown argument: $1" >&2; usage >&2; exit 2;; esac; done
case "$TARGET" in
  claude-code) PROJECT_ROOT=.claude; USER_ROOT=.claude;; codex|agents|zed|openclaw) PROJECT_ROOT=.agents; USER_ROOT=.agents;;
  cursor) PROJECT_ROOT=.cursor; USER_ROOT=.cursor;; gemini-cli) PROJECT_ROOT=.gemini; USER_ROOT=.gemini;;
  copilot) PROJECT_ROOT=.github; USER_ROOT=.copilot;; qoder) PROJECT_ROOT=.qoder; USER_ROOT=.qoder;;
  opencode) PROJECT_ROOT=.opencode; USER_ROOT=.config/opencode;; antigravity) PROJECT_ROOT=.agents; USER_ROOT=.gemini/config;;
  amp) PROJECT_ROOT=.agents; USER_ROOT=.config/agents;; pi) PROJECT_ROOT=.pi; USER_ROOT=.pi/agent;;
  openclaw) PROJECT_ROOT=.agents; USER_ROOT=.agents;; autohand) PROJECT_ROOT=.autohand; USER_ROOT=.autohand;;
  warp) PROJECT_ROOT=.warp; USER_ROOT=.warp;; kilocode) PROJECT_ROOT=.kilo; USER_ROOT=.kilo;;
  cline) PROJECT_ROOT=.cline; USER_ROOT=.cline;; roo-code) PROJECT_ROOT=.roo; USER_ROOT=.roo;;
  trae) PROJECT_ROOT=.trae; USER_ROOT=.trae;; factory) PROJECT_ROOT=.factory; USER_ROOT=.factory;;
  *) echo "Unsupported target: $TARGET" >&2; exit 2;;
esac
case "$SCOPE" in project) BASE=$PROJECT_DIR; ROOT=$PROJECT_ROOT;; user) [ -n "$HOME_DIR" ] || { echo 'HOME is not set; pass --home-dir' >&2; exit 1; }; BASE=$HOME_DIR; ROOT=$USER_ROOT;; *) echo 'Scope must be project or user' >&2; exit 2;; esac
if [ "$FEATURES" != none ]; then
  OLDIFS=$IFS; IFS=,
  for feature in $FEATURES; do
    case "$feature" in rsaver|rscan) ;; *) echo "Unknown optional tool: $feature" >&2; exit 2;; esac
  done
  IFS=$OLDIFS
fi
[ -d "$BASE" ] || { echo "Selected directory does not exist: $BASE" >&2; exit 1; }
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd); SOURCE="$SCRIPT_DIR/../skills/rcoder"
[ -f "$SOURCE/SKILL.md" ] || { echo "Skill source missing: $SOURCE/SKILL.md" >&2; exit 1; }
TARGET_ROOT="$BASE/$ROOT"; DEST="$TARGET_ROOT/skills/rcoder"; BACKUP="$TARGET_ROOT/.rcoder-backups/rcoder"; LEGACY_BACKUP="$TARGET_ROOT/.rcoder-backups/$TARGET"; STAMP=$(date -u '+%Y%m%dT%H%M%SZ')-$$
check_links(){ base=$1; target=$2; case "$target" in "$base"/*) rel=${target#"$base"/};; *) echo "Refusing path outside selected scope: $target" >&2; exit 1;; esac; current=$base; oldIFS=$IFS; IFS=/; for part in $rel; do current="$current/$part"; [ ! -L "$current" ] || { echo "Refusing symbolic link: $current" >&2; exit 1; }; done; IFS=$oldIFS; }
check_links "$BASE" "$DEST"; check_links "$BASE" "$BACKUP"; check_links "$BASE" "$LEGACY_BACKUP"
if [ "$REMOVE" -eq 1 ]; then
  echo "Uninstall target: $TARGET -> $DEST"
  if [ "$DRY" -eq 1 ]; then echo "DRY RUN: preserve active install and restore latest backup under $BACKUP"; exit 0; fi
  if [ -d "$DEST" ]; then mkdir -p "$BACKUP"; mv "$DEST" "$BACKUP/uninstalled-$STAMP"; else echo 'No active RCoder installation found.'; fi
  RESTORE=''; for candidate in "$BACKUP"/install-*; do [ -d "$candidate" ] && RESTORE=$candidate; done
  if [ -z "$RESTORE" ]; then for candidate in "$LEGACY_BACKUP"/install-*; do [ -d "$candidate" ] && RESTORE=$candidate; done; fi
  if [ -n "$RESTORE" ]; then mkdir -p "$(dirname "$DEST")"; mv "$RESTORE" "$DEST"; echo "Restored previous installation: $DEST"; fi
  rm -f "$TARGET_ROOT/.rcoder-features.json"
  exit 0
fi
if [ -d "$DEST" ] && diff -qr "$SOURCE" "$DEST" >/dev/null 2>&1; then echo "RCoder is already current at $DEST"; exit 0; fi
echo "Install target: $TARGET ($SCOPE) -> $DEST"
if [ "$DRY" -eq 1 ]; then [ ! -d "$DEST" ] || echo "DRY RUN: backup existing folder to $BACKUP/install-$STAMP"; echo "DRY RUN: copy skill bundle to $DEST"; exit 0; fi
mkdir -p "$(dirname "$DEST")" "$BACKUP"; STAGE="$(dirname "$DEST")/.rcoder-stage-$STAMP"; SAVED=''
cleanup(){ [ ! -d "$STAGE" ] || rm -rf "$STAGE"; }; trap cleanup EXIT HUP INT TERM
cp -R "$SOURCE" "$STAGE"
if [ -d "$DEST" ]; then SAVED="$BACKUP/install-$STAMP"; mv "$DEST" "$SAVED"; fi
if ! mv "$STAGE" "$DEST"; then [ -z "$SAVED" ] || mv "$SAVED" "$DEST"; exit 1; fi
trap - EXIT HUP INT TERM
echo "Installed RCoder for $TARGET: $DEST"
FEATURE_MANIFEST="$TARGET_ROOT/.rcoder-features.json"
RSAVER=false; RSCAN=false
case ",$FEATURES," in *,rsaver,*) RSAVER=true;; esac
case ",$FEATURES," in *,rscan,*) RSCAN=true;; esac
VERSION=$(grep -m1 '"version"' "$SCRIPT_DIR/../package.json" | tr -dc '0-9.')
printf '{\n  "schema_version": 1,\n  "version": "%s",\n  "rsaver": %s,\n  "rscan": %s\n}\n' "$VERSION" "$RSAVER" "$RSCAN" > "$FEATURE_MANIFEST"
echo "Enabled optional tools: $FEATURES"
