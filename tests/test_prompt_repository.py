"""
Unit tests for PromptRepository.

Uses an in-memory (temp-file) SQLite database so no real data is touched.
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

# Ensure project root is on sys.path when running tests directly
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestPromptRepository(unittest.TestCase):

    def setUp(self):
        # Redirect DB to a temporary file for isolation
        import config as cfg
        self._tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        cfg.DB_PATH = Path(self._tmp.name)

        from repositories.database import initialize_db
        initialize_db()

        from repositories.prompt_repository import PromptRepository
        self.repo = PromptRepository()

    def tearDown(self):
        self._tmp.close()
        os.unlink(self._tmp.name)

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _now():
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _uid():
        import uuid
        return str(uuid.uuid4())

    def _make_prompt(self, name: str = "Test Prompt"):
        from models.prompt import Prompt
        now = self._now()
        return Prompt(
            id=self._uid(),
            name=name,
            description="A test prompt",
            current_version=1,
            created_at=now,
            updated_at=now,
        )

    def _make_version(self, prompt_id: str):
        from models.prompt import PromptVersion
        return PromptVersion(
            id=self._uid(),
            prompt_id=prompt_id,
            version=1,
            source_type="generated",
            parent_version_id=None,
            model_name="gemini-2.5-flash",
            file_path="/tmp/test_v1.md",
            summary="Initial version",
            created_at=self._now(),
        )

    # ── Tests ─────────────────────────────────────────────────────────────────

    def test_create_and_get_prompt(self):
        prompt = self._make_prompt()
        self.repo.create_prompt(prompt)
        retrieved = self.repo.get_prompt(prompt.id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "Test Prompt")
        self.assertEqual(retrieved.current_version, 1)

    def test_list_prompts_empty(self):
        self.assertEqual(self.repo.list_prompts(), [])

    def test_list_prompts_returns_items(self):
        self.repo.create_prompt(self._make_prompt("P1"))
        result = self.repo.list_prompts()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "P1")

    def test_update_prompt(self):
        prompt = self._make_prompt()
        self.repo.create_prompt(prompt)
        prompt.name = "Updated Name"
        prompt.current_version = 2
        self.repo.update_prompt(prompt)
        updated = self.repo.get_prompt(prompt.id)
        self.assertEqual(updated.name, "Updated Name")
        self.assertEqual(updated.current_version, 2)

    def test_create_and_get_version(self):
        prompt = self._make_prompt()
        self.repo.create_prompt(prompt)
        version = self._make_version(prompt.id)
        self.repo.create_version(version)
        retrieved = self.repo.get_version(version.id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.version, 1)
        self.assertEqual(retrieved.source_type, "generated")

    def test_list_versions(self):
        prompt = self._make_prompt()
        self.repo.create_prompt(prompt)
        self.repo.create_version(self._make_version(prompt.id))
        versions = self.repo.list_versions(prompt.id)
        self.assertEqual(len(versions), 1)

    def test_get_latest_version(self):
        from models.prompt import PromptVersion
        prompt = self._make_prompt()
        self.repo.create_prompt(prompt)
        v1 = self._make_version(prompt.id)
        self.repo.create_version(v1)
        v2 = PromptVersion(
            id=self._uid(),
            prompt_id=prompt.id,
            version=2,
            source_type="optimized",
            parent_version_id=v1.id,
            model_name="gemini-2.5-pro",
            file_path="/tmp/test_v2.md",
            summary="Optimised",
            created_at=self._now(),
        )
        self.repo.create_version(v2)
        latest = self.repo.get_latest_version(prompt.id)
        self.assertEqual(latest.version, 2)

    def test_get_prompt_returns_none_for_missing(self):
        self.assertIsNone(self.repo.get_prompt("nonexistent"))


if __name__ == "__main__":
    unittest.main()
