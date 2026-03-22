"""
Unit tests for PromptService.

The LLMClient is mocked so no real API calls are made.
Storage uses a temporary directory; DB uses a temporary SQLite file.
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestPromptService(unittest.TestCase):

    def setUp(self):
        # Redirect DB and storage paths
        import config as cfg
        self._tmp_db  = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self._tmp_dir = tempfile.mkdtemp()
        cfg.DB_PATH     = Path(self._tmp_db.name)
        cfg.PROMPTS_DIR = Path(self._tmp_dir)

        from repositories.database import initialize_db
        initialize_db()

        # Build a mock LLMClient
        from llm.client import LLMResponse
        self._mock_client = MagicMock()
        self._mock_client.generate.return_value = LLMResponse(
            text="## Role\nYou are a helpful assistant.\n\n## Objective\nHelp users.",
            model_name="gemini-2.5-flash",
            temperature=0.7,
            prompt_tokens=50,
            output_tokens=30,
            latency_ms=300.0,
        )

        from services.prompt_service import PromptService
        self.service = PromptService(llm_client=self._mock_client)

    def tearDown(self):
        self._tmp_db.close()
        os.unlink(self._tmp_db.name)

    # ── Generation ────────────────────────────────────────────────────────────

    def test_generate_prompt_returns_text(self):
        text, resp = self.service.generate_prompt(
            requirement="An email writing assistant",
            model_name="gemini-2.5-flash",
        )
        self.assertIn("Role", text)
        self.assertEqual(resp.model_name, "gemini-2.5-flash")

    def test_generate_prompt_empty_requirement_raises(self):
        with self.assertRaises(ValueError):
            self.service.generate_prompt(requirement="  ", model_name="gemini-2.5-flash")

    # ── Persistence ───────────────────────────────────────────────────────────

    def test_save_new_prompt_creates_record(self):
        prompt, version = self.service.save_new_prompt(
            name="Email Assistant",
            content="## Role\nYou are an email writer.",
            model_name="gemini-2.5-flash",
        )
        self.assertEqual(prompt.name, "Email Assistant")
        self.assertEqual(version.version, 1)
        self.assertTrue(Path(version.file_path).exists())

    def test_save_new_version_increments_version(self):
        prompt, v1 = self.service.save_new_prompt(
            name="Email Assistant",
            content="Version 1 content",
        )
        prompt2, v2 = self.service.save_new_version(
            prompt_id=prompt.id,
            content="Version 2 content",
            source_type="optimized",
        )
        self.assertEqual(v2.version, 2)
        self.assertEqual(prompt2.current_version, 2)

    # ── Retrieval ─────────────────────────────────────────────────────────────

    def test_list_prompts(self):
        self.service.save_new_prompt(name="P1", content="c1")
        self.service.save_new_prompt(name="P2", content="c2")
        prompts = self.service.list_prompts()
        # At least 2 prompts must exist (isolation via temp DB per test)
        self.assertGreaterEqual(len(prompts), 2)

    def test_get_latest_version_with_content(self):
        prompt, _ = self.service.save_new_prompt(name="Test", content="Hello World")
        version   = self.service.get_latest_version_with_content(prompt.id)
        self.assertIsNotNone(version)
        self.assertEqual(version.content, "Hello World")

    def test_list_versions(self):
        prompt, _ = self.service.save_new_prompt(name="Test", content="v1")
        self.service.save_new_version(
            prompt_id=prompt.id, content="v2", source_type="optimized"
        )
        versions = self.service.list_versions(prompt.id)
        self.assertEqual(len(versions), 2)

    def test_save_new_version_nonexistent_prompt_raises(self):
        with self.assertRaises(ValueError):
            self.service.save_new_version(
                prompt_id="nonexistent-id", content="x", source_type="manual"
            )


if __name__ == "__main__":
    unittest.main()
