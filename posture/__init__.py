"""POSTURE: bounded delegated standing for AI agents."""

from .core import (
    PostureError,
    clear_active,
    get_active,
    list_presets,
    migrate_repo,
    render_active,
    set_active,
    show_active,
)
from .schema import Profile, SchemaError

__all__ = [
    "PostureError",
    "Profile",
    "SchemaError",
    "clear_active",
    "get_active",
    "list_presets",
    "migrate_repo",
    "render_active",
    "set_active",
    "show_active",
]

__version__ = "0.2.0"
