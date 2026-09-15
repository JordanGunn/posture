"""Provider-agnostic POSTURE state, presets, migration, and rendering."""

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

from .schema import Profile, SchemaError, parse_profile, render_profile

STATE_SCHEMA_VERSION = 2
LEGACY_STATE_SCHEMA_VERSION = 1
STATE_DIR = ".posture"
STATE_FILE = "active.json"
LOCAL_PRESETS_DIR = "presets"
LEGACY_DEFINITIONS_DIR = "postures"
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")

LEGACY_BUILTIN_HASHES = {
    "migration": "aa3773e6ce5b132ce93568ffd33d62759e6eefe970b8f169b3216602b94d7e78",
    "maintenance": "8779c8c98cba6255a4533259e8592c8f3d59f56c30062e124cf137e72cb91747",
}

RUNTIME_CONTRACT = """POSTURE declares standing explicitly delegated by the human.
Apply it when ambiguity would otherwise make you defer, stay local, or preserve the existing state.

- These axes change the burden of proof; they do not predetermine conclusions.
- Explicit current requirements, hard constraints, and direct evidence override posture defaults for the decision at hand.
- A local override does not change the persistent posture.
- POSTURE does not grant permissions beyond the tools, environment, or authorization already in force.
- Read reach and write reach are ceilings, not obligations to expand scope.
- Do not broaden work into unrelated cleanup merely because a posture permits broader action.
"""


class PostureError(RuntimeError):
    """Raised when POSTURE state, presets, or migration are invalid."""


@dataclass(frozen=True)
class Preset:
    name: str
    profile: Profile
    source: str

    @property
    def sha256(self) -> str:
        return self.profile.sha256


@dataclass(frozen=True)
class ActivePosture:
    name: str
    profile: Profile
    source: str
    sha256: str
    schema_version: int = STATE_SCHEMA_VERSION


@dataclass(frozen=True)
class MigrationResult:
    active_action: str
    legacy_definitions: tuple[str, ...]


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


def _local_preset_path(root: Path, name: str) -> Path:
    return root / STATE_DIR / LOCAL_PRESETS_DIR / f"{name}.json"


def _legacy_definition_paths(root: Path) -> tuple[Path, ...]:
    legacy = root / STATE_DIR / LEGACY_DEFINITIONS_DIR
    if not legacy.is_dir():
        return ()
    return tuple(sorted(path for path in legacy.glob("*.md") if path.is_file()))


def _parse_preset_text(name: str, text: str, source: str) -> Preset:
    try:
        raw = json.loads(text)
    except json.JSONDecodeError as exc:
        raise PostureError(f"Invalid posture preset {source}: {exc}") from exc
    if not isinstance(raw, dict):
        raise PostureError(f"Invalid posture preset {source}: top-level value must be an object.")
    try:
        profile = parse_profile(raw)
    except SchemaError as exc:
        raise PostureError(f"Invalid posture preset {source}: {exc}") from exc
    return Preset(name=name, profile=profile, source=source)


def _builtin_preset(name: str) -> Preset | None:
    try:
        resource = importlib.resources.files("posture.presets").joinpath(f"{name}.json")
        if not resource.is_file():
            return None
        return _parse_preset_text(
            name,
            resource.read_text(encoding="utf-8"),
            f"builtin:{name}",
        )
    except (FileNotFoundError, ModuleNotFoundError):
        return None


def resolve_preset(name: str, root: Path | str) -> Preset:
    """Resolve a repository structured preset first, then a bundled preset."""
    root = Path(root).resolve()
    name = _validate_name(name)
    local = _local_preset_path(root, name)
    if local.is_file():
        return _parse_preset_text(
            name,
            local.read_text(encoding="utf-8"),
            str(local.relative_to(root)),
        )
    builtin = _builtin_preset(name)
    if builtin is not None:
        return builtin
    raise PostureError(f"Unknown posture preset: {name}")


def _iter_builtin_names() -> Iterable[str]:
    try:
        for item in importlib.resources.files("posture.presets").iterdir():
            if item.is_file() and item.name.endswith(".json"):
                yield item.name[:-5]
    except (FileNotFoundError, ModuleNotFoundError):
        return


def list_presets(root: Path | str) -> list[Preset]:
    """List available structured presets, with repository presets overriding built-ins."""
    root = Path(root).resolve()
    names = set(_iter_builtin_names())
    local_dir = root / STATE_DIR / LOCAL_PRESETS_DIR
    if local_dir.is_dir():
        names.update(path.stem for path in local_dir.glob("*.json"))

    presets: list[Preset] = []
    for name in sorted(names):
        try:
            presets.append(resolve_preset(name, root))
        except PostureError:
            continue
    return presets


def _write_active(active: ActivePosture, root: Path) -> None:
    path = _state_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": active.schema_version,
        "name": active.name,
        "sha256": active.sha256,
        "source": active.source,
        "profile": active.profile.as_dict(),
    }
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def set_active(name: str, root: Path | str) -> ActivePosture:
    """Snapshot a validated structured preset as the active repository posture."""
    root = Path(root).resolve()
    preset = resolve_preset(name, root)
    active = ActivePosture(
        name=preset.name,
        profile=preset.profile,
        source=preset.source,
        sha256=preset.sha256,
    )
    _write_active(active, root)
    return active


def clear_active(root: Path | str) -> bool:
    """Clear the active posture. Returns True when state existed."""
    path = _state_path(Path(root).resolve())
    try:
        path.unlink()
        return True
    except FileNotFoundError:
        return False


def _read_raw_state(root: Path) -> dict[str, object] | None:
    path = _state_path(root)
    if not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise PostureError(f"Invalid POSTURE state at {path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise PostureError(f"Invalid POSTURE state at {path}: top-level value must be an object.")
    return raw


def get_active(root: Path | str) -> ActivePosture | None:
    """Read and validate the snapshotted structured posture."""
    root = Path(root).resolve()
    raw = _read_raw_state(root)
    if raw is None:
        return None

    schema_version = raw.get("schema_version")
    if schema_version == LEGACY_STATE_SCHEMA_VERSION:
        raise PostureError(
            "Legacy free-form POSTURE state detected (schema 1). Run `posture migrate` "
            "to migrate known presets, or explicitly clear and set a structured posture."
        )
    if schema_version != STATE_SCHEMA_VERSION:
        raise PostureError(f"Unsupported POSTURE state schema: {schema_version!r}")

    name = raw.get("name")
    source = raw.get("source")
    sha256 = raw.get("sha256")
    profile_raw = raw.get("profile")
    if not isinstance(name, str) or not isinstance(source, str) or not isinstance(sha256, str):
        raise PostureError(f"Incomplete POSTURE state at {_state_path(root)}")
    if not isinstance(profile_raw, dict):
        raise PostureError(f"Incomplete POSTURE profile at {_state_path(root)}")
    try:
        profile = parse_profile(profile_raw)
    except SchemaError as exc:
        raise PostureError(f"Invalid active POSTURE profile: {exc}") from exc

    if profile.sha256 != sha256:
        raise PostureError(
            "Active POSTURE snapshot failed integrity validation. "
            "Clear it and explicitly set the posture again."
        )

    return ActivePosture(
        name=name,
        profile=profile,
        source=source,
        sha256=sha256,
    )


def preset_drifted(active: ActivePosture, root: Path | str) -> bool:
    """Return True when the source preset changed after activation."""
    try:
        current = resolve_preset(active.name, root)
    except PostureError:
        return True
    return current.sha256 != active.sha256


def render_active(root: Path | str) -> str | None:
    """Render the exact snapshotted structured posture for context injection."""
    active = get_active(root)
    if active is None:
        return None

    return (
        f'<POSTURE name="{active.name}" sha256="{active.sha256[:12]}">\n'
        f"{RUNTIME_CONTRACT.strip()}\n\n"
        f"{render_profile(active.profile)}\n"
        "</POSTURE>"
    )


def show_active(root: Path | str) -> dict[str, object] | None:
    """Return inspectable active state, including structured axes and preset drift."""
    active = get_active(root)
    if active is None:
        return None
    return {
        "name": active.name,
        "sha256": active.sha256,
        "source": active.source,
        "drifted": preset_drifted(active, root),
        "profile": active.profile.as_dict(),
    }


def _validate_legacy_state(raw: dict[str, object]) -> tuple[str, str]:
    required = ("name", "body", "source", "sha256")
    if any(not isinstance(raw.get(key), str) for key in required):
        raise PostureError("Legacy POSTURE state is incomplete and cannot be migrated safely.")
    body = raw["body"]
    sha256 = raw["sha256"]
    expected = hashlib.sha256(body.encode("utf-8")).hexdigest()
    if expected != sha256:
        raise PostureError(
            "Legacy POSTURE state failed integrity validation and cannot be migrated safely."
        )
    return raw["name"], raw["source"]


def migrate_repo(root: Path | str) -> MigrationResult:
    """Migrate safe legacy state to the bounded schema without inferring from prose."""
    root = Path(root).resolve()
    (root / STATE_DIR / LOCAL_PRESETS_DIR).mkdir(parents=True, exist_ok=True)
    legacy_files = tuple(str(path.relative_to(root)) for path in _legacy_definition_paths(root))
    raw = _read_raw_state(root)

    if raw is None:
        return MigrationResult("none", legacy_files)

    schema_version = raw.get("schema_version")
    if schema_version == STATE_SCHEMA_VERSION:
        get_active(root)
        return MigrationResult("already-current", legacy_files)

    if schema_version != LEGACY_STATE_SCHEMA_VERSION:
        raise PostureError(f"Unsupported POSTURE state schema: {schema_version!r}")

    name, source = _validate_legacy_state(raw)
    legacy_hash = raw["sha256"]
    expected_legacy_hash = LEGACY_BUILTIN_HASHES.get(name)
    if (
        source != f"builtin:{name}"
        or expected_legacy_hash is None
        or legacy_hash != expected_legacy_hash
    ):
        raise PostureError(
            f"Legacy active posture {name!r} is not an exact known bundled definition. "
            "POSTURE will not infer structured authorization from arbitrary or modified prose. "
            "Clear it and explicitly set or author a bounded JSON preset under "
            "`.posture/presets/`."
        )

    try:
        preset = resolve_preset(name, root)
    except PostureError as exc:
        raise PostureError(
            f"Legacy built-in posture {name!r} has no structured migration target."
        ) from exc

    active = ActivePosture(
        name=preset.name,
        profile=preset.profile,
        source=preset.source,
        sha256=preset.sha256,
    )
    _write_active(active, root)
    return MigrationResult("migrated", legacy_files)
