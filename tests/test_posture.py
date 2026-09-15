from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from posture.core import (
    PostureError,
    clear_active,
    get_active,
    render_active,
    resolve_definition,
    set_active,
    show_active,
)


class PostureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _custom(self, name: str, body: str) -> Path:
        path = self.root / ".posture" / "postures" / f"{name}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        return path

    def test_builtin_definition_resolves(self) -> None:
        definition = resolve_definition("migration", self.root)
        self.assertEqual(definition.name, "migration")
        self.assertIn("Backward compatibility is not presumed", definition.body)

    def test_set_snapshots_definition(self) -> None:
        path = self._custom("custom", "First stance.")
        active = set_active("custom", self.root)
        path.write_text("Changed stance.", encoding="utf-8")

        rendered = render_active(self.root)
        self.assertIsNotNone(rendered)
        self.assertIn("First stance.", rendered)
        self.assertNotIn("Changed stance.", rendered)

        status = show_active(self.root)
        self.assertIsNotNone(status)
        self.assertTrue(status["drifted"])
        self.assertEqual(active.sha256, status["sha256"])

    def test_state_integrity_is_checked(self) -> None:
        self._custom("custom", "Stable stance.")
        set_active("custom", self.root)
        state_path = self.root / ".posture" / "active.json"
        raw = json.loads(state_path.read_text(encoding="utf-8"))
        raw["body"] = "tampered"
        state_path.write_text(json.dumps(raw), encoding="utf-8")

        with self.assertRaises(PostureError):
            get_active(self.root)

    def test_clear_is_idempotent(self) -> None:
        set_active("maintenance", self.root)
        self.assertTrue(clear_active(self.root))
        self.assertFalse(clear_active(self.root))
        self.assertIsNone(get_active(self.root))

    def test_render_includes_runtime_contract(self) -> None:
        set_active("migration", self.root)
        rendered = render_active(self.root)
        self.assertIn("persistent operating prior", rendered)
        self.assertIn("Explicit current requirements", rendered)
        self.assertIn('<POSTURE name="migration"', rendered)


if __name__ == "__main__":
    unittest.main()
