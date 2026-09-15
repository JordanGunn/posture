"""Provider-agnostic POSTURE state and rendering."""

from __future__ import annotations

import hashlib
import importlib.resources
import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

STATE_SCHEMA_VERSION = 1
STATE_DIR = ".posture"
STATE_FILE = "active.json"
LOCAL_DEFINITIONS_DIR = "postures"
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")

RUNTIME_CONTRACT = """POSTURE is a persistent operating prior selected by the human.
Apply it when resolving ambiguity in the current work.

- Treat the posture as a default over judgment, not as a fact or predetermined conclusion.
- Explicit current requirements and direct evidence override posture defaults for the decision at hand.
- A local override does not change the persistent posture.
- POSTURE does not grant permissions beyond the tools, environment, or authorization already in force.
- Do not broaden work into unrelated cleanup merely because the posture favors a direction.
"""


class PostureError(RuntimeError):
    """Raised when POSTURE state or definitions are invalid."""


@dataclass(frozen=True)
class Definition:
    name: str
    body: str
    source: str

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.body.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ActivePosture:
    name: str
    body: str
    source: str
    sha256: str
    schema_version: int = STATE_SCHEMA_VERSION


def find_repo_root(cwd: Path | str | None = None) -> Path:
    """Resolve the current Git repository root."""
    start = Path(cwd or os.getcwd()).resolve()
    result = subprocess.run(
        ["git", "-C", str(start), "rev-parse", "--show-toplevel"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise PostureError("POSTURE requires a Git repository.")
    return Path(result.stdout.strip()).resolve()


def _validate_name(name: str) -> str:
    normalized = name.strip().lower()
    if not NAME_RE.fullmatch(normalized):
        raise PostureError(
            "Posture names must use lowercase letters, digits, '-' or '_'."
        )
    return normalized


def _state_path(root: Path) -> Path:
    return root / STATE_DIR / STATE_FILE


def _local_definition_path(root: Path, name: str) -> Path:
    return root / STATE_DIR / LOCAL_DEFINITIONS_DIR / f"{name}.md"


def _builtin_definition(name: str) -> Definition | None:
    try:
        resource = importlib.resources.files("posture.definitions").joinpath(f"{name}.md")
        if not resource.is_file():
            return None
        return Definition(
            name=name,
            body=resource.read_text(encoding="utf-8").strip(),
            source=f"builtin:{name}",
        )
    except (FileNotFoundError, ModuleNotFoundError):
        return None


def resolve_definition(name: str, root: Path | str) -> Definition:
    """Resolve a repository override first, then a bundled definition."""
    root = Path(root).resolve()
    name = _validate_name(name)
    local = _local_definition_path(root, name)
    if local.is_file():
        return Definition(
            name=name,
            body=local.read_text(encoding="utf-8").strip(),
            source=str(local.relative_to(root)),
        )
    builtin = _builtin_definition(name)
    if builtin is not None:
        return builtin
    raise PostureError(f"Unknown posture: {name}")


def _iter_builtin_names() -> Iterable[str]:
    try:
        for item in importlib.resources.files("posture.definitions").iterdir():
            if item.is_file() and item.name.endswith(".md"):
                yield item.name[:-3]
    except (FileNotFoundError, ModuleNotFoundError):
        return


def list_postures(root: Path | str) -> list[Definition]:
    """List available postures, with repository definitions overriding built-ins."""
    root = Path(root).resolve()
    names = set(_iter_builtin_names())
    local_dir = root / STATE_DIR / LOCAL_DEFINITIONS_DIR
    if local_dir.is_dir():
        names.update(path.stem for path in local_dir.glob("*.md"))

    definitions: list[Definition] = []
    for name in sorted(names):
        try:
            definitions.append(resolve_definition(name, root))
        except PostureError:
            continue
    return definitions


def set_active(name: str, root: Path | str) -> ActivePosture:
    """Snapshot a definition as the active repository posture."""
    root = Path(root).resolve()
    definition = resolve_definition(name, root)
    active = ActivePosture(
        name=definition.name,
        body=definition.body,
        source=definition.source,
        sha256=definition.sha256,
    )
    path = _state_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": active.schema_version,
        "name": active.name,
        "sha256": active.sha256,
        "source": active.source,
        "body": active.body,
    }
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)
    return active


def clear_active(root: Path | str) -> bool:
    """Clear the active posture. Returns True when state existed."""
    path = _state_path(Path(root).resolve())
    try:
        path.unlink()
        return True
    except FileNotFoundError:
        return False


def get_active(root: Path | str) -> ActivePosture | None:
    """Read the snapshotted active posture."""
    path = _state_path(Path(root).resolve())
    if not path.is_file():
        return None

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise PostureError(f"Invalid POSTURE state at {path}: {exc}") from exc

    if raw.get("schema_version") != STATE_SCHEMA_VERSION:
        raise PostureError(
            f"Unsupported POSTURE state schema: {raw.get('schema_version')!r}"
        )

    required = ("name", "body", "source", "sha256")
    if any(not isinstance(raw.get(key), str) for key in required):
        raise PostureError(f"Incomplete POSTURE state at {path}")

    expected = hashlib.sha256(raw["body"].encode("utf-8")).hexdigest()
    if expected != raw["sha256"]:
        raise PostureError(
            "Active POSTURE snapshot failed integrity validation. "
            "Clear it and explicitly set the posture again."
        )

    return ActivePosture(
        name=raw["name"],
        body=raw["body"],
        source=raw["source"],
        sha256=raw["sha256"],
    )


def definition_drifted(active: ActivePosture, root: Path | str) -> bool:
    """Return True when the source definition changed after activation."""
    try:
        current = resolve_definition(active.name, root)
    except PostureError:
        return True
    return current.sha256 != active.sha256


def render_active(root: Path | str) -> str | None:
    """Render the exact snapshotted posture for agent context injection."""
    active = get_active(root)
    if active is None:
        return None

    return (
        f'<POSTURE name="{active.name}" sha256="{active.sha256[:12]}">\n'
        f"{RUNTIME_CONTRACT.strip()}\n\n"
        f"{active.body.strip()}\n"
        "</POSTURE>"
    )


def show_active(root: Path | str) -> dict[str, object] | None:
    """Return inspectable active state, including definition drift."""
    active = get_active(root)
    if active is None:
        return None
    return {
        "name": active.name,
        "sha256": active.sha256,
        "source": active.source,
        "drifted": definition_drifted(active, root),
        "body": active.body,
    }
