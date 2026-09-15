"""Repository bootstrap and provider integration for POSTURE."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .core import PostureError

STATE_DIR = ".posture"
BOOTSTRAP_IGNORE = "active.json\n"

CLAUDE_HOOK_COMMAND = 'cd "$CLAUDE_PROJECT_DIR" && posture hook'
CODEX_HOOK_COMMAND = 'cd "$(git rev-parse --show-toplevel)" && posture hook'
CLAUDE_LEGACY_COMMANDS = {
    'cd "$CLAUDE_PROJECT_DIR" && python3 -m posture.hook',
}
CODEX_LEGACY_COMMANDS = {
    'cd "$(git rev-parse --show-toplevel)" && python3 -m posture.hook',
}

CLAUDE_SKILL = """---
name: posture
description: Set, clear, inspect, list, or migrate the repository's bounded POSTURE. Invoke explicitly when the user wants to change or inspect the agent's delegated standing.
disable-model-invocation: true
---

Manage repository POSTURE state using the provider-agnostic CLI.

Interpret `$ARGUMENTS` as one of:

- `set <name>`
- `clear`
- `show`
- `list`
- `migrate`

Run:

```bash
posture $ARGUMENTS
```

POSTURE is a bounded schema over epistemic authority, read reach, write reach, and continuity prior.
Do not change posture implicitly. If the user is discussing whether a posture still fits but has not asked to change it, inspect or recommend only.
"""

CODEX_SKILL = """---
name: posture
description: Set, clear, inspect, list, or migrate the repository's bounded POSTURE. Use only when the user explicitly wants to change or inspect the agent's delegated standing.
---

Manage repository POSTURE state using the provider-agnostic CLI.

Interpret the user's requested posture operation as one of:

- `set <name>`
- `clear`
- `show`
- `list`
- `migrate`

Run the corresponding command:

```bash
posture <operation>
```

POSTURE is a bounded schema over epistemic authority, read reach, write reach, and continuity prior.
Do not change posture implicitly. If the user is discussing whether a posture still fits but has not asked to change it, inspect or recommend only.
"""

CODEX_OPENAI_YAML = """interface:
  display_name: "POSTURE"
  short_description: "Set or inspect the repository's bounded agent posture."

policy:
  allow_implicit_invocation: false
"""

CLAUDE_LEGACY_SKILLS = {'---\nname: posture\ndescription: Set, clear, inspect, or list the repository\'s persistent POSTURE. Invoke explicitly when the user wants to change or inspect the agent\'s operating stance.\ndisable-model-invocation: true\n---\n\nManage repository POSTURE state using the provider-agnostic CLI.\n\nInterpret `$ARGUMENTS` as one of:\n\n- `set <name>`\n- `clear`\n- `show`\n- `list`\n\nRun:\n\n```bash\nposture $ARGUMENTS\n```\n\nDo not change posture implicitly. If the user is discussing whether a posture still fits but has not asked to change it, inspect or recommend only.\n'}
CODEX_LEGACY_SKILLS = {'---\nname: posture\ndescription: Set, clear, inspect, or list the repository\'s persistent POSTURE. Use only when the user explicitly wants to change or inspect the agent\'s operating stance.\n---\n\nManage repository POSTURE state using the provider-agnostic CLI.\n\nInterpret the user\'s requested posture operation as one of:\n\n- `set <name>`\n- `clear`\n- `show`\n- `list`\n\nRun the corresponding command:\n\n```bash\nposture <operation>\n```\n\nDo not change posture implicitly. If the user is discussing whether a posture still fits but has not asked to change it, inspect or recommend only.\n'}
CODEX_LEGACY_YAMLS = {'interface:\n  display_name: "POSTURE"\n  short_description: "Set or inspect the repository\'s anchored agent posture."\n\npolicy:\n  allow_implicit_invocation: false\n'}


@dataclass(frozen=True)
class Change:
    path: str
    action: str


def _relative(path: Path, root: Path) -> str:
    return str(path.relative_to(root))


def _check_owned(
    path: Path,
    content: str,
    root: Path,
    legacy_contents: set[str] | None = None,
) -> None:
    if not path.exists():
        return
    existing = path.read_text(encoding="utf-8")
    if existing == content or existing in (legacy_contents or set()):
        return
    raise PostureError(
        f"Refusing to overwrite existing {path.relative_to(root)}. "
        "Move or reconcile that file explicitly, then retry."
    )


def _write_owned(
    path: Path,
    content: str,
    root: Path,
    legacy_contents: set[str] | None = None,
) -> Change:
    """Create or migrate a POSTURE-owned file without overwriting foreign content."""
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        if existing == content:
            return Change(_relative(path, root), "unchanged")
        if existing in (legacy_contents or set()):
            path.write_text(content, encoding="utf-8")
            return Change(_relative(path, root), "updated")
        raise PostureError(
            f"Refusing to overwrite existing {path.relative_to(root)}. "
            "Move or reconcile that file explicitly, then retry."
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return Change(_relative(path, root), "created")


def bootstrap_repo(root: Path | str) -> list[Change]:
    """Initialize repository-local POSTURE state without provider integration."""
    root = Path(root).resolve()
    state_dir = root / STATE_DIR
    (state_dir / "presets").mkdir(parents=True, exist_ok=True)

    ignore_path = state_dir / ".gitignore"
    if not ignore_path.exists():
        ignore_path.write_text(BOOTSTRAP_IGNORE, encoding="utf-8")
        return [Change(_relative(ignore_path, root), "created")]

    existing = ignore_path.read_text(encoding="utf-8")
    lines = [line.strip() for line in existing.splitlines()]
    if "active.json" in lines:
        return [Change(_relative(ignore_path, root), "unchanged")]

    suffix = "" if existing.endswith("\n") or not existing else "\n"
    ignore_path.write_text(existing + suffix + "active.json\n", encoding="utf-8")
    return [Change(_relative(ignore_path, root), "updated")]


def is_bootstrapped(root: Path | str) -> bool:
    root = Path(root).resolve()
    ignore_path = root / STATE_DIR / ".gitignore"
    if not ignore_path.is_file():
        return False
    return "active.json" in {
        line.strip() for line in ignore_path.read_text(encoding="utf-8").splitlines()
    }


def _load_json(path: Path, root: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PostureError(
            f"Cannot merge POSTURE integration into {path.relative_to(root)}: "
            f"invalid JSON ({exc})."
        ) from exc
    if not isinstance(value, dict):
        raise PostureError(
            f"Cannot merge POSTURE integration into {path.relative_to(root)}: "
            "top-level JSON value must be an object."
        )
    return value


def _hook_entries(path: Path, root: Path) -> tuple[dict[str, object], list[object]]:
    data = _load_json(path, root)
    hooks = data.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise PostureError(
            f"Cannot merge POSTURE integration into {path.relative_to(root)}: "
            "'hooks' must be an object."
        )

    entries = hooks.setdefault("UserPromptSubmit", [])
    if not isinstance(entries, list):
        raise PostureError(
            f"Cannot merge POSTURE integration into {path.relative_to(root)}: "
            "'hooks.UserPromptSubmit' must be a list."
        )
    return data, entries


def _merge_hook(
    path: Path,
    root: Path,
    command: str,
    extra: dict[str, object] | None = None,
    legacy_commands: set[str] | None = None,
) -> Change:
    existed = path.exists()
    data, entries = _hook_entries(path, root)
    legacy_commands = legacy_commands or set()

    for entry in entries:
        if not isinstance(entry, dict):
            continue
        nested = entry.get("hooks")
        if not isinstance(nested, list):
            continue
        for hook in nested:
            if not isinstance(hook, dict):
                continue
            current = hook.get("command")
            if current == command:
                return Change(_relative(path, root), "unchanged")
            if current in legacy_commands:
                hook["command"] = command
                if extra:
                    hook.update(extra)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
                return Change(_relative(path, root), "updated")

    hook: dict[str, object] = {
        "type": "command",
        "command": command,
        "timeout": 5,
    }
    if extra:
        hook.update(extra)
    entries.append({"hooks": [hook]})

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return Change(_relative(path, root), "updated" if existed else "created")


def _preflight_claude(root: Path) -> None:
    _hook_entries(root / ".claude" / "settings.json", root)
    _check_owned(
        root / ".claude" / "skills" / "posture" / "SKILL.md",
        CLAUDE_SKILL,
        root,
        CLAUDE_LEGACY_SKILLS,
    )


def _preflight_codex(root: Path) -> None:
    _hook_entries(root / ".codex" / "hooks.json", root)
    _check_owned(
        root / ".agents" / "skills" / "posture" / "SKILL.md",
        CODEX_SKILL,
        root,
        CODEX_LEGACY_SKILLS,
    )
    _check_owned(
        root / ".agents" / "skills" / "posture" / "agents" / "openai.yaml",
        CODEX_OPENAI_YAML,
        root,
        CODEX_LEGACY_YAMLS,
    )


def _install_claude(root: Path) -> list[Change]:
    return [
        _merge_hook(
            root / ".claude" / "settings.json",
            root,
            CLAUDE_HOOK_COMMAND,
            legacy_commands=CLAUDE_LEGACY_COMMANDS,
        ),
        _write_owned(
            root / ".claude" / "skills" / "posture" / "SKILL.md",
            CLAUDE_SKILL,
            root,
            CLAUDE_LEGACY_SKILLS,
        ),
    ]


def _install_codex(root: Path) -> list[Change]:
    return [
        _merge_hook(
            root / ".codex" / "hooks.json",
            root,
            CODEX_HOOK_COMMAND,
            {"additionalContextLimit": 1200},
            legacy_commands=CODEX_LEGACY_COMMANDS,
        ),
        _write_owned(
            root / ".agents" / "skills" / "posture" / "SKILL.md",
            CODEX_SKILL,
            root,
            CODEX_LEGACY_SKILLS,
        ),
        _write_owned(
            root / ".agents" / "skills" / "posture" / "agents" / "openai.yaml",
            CODEX_OPENAI_YAML,
            root,
            CODEX_LEGACY_YAMLS,
        ),
    ]


def install_providers(
    root: Path | str, providers: Iterable[str] = ("claude", "codex")
) -> list[Change]:
    """Install provider adapters into an already-bootstrapped repository."""
    root = Path(root).resolve()
    if not is_bootstrapped(root):
        raise PostureError(
            "Repository is not bootstrapped for POSTURE. Run `posture bootstrap` first."
        )

    normalized = list(dict.fromkeys(provider.strip().lower() for provider in providers))
    unknown = [provider for provider in normalized if provider not in {"claude", "codex"}]
    if unknown:
        raise PostureError(f"Unsupported provider(s): {', '.join(unknown)}")

    for provider in normalized:
        if provider == "claude":
            _preflight_claude(root)
        elif provider == "codex":
            _preflight_codex(root)

    changes: list[Change] = []
    for provider in normalized:
        if provider == "claude":
            changes.extend(_install_claude(root))
        elif provider == "codex":
            changes.extend(_install_codex(root))
    return changes
