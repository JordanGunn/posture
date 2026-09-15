"""Shared Claude Code / Codex UserPromptSubmit hook."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from .core import PostureError, find_repo_root, render_active


def _warning(message: str) -> None:
    print(json.dumps({"systemMessage": f"POSTURE warning: {message}"}))


def main(cwd: Path | str | None = None) -> int:
    # Consume the hook payload even though v0 does not inspect the prompt.
    try:
        sys.stdin.read()
    except OSError:
        pass

    try:
        root = find_repo_root(cwd)
        rendered = render_active(root)
    except PostureError as exc:
        _warning(str(exc))
        return 0

    if not rendered:
        return 0

    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "UserPromptSubmit",
                    "additionalContext": rendered,
                }
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
