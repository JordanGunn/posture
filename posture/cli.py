"""Command-line interface for POSTURE."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .core import (
    PostureError,
    clear_active,
    find_repo_root,
    list_postures,
    render_active,
    set_active,
    show_active,
)
from .hook import main as hook_main
from .integration import bootstrap_repo, install_providers


def _root(value: str | None) -> Path:
    return find_repo_root(value)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="posture",
        description="Anchor an AI agent's operating posture at repository scope.",
    )
    parser.add_argument(
        "--repo",
        help="Path inside the target Git repository. Defaults to the current directory.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    set_parser = sub.add_parser("set", help="Set and snapshot an active posture.")
    set_parser.add_argument("name")

    sub.add_parser("clear", help="Clear the active posture.")
    sub.add_parser("show", help="Show the active posture and definition drift.")
    sub.add_parser("list", help="List available postures.")
    sub.add_parser("render", help="Render canonical context for the active posture.")
    sub.add_parser(
        "bootstrap",
        help="Initialize repository-local POSTURE state without agent integrations.",
    )

    install_parser = sub.add_parser(
        "install",
        help="Install POSTURE hooks and skills into an already-bootstrapped repository.",
    )
    install_parser.add_argument(
        "--provider",
        action="append",
        choices=("claude", "codex"),
        dest="providers",
        help="Provider to integrate. Repeat to select several. Defaults to both.",
    )

    sub.add_parser("hook", help=argparse.SUPPRESS)
    return parser


def _print_changes(changes: list[object]) -> None:
    for change in changes:
        print(f"{change.action}: {change.path}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        root = _root(args.repo)

        if args.command == "set":
            active = set_active(args.name, root)
            print(f"POSTURE set: {active.name} ({active.sha256[:12]})")
            return 0

        if args.command == "clear":
            cleared = clear_active(root)
            print("POSTURE cleared." if cleared else "POSTURE already clear.")
            return 0

        if args.command == "show":
            status = show_active(root)
            if status is None:
                print("POSTURE: none")
                return 0
            print(f"POSTURE: {status['name']}")
            print(f"sha256:  {status['sha256']}")
            print(f"source:  {status['source']}")
            print(f"drifted: {'yes' if status['drifted'] else 'no'}")
            print()
            print(status["body"])
            return 0

        if args.command == "list":
            for definition in list_postures(root):
                print(f"{definition.name}\t{definition.source}\t{definition.sha256[:12]}")
            return 0

        if args.command == "render":
            rendered = render_active(root)
            if rendered:
                print(rendered)
            return 0

        if args.command == "bootstrap":
            _print_changes(bootstrap_repo(root))
            print("POSTURE repository state initialized.")
            return 0

        if args.command == "install":
            providers = args.providers or ["claude", "codex"]
            _print_changes(install_providers(root, providers))
            print("POSTURE provider integration installed.")
            return 0

        if args.command == "hook":
            return hook_main(root)

    except PostureError as exc:
        print(f"posture: {exc}", file=sys.stderr)
        return 2

    parser.error(f"unsupported command: {args.command}")
    return 2
