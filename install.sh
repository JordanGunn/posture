#!/bin/sh
set -eu

PYTHON="${PYTHON:-python3}"
POSTURE_HOME="${POSTURE_HOME:-$HOME/.local/share/posture}"
POSTURE_BIN_DIR="${POSTURE_BIN_DIR:-$HOME/.local/bin}"
POSTURE_SOURCE="${POSTURE_SOURCE:-https://github.com/JordanGunn/posture/archive/refs/heads/master.zip}"
APP_DIR="$POSTURE_HOME/app"

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

PYTHON_BIN="$(command -v "$PYTHON")"
mkdir -p "$POSTURE_HOME" "$POSTURE_BIN_DIR"

# v0.1 used a virtual environment. Remove an incomplete or previous install;
# POSTURE is stdlib-only and no longer needs venv/pip at runtime.
rm -rf "$POSTURE_HOME/venv"

POSTURE_SOURCE="$POSTURE_SOURCE" APP_DIR="$APP_DIR" "$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import io
import os
import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path

source = os.environ["POSTURE_SOURCE"]
target = Path(os.environ["APP_DIR"]).expanduser().resolve()
target.parent.mkdir(parents=True, exist_ok=True)

try:
    with urllib.request.urlopen(source) as response:
        payload = response.read()
except Exception as exc:
    raise SystemExit(f"posture installer: could not download {source}: {exc}")

try:
    archive = zipfile.ZipFile(io.BytesIO(payload))
except zipfile.BadZipFile as exc:
    raise SystemExit(f"posture installer: downloaded source is not a valid zip archive: {exc}")

with archive:
    package_members = []
    for info in archive.infolist():
        parts = Path(info.filename).parts
        if len(parts) >= 2 and parts[1] == "posture":
            package_members.append((info, parts[2:]))

    if not package_members:
        raise SystemExit("posture installer: source archive does not contain the posture package")

    with tempfile.TemporaryDirectory(prefix="posture-install-", dir=target.parent) as tmp:
        staged = Path(tmp) / "app"
        package_root = staged / "posture"
        package_root.mkdir(parents=True)

        for info, relative_parts in package_members:
            if not relative_parts or info.is_dir():
                continue
            destination = package_root.joinpath(*relative_parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(archive.read(info))

        if not (package_root / "__main__.py").is_file():
            raise SystemExit("posture installer: source archive contains an incomplete posture package")

        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(staged, target)
PY

cat > "$POSTURE_BIN_DIR/posture" <<EOF
#!/bin/sh
POSTURE_HOME="\${POSTURE_HOME:-$POSTURE_HOME}"
export PYTHONPATH="\$POSTURE_HOME/app\${PYTHONPATH:+:\$PYTHONPATH}"
exec "$PYTHON_BIN" -m posture "\$@"
EOF
chmod +x "$POSTURE_BIN_DIR/posture"

if ! "$POSTURE_BIN_DIR/posture" --help >/dev/null 2>&1; then
    echo "posture installer: installed CLI failed its self-check." >&2
    exit 1
fi

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
