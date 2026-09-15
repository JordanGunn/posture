from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from posture.core import PostureError
from posture.integration import bootstrap_repo, install_providers, is_bootstrapped


class IntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_bootstrap_is_idempotent(self) -> None:
        first = bootstrap_repo(self.root)
        second = bootstrap_repo(self.root)

        self.assertEqual(first[0].action, "created")
        self.assertEqual(second[0].action, "unchanged")
        self.assertTrue(is_bootstrapped(self.root))
        self.assertEqual(
            (self.root / ".posture" / ".gitignore").read_text(encoding="utf-8"),
            "active.json\n",
        )
        self.assertTrue((self.root / ".posture" / "postures").is_dir())

    def test_install_requires_bootstrap(self) -> None:
        with self.assertRaisesRegex(PostureError, "posture bootstrap"):
            install_providers(self.root)

    def test_install_merges_existing_config_and_is_idempotent(self) -> None:
        bootstrap_repo(self.root)
        settings = self.root / ".claude" / "settings.json"
        settings.parent.mkdir(parents=True)
        settings.write_text(
            json.dumps({"permissions": {"allow": ["Bash(git status)"]}}, indent=2)
            + "\n",
            encoding="utf-8",
        )

        install_providers(self.root)
        install_providers(self.root)

        merged = json.loads(settings.read_text(encoding="utf-8"))
        self.assertEqual(merged["permissions"]["allow"], ["Bash(git status)"])
        entries = merged["hooks"]["UserPromptSubmit"]
        commands = [
            hook["command"]
            for entry in entries
            for hook in entry.get("hooks", [])
            if isinstance(hook, dict)
        ]
        self.assertEqual(
            commands.count('cd "$CLAUDE_PROJECT_DIR" && posture hook'),
            1,
        )

        codex = json.loads(
            (self.root / ".codex" / "hooks.json").read_text(encoding="utf-8")
        )
        codex_hook = codex["hooks"]["UserPromptSubmit"][0]["hooks"][0]
        self.assertEqual(
            codex_hook["command"],
            'cd "$(git rev-parse --show-toplevel)" && posture hook',
        )
        self.assertEqual(codex_hook["additionalContextLimit"], 1200)

    def test_install_preflights_owned_skill_conflicts(self) -> None:
        bootstrap_repo(self.root)
        skill = self.root / ".claude" / "skills" / "posture" / "SKILL.md"
        skill.parent.mkdir(parents=True)
        skill.write_text("foreign skill\n", encoding="utf-8")

        with self.assertRaisesRegex(PostureError, "Refusing to overwrite"):
            install_providers(self.root, ["claude"])

        self.assertFalse((self.root / ".claude" / "settings.json").exists())


if __name__ == "__main__":
    unittest.main()
