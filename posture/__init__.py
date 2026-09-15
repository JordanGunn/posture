"""POSTURE: anchored operating stance for AI agents."""

from .core import (
    PostureError,
    clear_active,
    get_active,
    list_postures,
    render_active,
    set_active,
    show_active,
)

__all__ = [
    "PostureError",
    "clear_active",
    "get_active",
    "list_postures",
    "render_active",
    "set_active",
    "show_active",
]

__version__ = "0.1.0"
