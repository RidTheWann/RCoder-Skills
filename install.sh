#!/usr/bin/env sh
# Stable POSIX entrypoint. Keep installation behavior in scripts/install.sh.
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
DELEGATE="$ROOT/scripts/install.sh"

if [ ! -f "$DELEGATE" ]; then
  printf '%s\n' "[RCoder] ERROR: canonical installer not found: $DELEGATE" >&2
  printf '%s\n' "Cause: the repository checkout is incomplete or scripts/install.sh was moved." >&2
  printf '%s\n' "Fix: restore scripts/install.sh from the same RCoder-Skills release, then retry." >&2
  exit 1
fi

exec sh "$DELEGATE" "$@"
