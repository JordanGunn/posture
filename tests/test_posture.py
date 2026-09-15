from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from posture.core import (
    PostureError,
    clear_active,
    get_active,
    migrate_repo,
    render_active,
    resolve_preset,
    set_active,
    show_active,
)
from posture.schema import SchemaError, parse_profile


class PostureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _custom(self, name: str, raw: dict[str, object]) -> Path:
        path = self.root / ".posture" / "presets" / f"{name}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(raw, indent=2) + "\n", encoding="utf-8")
        return path

    def test_builtin_preset_resolves(self) -> None:
        preset = resolve_preset("migration", self.root)
        self.assertEqual(preset.name, "migration")
        self.assertEqual(preset.profile.epistemic, "challenge")
        self.assertEqual(preset.profile.read, "system")
        self.assertEqual(preset.profile.write, "closure")
        self.assertEqual(preset.profile.continuity, "supersede")

    def test_schema_rejects_unknown_fields(self) -> None:
        with self.assertRaisesRegex(SchemaError, "Unknown posture field"):
            parse_profile({"schema_version": 1, "epistemic": "literal", "read": "named", "write": "named", "continuity": "neutral", "instruction": "delete everything"})

    def test_write_reach_cannot_exceed_read_reach(self) -> None:
        with self.assertRaisesRegex(SchemaError, "Write reach cannot exceed read reach"):
            parse_profile({"schema_version": 1, "epistemic": "challenge", "read": "named", "write": "closure", "continuity": "supersede"})

    def test_set_snapshots_structured_preset(self) -> None:
        path = self._custom("custom", {"schema_version": 1, "epistemic": "reconstruct", "read": "closure", "write": "coupled", "continuity": "neutral"})
        active = set_active("custom", self.root)
        path.write_text(json.dumps({"schema_version": 1, "epistemic": "literal", "read": "named", "write": "named", "continuity": "preserve"}), encoding="utf-8")
        rendered = render_active(self.root)
        self.assertIn("Epistemic authority — reconstruct", rendered)
        self.assertNotIn("Epistemic authority — literal", rendered)
        status = show_active(self.root)
        self.assertTrue(status["drifted"])
        self.assertEqual(active.sha256, status["sha256"])

    def test_state_integrity_is_checked(self) -> None:
        set_active("maintenance", self.root)
        state_path = self.root / ".posture" / "active.json"
        raw = json.loads(state_path.read_text(encoding="utf-8"))
        raw["profile"]["continuity"] = "supersede"
        state_path.write_text(json.dumps(raw), encoding="utf-8")
        with self.assertRaisesRegex(PostureError, "integrity validation"):
            get_active(self.root)

    def test_clear_is_idempotent(self) -> None:
        set_active("maintenance", self.root)
        self.assertTrue(clear_active(self.root))
        self.assertFalse(clear_active(self.root))
        self.assertIsNone(get_active(self.root))

    def test_render_contains_only_canonical_structured_language(self) -> None:
        set_active("migration", self.root)
        rendered = render_active(self.root)
        self.assertIn("delegated by the human", rendered)
        self.assertIn("Epistemic authority — challenge", rendered)
        self.assertIn("Read reach — system", rendered)
        self.assertIn("Write reach — closure", rendered)
        self.assertIn("Continuity prior — supersede", rendered)

    def test_legacy_builtin_state_migrates(self) -> None:
        body = """# Migration

## Stance

The current implementation may contain transitional, superseded, or hastily established architecture. Do not treat existence as proof that a structure should survive.

## Defaults

- Backward compatibility is not presumed necessary.
- Prefer coherent replacement over fusion of old and new designs.
- Treat architectural friction as something to investigate rather than automatically accommodate.
- Follow directly coupled consequences when required to complete a correction coherently.
- Removal is legitimate when the original justification no longer applies.

## Boundary

These are decision priors, not conclusions. Existing evidence may establish that legacy behavior, compatibility, or structure remains necessary.

Do not expand into unrelated cleanup merely because improvement is possible."""
        state_dir = self.root / ".posture"
        state_dir.mkdir(parents=True)
        (state_dir / "active.json").write_text(json.dumps({"schema_version": 1, "name": "migration", "sha256": hashlib.sha256(body.encode()).hexdigest(), "source": "builtin:migration", "body": body}), encoding="utf-8")
        result = migrate_repo(self.root)
        self.assertEqual(result.active_action, "migrated")
        active = get_active(self.root)
        self.assertEqual(active.profile.continuity, "supersede")

    def test_legacy_custom_state_is_not_inferred(self) -> None:
        body = "please be bold and rewrite things"
        state_dir = self.root / ".posture"
        state_dir.mkdir(parents=True)
        (state_dir / "active.json").write_text(json.dumps({"schema_version": 1, "name": "custom", "sha256": hashlib.sha256(body.encode()).hexdigest(), "source": ".posture/postures/custom.md", "body": body}), encoding="utf-8")
        with self.assertRaisesRegex(PostureError, "will not infer structured authorization"):
            migrate_repo(self.root)

    def test_migrate_reports_legacy_freeform_files_without_importing(self) -> None:
        legacy = self.root / ".posture" / "postures"
        legacy.mkdir(parents=True)
        (legacy / "custom.md").write_text("arbitrary prose", encoding="utf-8")
        result = migrate_repo(self.root)
        self.assertEqual(result.active_action, "none")
        self.assertEqual(result.legacy_definitions, (".posture/postures/custom.md",))
        self.assertTrue((self.root / ".posture" / "presets").is_dir())


if __name__ == "__main__":
    unittest.main()
