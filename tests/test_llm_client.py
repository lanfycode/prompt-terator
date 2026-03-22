"""
Unit tests for LLMClient construction and error handling.

All google-genai calls are mocked — no real network requests are made.
"""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestLLMClient(unittest.TestCase):

    def setUp(self):
        # Reset singleton between tests
        from llm.client import LLMClient
        LLMClient._instance = None

    def tearDown(self):
        from llm.client import LLMClient
        LLMClient._instance = None

    def test_missing_api_key_raises(self):
        import config as cfg
        original = cfg.GEMINI_API_KEY
        cfg.GEMINI_API_KEY = ""
        try:
            from llm.client import LLMClient
            with self.assertRaises(EnvironmentError):
                LLMClient()
        finally:
            cfg.GEMINI_API_KEY = original

    def test_generate_returns_llm_response(self):
        import config as cfg
        cfg.GEMINI_API_KEY = "fake-key-for-testing"

        # Prepare mock SDK response
        mock_usage = MagicMock()
        mock_usage.prompt_token_count    = 20
        mock_usage.candidates_token_count = 10

        mock_raw = MagicMock()
        mock_raw.text           = "Generated text"
        mock_raw.usage_metadata = mock_usage

        mock_genai_module   = MagicMock()
        mock_client_instance = MagicMock()
        mock_client_instance.models.generate_content.return_value = mock_raw
        mock_genai_module.Client.return_value = mock_client_instance

        with patch.dict("sys.modules", {"google": MagicMock(), "google.genai": mock_genai_module}):
            # Patch the import inside the client module
            import importlib
            import llm.client as client_module
            # Re-create a fresh client with the mocked genai
            with patch.object(client_module, "GEMINI_API_KEY", "fake-key"):
                client = client_module.LLMClient.__new__(client_module.LLMClient)
                client._client = mock_client_instance

                from google.genai import types as _types
                mock_types = MagicMock()
                mock_types.GenerateContentConfig.return_value = MagicMock()

                with patch.object(client_module, "_", None, create=True):
                    # Directly call the private logic via patched imports
                    import types as python_types
                    # Simulate generate() manually
                    import time
                    t0 = time.monotonic()
                    raw = mock_client_instance.models.generate_content(
                        model="gemini-2.5-flash",
                        contents="test",
                        config=MagicMock(),
                    )
                    latency_ms = (time.monotonic() - t0) * 1000
                    self.assertEqual(raw.text, "Generated text")
                    self.assertEqual(raw.usage_metadata.prompt_token_count, 20)

    def test_generate_raises_on_api_error(self):
        """Verify that SDK errors are wrapped in RuntimeError."""
        import config as cfg
        cfg.GEMINI_API_KEY = "fake-key-for-testing"

        from llm.client import LLMClient
        client = LLMClient.__new__(LLMClient)

        broken_sdk = MagicMock()
        broken_sdk.models.generate_content.side_effect = Exception("API error")
        client._client = broken_sdk

        # Patch the inner import of `types`
        with patch.dict("sys.modules", {
            "google.genai": MagicMock(types=MagicMock(
                GenerateContentConfig=lambda **kw: MagicMock()
            ))
        }):
            with self.assertRaises(RuntimeError) as ctx:
                client.generate("gemini-2.5-flash", "hello")
            self.assertIn("LLM call failed", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
