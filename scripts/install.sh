#!/bin/sh
set -eu
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
usage(){
  cat <<'EOF'
Usage: install.sh [OPTIONS]

Host and scope:
  --target ID, --host ID   Host from targets.json (default: agents).
                           Aliases: claude -> claude-code, gemini -> gemini-cli.
  --scope project|user     Installation scope (default: project).
  --project-dir PATH       Project root (default: current directory).
  --home-dir PATH          User home override (default: $HOME).

Actions:
  --dry-run                Preview without changing files.
  --uninstall              Remove RCoder and restore the latest backup.
  --doctor                 Run the RCoder CLI doctor (requires Node.js >= 18.18).
  --yes, -y                Accepted for automation; this installer is non-interactive.
  --list-features          List optional tools.
  --help, -h               Show this help.

Optional integrations:
  --features CSV           rsaver,rscan (default) or none.
  --mcp none|show|install  Skip, print, or apply MCP host configuration.
EOF
}
TARGET=agents
SCOPE=project
PROJECT_DIR=$(pwd)
HOME_DIR=${HOME:-}
DRY=0
REMOVE=0
DOCTOR=0
FEATURES=rsaver,rscan
MCP=none

while [ "$#" -gt 0 ]; do
  case "$1" in
    --target|--host)
      [ "$#" -ge 2 ] || { echo "Missing value for $1" >&2; usage >&2; exit 2; }
      TARGET=$2
      shift 2
      ;;
    --scope)
      [ "$#" -ge 2 ] || { echo 'Missing value for --scope' >&2; usage >&2; exit 2; }
      SCOPE=$2
      shift 2
      ;;
    --project-dir)
      [ "$#" -ge 2 ] || { echo 'Missing value for --project-dir' >&2; usage >&2; exit 2; }
      PROJECT_DIR=$2
      shift 2
      ;;
    --home-dir)
      [ "$#" -ge 2 ] || { echo 'Missing value for --home-dir' >&2; usage >&2; exit 2; }
      HOME_DIR=$2
      shift 2
      ;;
    --features)
      [ "$#" -ge 2 ] || { echo 'Missing value for --features' >&2; usage >&2; exit 2; }
      FEATURES=$2
      shift 2
      ;;
    --mcp)
      [ "$#" -ge 2 ] || { echo 'Missing value for --mcp' >&2; usage >&2; exit 2; }
      MCP=$2
      shift 2
      ;;
    --list-features)
      echo 'RSaver: Context pruning, budgeting, and re-anchoring for long sessions'
      echo 'RScan: Read-only project scan with ranked development options at session start'
      exit 0
      ;;
    --dry-run) DRY=1; shift ;;
    --uninstall) REMOVE=1; shift ;;
    --doctor) DOCTOR=1; shift ;;
    --yes|-y) shift ;; # No prompt is used; accept the flag for automation compatibility.
    -h|--help) usage; exit 0 ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

case "$TARGET" in
  claude) TARGET=claude-code ;;
  gemini) TARGET=gemini-cli ;;
  all)
    echo "[RCoder] ERROR: --host all is not a valid single-host install target." >&2
    echo "Cause: this installer installs one host integration per invocation." >&2
    echo "Fix: use --target agents for a generic Agent Skills installation, or run once per host." >&2
    exit 2
    ;;
  mcp)
    echo "[RCoder] ERROR: MCP is an integration mode, not an installation target." >&2
    echo "Cause: an MCP server must be configured for a concrete host and scope." >&2
    echo "Fix: use --target <host> --mcp install." >&2
    exit 2
    ;;
esac

if [ "$DOCTOR" -eq 1 ]; then
  if [ "$REMOVE" -eq 1 ] || [ "$DRY" -eq 1 ]; then
    echo "[RCoder] ERROR: --doctor cannot be combined with --dry-run or --uninstall." >&2
    exit 2
  fi
  if ! command -v node >/dev/null 2>&1; then
    echo "[RCoder] ERROR: Node.js is required for the CLI doctor." >&2
    echo "Cause: the diagnostic command runs scripts/rcoder.mjs." >&2
    echo "Fix: install Node.js 18.18 or newer, then run ./install.sh --doctor." >&2
    exit 1
  fi
  if ! node -e 'const [major, minor] = process.versions.node.split(".").map(Number); process.exit(major > 18 || (major === 18 && minor >= 18) ? 0 : 1)' >/dev/null 2>&1; then
    echo "[RCoder] ERROR: Node.js $(node -v) is older than the required 18.18." >&2
    echo "Cause: the RCoder CLI uses runtime features from Node.js 18.18 or newer." >&2
    echo "Fix: update Node.js to the current LTS release, then rerun ./install.sh --doctor." >&2
    exit 1
  fi
  exec node "$SCRIPT_DIR/rcoder.mjs" doctor --json
fi

case "$TARGET" in
  claude-code) PROJECT_ROOT=.claude; USER_ROOT=.claude ;;
  codex|agents|zed|openclaw) PROJECT_ROOT=.agents; USER_ROOT=.agents ;;
  cursor) PROJECT_ROOT=.cursor; USER_ROOT=.cursor ;;
  gemini-cli) PROJECT_ROOT=.gemini; USER_ROOT=.gemini ;;
  copilot) PROJECT_ROOT=.github; USER_ROOT=.copilot ;;
  qoder) PROJECT_ROOT=.qoder; USER_ROOT=.qoder ;;
  opencode) PROJECT_ROOT=.opencode; USER_ROOT=.config/opencode ;;
  antigravity) PROJECT_ROOT=.agents; USER_ROOT=.gemini/config ;;
  amp) PROJECT_ROOT=.agents; USER_ROOT=.config/agents ;;
  pi) PROJECT_ROOT=.pi; USER_ROOT=.pi/agent ;;
  autohand) PROJECT_ROOT=.autohand; USER_ROOT=.autohand ;;
  warp) PROJECT_ROOT=.warp; USER_ROOT=.warp ;;
  kilocode) PROJECT_ROOT=.kilo; USER_ROOT=.kilo ;;
  cline) PROJECT_ROOT=.cline; USER_ROOT=.cline ;;
  roo-code) PROJECT_ROOT=.roo; USER_ROOT=.roo ;;
  trae) PROJECT_ROOT=.trae; USER_ROOT=.trae ;;
  factory) PROJECT_ROOT=.factory; USER_ROOT=.factory ;;
  *)
    echo "Unsupported target: $TARGET" >&2
    echo "Valid targets: claude-code, codex, cursor, gemini-cli, copilot, agents, qoder, opencode, antigravity, amp, zed, pi, openclaw, autohand, warp, kilocode, cline, roo-code, trae, factory." >&2
    echo "Fix: choose one target from the list and retry." >&2
    exit 2
    ;;
esac

case "$MCP" in none|show|install) ;; *) echo '--mcp must be none, show, or install' >&2; exit 2 ;; esac
case "$SCOPE" in
  project) BASE=$PROJECT_DIR; ROOT=$PROJECT_ROOT ;;
  user)
    [ -n "$HOME_DIR" ] || { echo 'HOME is not set; pass --home-dir' >&2; exit 1; }
    BASE=$HOME_DIR
    ROOT=$USER_ROOT
    ;;
  *) echo 'Scope must be project or user' >&2; exit 2 ;;
esac

if [ "$FEATURES" != none ]; then
  OLDIFS=$IFS
  IFS=,
  for feature in $FEATURES; do
    case "$feature" in rsaver|rscan) ;; *) echo "Unknown optional tool: $feature" >&2; exit 2 ;; esac
  done
  IFS=$OLDIFS
fi

[ -d "$BASE" ] || { echo "Selected directory does not exist: $BASE" >&2; exit 1; }
SOURCE="$SCRIPT_DIR/../skills/rcoder"
[ -f "$SOURCE/SKILL.md" ] || { echo "Skill source missing: $SOURCE/SKILL.md" >&2; exit 1; }
TARGET_ROOT="$BASE/$ROOT"
DEST="$TARGET_ROOT/skills/rcoder"
BACKUP="$TARGET_ROOT/.rcoder-backups/rcoder"
LEGACY_BACKUP="$TARGET_ROOT/.rcoder-backups/$TARGET"
STAMP=$(date -u '+%Y%m%dT%H%M%SZ')-$$

check_links(){
  base=$1
  target=$2
  case "$target" in "$base"/*) rel=${target#"$base"/} ;; *) echo "Refusing path outside selected scope: $target" >&2; exit 1 ;; esac
  current=$base
  oldIFS=$IFS
  IFS=/
  for part in $rel; do
    current="$current/$part"
    [ ! -L "$current" ] || { echo "Refusing symbolic link: $current" >&2; exit 1; }
  done
  IFS=$oldIFS
}
check_links "$BASE" "$DEST"
check_links "$BASE" "$BACKUP"
check_links "$BASE" "$LEGACY_BACKUP"

if [ "$REMOVE" -eq 1 ]; then
  echo "Uninstall target: $TARGET -> $DEST"
  if [ "$DRY" -eq 1 ]; then
    echo "DRY RUN: preserve active install and restore latest backup under $BACKUP"
    exit 0
  fi
  if [ -d "$DEST" ]; then
    mkdir -p "$BACKUP"
    mv "$DEST" "$BACKUP/uninstalled-$STAMP"
  else
    echo 'No active RCoder installation found.'
  fi
  RESTORE=''
  for candidate in "$BACKUP"/install-*; do [ -d "$candidate" ] && RESTORE=$candidate; done
  if [ -z "$RESTORE" ]; then
    for candidate in "$LEGACY_BACKUP"/install-*; do [ -d "$candidate" ] && RESTORE=$candidate; done
  fi
  if [ -n "$RESTORE" ]; then
    mkdir -p "$(dirname "$DEST")"
    mv "$RESTORE" "$DEST"
    echo "Restored previous installation: $DEST"
  fi
  rm -f "$TARGET_ROOT/.rcoder-features.json"
  exit 0
fi

mcp_step(){
  [ "$MCP" != none ] || return 0
  PY=''
  for candidate in python3 python; do
    if command -v "$candidate" >/dev/null 2>&1 && [ "$("$candidate" -c 'import sys; print(sys.version_info[0])' 2>/dev/null)" = 3 ]; then
      PY=$candidate
      break
    fi
  done
  if [ -z "$PY" ]; then
    echo 'MCP setup skipped: Python 3 was not found (the MCP server is a Python script).'
    return 0
  fi
  ACTION=show
  [ "$MCP" = install ] && ACTION=apply
  "$PY" "$DEST/scripts/rcoder_mcp_setup.py" "$ACTION" --host "$TARGET" --scope "$SCOPE" --base "$BASE" --server "$DEST/scripts/rcoder_mcp_modern.py" || echo 'Warning: MCP setup reported a problem.'
}

if [ -d "$DEST" ] && diff -qr "$SOURCE" "$DEST" >/dev/null 2>&1; then
  echo "RCoder is already current at $DEST"
  [ "$DRY" -eq 1 ] || mcp_step
  exit 0
fi

echo "Install target: $TARGET ($SCOPE) -> $DEST"
if [ "$DRY" -eq 1 ]; then
  [ ! -d "$DEST" ] || echo "DRY RUN: backup existing folder to $BACKUP/install-$STAMP"
  echo "DRY RUN: copy skill bundle to $DEST"
  exit 0
fi

mkdir -p "$(dirname "$DEST")" "$BACKUP"
STAGE="$(dirname "$DEST")/.rcoder-stage-$STAMP"
SAVED=''
cleanup(){ [ ! -d "$STAGE" ] || rm -rf "$STAGE"; }
trap cleanup EXIT HUP INT TERM
cp -R "$SOURCE" "$STAGE"
if [ -d "$DEST" ]; then
  SAVED="$BACKUP/install-$STAMP"
  mv "$DEST" "$SAVED"
fi
if ! mv "$STAGE" "$DEST"; then
  [ -z "$SAVED" ] || mv "$SAVED" "$DEST"
  exit 1
fi
trap - EXIT HUP INT TERM

echo "Installed RCoder for $TARGET: $DEST"
FEATURE_MANIFEST="$TARGET_ROOT/.rcoder-features.json"
RSAVER=false
RSCAN=false
case ",$FEATURES," in *,rsaver,*) RSAVER=true ;; esac
case ",$FEATURES," in *,rscan,*) RSCAN=true ;; esac
VERSION=$(grep -m1 '"version"' "$SCRIPT_DIR/../package.json" | tr -dc '0-9.')
FEATURE_TMP="$TARGET_ROOT/.rcoder-features.json.tmp.$$"
printf '{\n  "schema_version": 1,\n  "version": "%s",\n  "rsaver": %s,\n  "rscan": %s\n}\n' "$VERSION" "$RSAVER" "$RSCAN" > "$FEATURE_TMP"
mv -f "$FEATURE_TMP" "$FEATURE_MANIFEST"
echo "Enabled optional tools: $FEATURES"
mcp_step
