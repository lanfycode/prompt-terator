"""
File-system storage for Prompt content (and Phase 2 artefacts).

Each Prompt version is persisted as an individual Markdown file under:
  data/prompts/<prompt_id>/v<version>.md

This keeps metadata (in SQLite) separate from content (plain files),
making content human-readable and easy to back up or audit.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import config as _config
from utils.logger import get_logger

logger = get_logger(__name__)


class PromptStorage:
    """Read/write Prompt version content on the local file system."""

    def __init__(self) -> None:
        _config.ensure_data_dirs()

    # ── Public API ────────────────────────────────────────────────────────────

    def save(self, prompt_id: str, version: int, content: str) -> str:
        """
        Write *content* to the canonical path for this version.

        Returns the absolute path as a string (stored in prompt_versions.file_path).
        """
        path = self._version_path(prompt_id, version)
        path.write_text(content, encoding="utf-8")
        logger.debug("Saved prompt content → %s", path)
        return str(path)

    def load(self, file_path: str) -> Optional[str]:
        """Read and return the content at *file_path*, or None if missing."""
        path = Path(file_path)
        if not path.exists():
            logger.warning("Prompt file not found: %s", path)
            return None
        return path.read_text(encoding="utf-8")

    def delete(self, file_path: str) -> None:
        path = Path(file_path)
        if path.exists():
            path.unlink()
            logger.debug("Deleted prompt file: %s", path)

    # ── Private ───────────────────────────────────────────────────────────────

    def _version_path(self, prompt_id: str, version: int) -> Path:
        prompt_dir = _config.PROMPTS_DIR / prompt_id
        prompt_dir.mkdir(parents=True, exist_ok=True)
        return prompt_dir / f"v{version}.md"
