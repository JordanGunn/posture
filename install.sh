#!/bin/sh
set -eu

PYTHON="${PYTHON:-python3}"
POSTURE_HOME="${POSTURE_HOME:-$HOME/.local/share/posture}"
POSTURE_BIN_DIR="${POSTURE_BIN_DIR:-$HOME/.local/bin}"
POSTURE_SOURCE="${POSTURE_SOURCE:-https://github.com/JordanGunn/posture/archive/refs/heads/master.zip}"
VENV="$POSTURE_HOME/venv"

if ! command -v "$PYTHON" >/dev/null 2>&1; then
    echo "posture installer: Python 3.10+ is required." >&2
    exit 1
fi

if ! "$PYTHON" - <<'PY'
import sys
raise SystemExit(0 if sys.version_info >= (3, 10) else 1)
PY
then
    echo "posture installer: Python 3.10+ is required." >&2
    exit 1
fi

mkdir -p "$POSTURE_HOME" "$POSTURE_BIN_DIR"

if ! "$PYTHON" -m venv "$VENV"; then
    echo "posture installer: could not create a virtual environment." >&2
    echo "Install your Python venv support (for example python3-venv on Debian/Ubuntu) and retry." >&2
    exit 1
fi

"$VENV/bin/python" -m pip install --disable-pip-version-check --quiet --upgrade pip
"$VENV/bin/python" -m pip install --disable-pip-version-check --quiet --upgrade "$POSTURE_SOURCE"

ln -sf "$VENV/bin/posture" "$POSTURE_BIN_DIR/posture"

echo "POSTURE installed: $POSTURE_BIN_DIR/posture"
case ":$PATH:" in
    *":$POSTURE_BIN_DIR:"*) ;;
    *)
        echo "Add $POSTURE_BIN_DIR to PATH to invoke 'posture' directly."
        ;;
esac

echo
echo "Next:"
echo "  cd <your-repository>"
echo "  posture bootstrap"
echo "  posture install"
echo "  posture set migration"
