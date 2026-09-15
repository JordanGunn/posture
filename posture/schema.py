"""Bounded POSTURE schema and canonical rendering semantics."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Mapping

PROFILE_SCHEMA_VERSION = 1

EPISTEMIC_LEVELS = ("literal", "complete", "challenge", "reconstruct")
READ_LEVELS = ("named", "adjacent", "closure", "system")
WRITE_LEVELS = ("named", "coupled", "closure", "systemic")
CONTINUITY_LEVELS = ("preserve", "neutral", "supersede")

READ_RANK = {name: rank for rank, name in enumerate(READ_LEVELS)}
WRITE_RANK = {name: rank for rank, name in enumerate(WRITE_LEVELS)}

AXIS_TEXT: dict[str, dict[str, str]] = {
    "epistemic": {
        "literal": (
            "Treat the human's technical framing and terminology as authoritative. "
            "Do not reinterpret the problem beyond what is required to execute it safely."
        ),
        "complete": (
            "Fill routine omissions and implementation gaps, but preserve the human's "
            "conceptual model unless direct evidence makes it untenable."
        ),
        "challenge": (
            "Material contradictions, mistaken assumptions, and misleading terminology are "
            "within scope to surface and correct when evidence warrants it."
        ),
        "reconstruct": (
            "Treat the human's articulation as evidence of intent rather than an authoritative "
            "model. When necessary, reconstruct a more coherent underlying problem before acting."
        ),
    },
    "read": {
        "named": (
            "Inspect only the named scope and the minimum context required to operate within it."
        ),
        "adjacent": (
            "Inspect immediate dependencies, dependents, and neighboring context needed to "
            "understand the named scope."
        ),
        "closure": (
            "Follow materially relevant dependency and coupling chains until the decision surface "
            "is coherent."
        ),
        "system": (
            "Inspect project- or system-wide context wherever it is materially relevant to the "
            "decision."
        ),
    },
    "write": {
        "named": "Modify only the explicitly named scope.",
        "coupled": (
            "May modify directly coupled artifacts when required to complete the named change "
            "coherently."
        ),
        "closure": (
            "May propagate changes through the relevant dependency closure when required for "
            "architectural or behavioral coherence."
        ),
        "systemic": (
            "May propagate changes system-wide until the relevant invariant is restored. "
            "This does not authorize unrelated cleanup."
        ),
    },
    "continuity": {
        "preserve": (
            "Existing behavior and structure have a positive preservation prior. Treat compatibility "
            "as presumptively valuable unless evidence or an explicit requirement says otherwise."
        ),
        "neutral": (
            "Existing state receives no special preservation or replacement weight solely because "
            "it already exists."
        ),
        "supersede": (
            "Existing state may be transitional or superseded. Do not preserve compatibility or "
            "architecture solely because it exists; prefer coherent replacement when evidence "
            "supports supersession."
        ),
    },
}


class SchemaError(ValueError):
    """Raised when a posture profile violates the bounded schema."""


@dataclass(frozen=True)
class Profile:
    epistemic: str
    read: str
    write: str
    continuity: str
    schema_version: int = PROFILE_SCHEMA_VERSION

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "epistemic": self.epistemic,
            "read": self.read,
            "write": self.write,
            "continuity": self.continuity,
        }

    @property
    def sha256(self) -> str:
        payload = json.dumps(self.as_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def parse_profile(raw: Mapping[str, object]) -> Profile:
    """Validate and construct a bounded posture profile."""
    allowed = {"schema_version", "epistemic", "read", "write", "continuity"}
    unknown = set(raw) - allowed
    if unknown:
        raise SchemaError(f"Unknown posture field(s): {', '.join(sorted(unknown))}")

    if raw.get("schema_version") != PROFILE_SCHEMA_VERSION:
        raise SchemaError(
            f"Unsupported posture profile schema: {raw.get('schema_version')!r}"
        )

    values: dict[str, str] = {}
    domains = {
        "epistemic": EPISTEMIC_LEVELS,
        "read": READ_LEVELS,
        "write": WRITE_LEVELS,
        "continuity": CONTINUITY_LEVELS,
    }
    for field, domain in domains.items():
        value = raw.get(field)
        if not isinstance(value, str) or value not in domain:
            raise SchemaError(
                f"Invalid {field!r}: {value!r}. Expected one of: {', '.join(domain)}"
            )
        values[field] = value

    if WRITE_RANK[values["write"]] > READ_RANK[values["read"]]:
        raise SchemaError(
            "Write reach cannot exceed read reach. The agent must be allowed to inspect "
            "at least as far as it may modify."
        )

    return Profile(**values)


def render_profile(profile: Profile) -> str:
    """Compile a bounded profile into canonical agent-facing language."""
    return "\n".join(
        [
            f"Epistemic authority — {profile.epistemic}:",
            AXIS_TEXT["epistemic"][profile.epistemic],
            "",
            f"Read reach — {profile.read}:",
            AXIS_TEXT["read"][profile.read],
            "",
            f"Write reach — {profile.write}:",
            AXIS_TEXT["write"][profile.write],
            "",
            f"Continuity prior — {profile.continuity}:",
            AXIS_TEXT["continuity"][profile.continuity],
        ]
    )
