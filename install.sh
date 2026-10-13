#!/bin/sh
# Install into an isolated environment; no activation needed.
set -eu
CRUX_SOURCE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
CRUX_HOME="${XDG_DATA_HOME:-$HOME/.local/share}/crux"
CRUX_BIN="$HOME/.local/bin"
# Check ownership before touching the installation environment.
if [ -e "$CRUX_BIN/crux" ] && [ ! -L "$CRUX_BIN/crux" ]; then
  echo "Refusing to replace $CRUX_BIN/crux; remove or rename it first." >&2
  exit 1
fi
if [ -L "$CRUX_BIN/crux" ] && [ "$(readlink "$CRUX_BIN/crux")" != "$CRUX_HOME/venv/bin/crux" ]; then
  echo "Refusing to replace an unrelated Crux link: $CRUX_BIN/crux" >&2
  exit 1
fi
if [ -L "$CRUX_HOME/venv" ]; then
  echo "Refusing to install into a symlinked environment: $CRUX_HOME/venv" >&2
  exit 1
fi
if [ -e "$CRUX_HOME/venv" ]; then
  if [ ! -x "$CRUX_HOME/venv/bin/python" ]; then
    echo "Existing Crux environment is incomplete: $CRUX_HOME/venv; inspect it before retrying." >&2
    exit 1
  fi
else
  python3 -m venv "$CRUX_HOME/venv"
fi
"$CRUX_HOME/venv/bin/python" -m pip install "$CRUX_SOURCE"
mkdir -p "$CRUX_BIN"
ln -sfn "$CRUX_HOME/venv/bin/crux" "$CRUX_BIN/crux"
export PATH="$CRUX_BIN:$PATH"
"$CRUX_BIN/crux" install --yes "$@"
printf '%s\n' 'Crux installed. Open a new terminal; no virtual environment activation is needed.'
printf '%s\n' 'Integration leaves PATH unchanged. Ensure ~/.local/bin is on your existing PATH for new shells.'
