"""
Repository for Prompt and PromptVersion CRUD operations.

All database interaction for Prompt management is encapsulated here so
that services never touch SQL directly.
"""
from __future__ import annotations

import sqlite3
from typing import List, Optional

from models.prompt import Prompt, PromptVersion
from repositories.database import get_connection
from utils.logger import get_logger

logger = get_logger(__name__)


class PromptRepository:

    # ── Prompt ────────────────────────────────────────────────────────────────

    def create_prompt(self, prompt: Prompt) -> Prompt:
        sql = """
            INSERT INTO prompts
                (id, name, description, current_version, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        with get_connection() as conn:
            conn.execute(sql, (
                prompt.id, prompt.name, prompt.description,
                prompt.current_version, prompt.created_at, prompt.updated_at,
            ))
            conn.commit()
        logger.debug("Created prompt  id=%s  name=%s", prompt.id, prompt.name)
        return prompt

    def update_prompt(self, prompt: Prompt) -> Prompt:
        sql = """
            UPDATE prompts
            SET name=?, description=?, current_version=?, updated_at=?
            WHERE id=?
        """
        with get_connection() as conn:
            conn.execute(sql, (
                prompt.name, prompt.description,
                prompt.current_version, prompt.updated_at, prompt.id,
            ))
            conn.commit()
        return prompt

    def get_prompt(self, prompt_id: str) -> Optional[Prompt]:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM prompts WHERE id=?", (prompt_id,)
            ).fetchone()
        return _row_to_prompt(row) if row else None

    def list_prompts(self) -> List[Prompt]:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM prompts ORDER BY updated_at DESC"
            ).fetchall()
        return [_row_to_prompt(r) for r in rows]

    # ── PromptVersion ─────────────────────────────────────────────────────────

    def create_version(self, version: PromptVersion) -> PromptVersion:
        sql = """
            INSERT INTO prompt_versions
                (id, prompt_id, version, source_type, parent_version_id,
                 model_name, file_path, summary, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        with get_connection() as conn:
            conn.execute(sql, (
                version.id, version.prompt_id, version.version,
                version.source_type, version.parent_version_id,
                version.model_name, version.file_path,
                version.summary, version.created_at,
            ))
            conn.commit()
        logger.debug(
            "Created version  id=%s  prompt_id=%s  v=%d",
            version.id, version.prompt_id, version.version,
        )
        return version

    def get_version(self, version_id: str) -> Optional[PromptVersion]:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM prompt_versions WHERE id=?", (version_id,)
            ).fetchone()
        return _row_to_version(row) if row else None

    def list_versions(self, prompt_id: str) -> List[PromptVersion]:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM prompt_versions WHERE prompt_id=? ORDER BY version ASC",
                (prompt_id,),
            ).fetchall()
        return [_row_to_version(r) for r in rows]

    def get_latest_version(self, prompt_id: str) -> Optional[PromptVersion]:
        with get_connection() as conn:
            row = conn.execute(
                """SELECT * FROM prompt_versions
                   WHERE prompt_id=?
                   ORDER BY version DESC LIMIT 1""",
                (prompt_id,),
            ).fetchone()
        return _row_to_version(row) if row else None


# ── Private helpers ───────────────────────────────────────────────────────────

def _row_to_prompt(row: sqlite3.Row) -> Prompt:
    return Prompt(
        id=row["id"],
        name=row["name"],
        description=row["description"],
        current_version=row["current_version"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_version(row: sqlite3.Row) -> PromptVersion:
    return PromptVersion(
        id=row["id"],
        prompt_id=row["prompt_id"],
        version=row["version"],
        source_type=row["source_type"],
        parent_version_id=row["parent_version_id"],
        model_name=row["model_name"],
        file_path=row["file_path"],
        summary=row["summary"],
        created_at=row["created_at"],
    )
