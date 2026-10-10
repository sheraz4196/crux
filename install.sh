#!/bin/sh
# Install into an isolated environment; no activation needed.
set -eu
CRUX_SOURCE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
CRUX_HOME="${XDG_DATA_HOME:-$HOME/.local/share}/crux"
CRUX_BIN="$HOME/.local/bin"
python3 -m venv "$CRUX_HOME/venv"
"$CRUX_HOME/venv/bin/python" -m pip install "$CRUX_SOURCE"
mkdir -p "$CRUX_BIN"
if [ -e "$CRUX_BIN/crux" ] && [ ! -L "$CRUX_BIN/crux" ]; then
  echo "Refusing to replace $CRUX_BIN/crux; remove or rename it first." >&2
  exit 1
fi
ln -sfn "$CRUX_HOME/venv/bin/crux" "$CRUX_BIN/crux"
export PATH="$CRUX_BIN:$PATH"
"$CRUX_BIN/crux" install --yes "$@"
printf '%s\n' 'Crux installed. Open a new terminal; no virtual environment activation is needed.'
