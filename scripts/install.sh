#!/bin/sh
set -eu
usage(){ echo 'Usage: install.sh [--target claude-code|codex|cursor|gemini-cli|copilot|agents] [--scope project|user] [--project-dir PATH] [--home-dir PATH] [--dry-run] [--uninstall]'; }
TARGET=agents; SCOPE=project; PROJECT_DIR=$(pwd); HOME_DIR=${HOME:-}; DRY=0; REMOVE=0
while [ "$#" -gt 0 ]; do case "$1" in
  --target) [ "$#" -ge 2 ] || { usage >&2; exit 2; }; TARGET=$2; shift 2;;
  --scope) [ "$#" -ge 2 ] || { usage >&2; exit 2; }; SCOPE=$2; shift 2;;
  --project-dir) [ "$#" -ge 2 ] || { usage >&2; exit 2; }; PROJECT_DIR=$2; shift 2;;
  --home-dir) [ "$#" -ge 2 ] || { usage >&2; exit 2; }; HOME_DIR=$2; shift 2;;
  --dry-run) DRY=1; shift;; --uninstall) REMOVE=1; shift;; -h|--help) usage; exit 0;;
  *) echo "Unknown argument: $1" >&2; usage >&2; exit 2;; esac; done
case "$TARGET" in claude-code|codex|cursor|gemini-cli|copilot|agents) ;; *) echo "Unsupported target: $TARGET" >&2; exit 2;; esac
case "$SCOPE" in project) BASE=$PROJECT_DIR;; user) [ -n "$HOME_DIR" ] || { echo 'HOME is not set; pass --home-dir' >&2; exit 1; }; BASE=$HOME_DIR;; *) echo 'Scope must be project or user' >&2; exit 2;; esac
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd); SOURCE="$SCRIPT_DIR/../skills/rcoder"
[ -f "$SOURCE/SKILL.md" ] || { echo "Skill source not found: $SOURCE/SKILL.md" >&2; exit 1; }
case "$TARGET" in claude-code) ROOT="$BASE/.claude";; codex|agents) ROOT="$BASE/.agents";; cursor) ROOT="$BASE/.cursor";; gemini-cli) ROOT="$BASE/.gemini";; copilot) if [ "$SCOPE" = user ]; then ROOT="$BASE/.copilot"; else ROOT="$BASE/.github"; fi;; esac
DEST="$ROOT/skills/rcoder"; BACKUP="$ROOT/.rcoder-backups/$TARGET"; STAMP=$(date -u '+%Y%m%dT%H%M%SZ')-$$
if [ "$REMOVE" -eq 1 ]; then
  echo "Uninstall target: $DEST"
  if [ "$DRY" -eq 1 ]; then echo "DRY RUN: preserve current install and restore newest backup under $BACKUP"; exit 0; fi
  if [ -d "$DEST" ]; then mkdir -p "$BACKUP"; mv "$DEST" "$BACKUP/uninstalled-$STAMP"; else echo 'No active RCoder installation found.'; fi
  RESTORE=''; for candidate in "$BACKUP"/install-*; do [ -d "$candidate" ] && RESTORE=$candidate; done
  if [ -n "$RESTORE" ]; then mkdir -p "$(dirname "$DEST")"; mv "$RESTORE" "$DEST"; echo "Restored previous installation: $DEST"; fi
  exit 0
fi
if [ -d "$DEST" ] && diff -qr "$SOURCE" "$DEST" >/dev/null 2>&1; then echo "RCoder is already current at $DEST"; exit 0; fi
echo "Install target: $DEST"
if [ "$DRY" -eq 1 ]; then [ ! -d "$DEST" ] || echo "DRY RUN: backup existing folder to $BACKUP/install-$STAMP"; echo "DRY RUN: copy $SOURCE to $DEST"; exit 0; fi
mkdir -p "$(dirname "$DEST")" "$BACKUP"; STAGE="$(dirname "$DEST")/.rcoder-stage-$STAMP"
cleanup(){ [ ! -d "$STAGE" ] || rm -rf "$STAGE"; }; trap cleanup EXIT HUP INT TERM
cp -R "$SOURCE" "$STAGE"
if [ -d "$DEST" ]; then mv "$DEST" "$BACKUP/install-$STAMP"; echo "Backed up previous installation: $BACKUP/install-$STAMP"; fi
mv "$STAGE" "$DEST"; trap - EXIT HUP INT TERM
echo "Installed RCoder for $TARGET ($SCOPE): $DEST"
