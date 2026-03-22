"""
PromptService — core business logic for Prompt lifecycle management.

Responsibilities:
  - Generate a prompt from a requirement (via PromptGeneratorAgent).
  - Optimise an existing prompt (via PromptOptimizerAgent).
  - Persist prompts and their versions (via Repository + Storage).
  - Retrieve prompts and load their content.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from agents.prompt_generator_agent import PromptGeneratorAgent
from agents.prompt_optimizer_agent import PromptOptimizerAgent
from llm.client import LLMClient, LLMResponse
from models.prompt import Prompt, PromptVersion, SourceType
from repositories.prompt_repository import PromptRepository
from storage.prompt_storage import PromptStorage
from utils.logger import get_logger

logger = get_logger(__name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class PromptService:

    def __init__(
        self,
        llm_client:  Optional[LLMClient]          = None,
        repository:  Optional[PromptRepository]   = None,
        storage:     Optional[PromptStorage]       = None,
    ) -> None:
        self._client    = llm_client or LLMClient.get_instance()
        self._repo      = repository or PromptRepository()
        self._storage   = storage    or PromptStorage()
        self._generator = PromptGeneratorAgent(self._client)
        self._optimizer = PromptOptimizerAgent(self._client)

    # ── Generation ────────────────────────────────────────────────────────────

    def generate_prompt(
        self,
        requirement: str,
        model_name:  str,
        temperature: float = 0.7,
    ) -> Tuple[str, LLMResponse]:
        """
        Call the PromptGeneratorAgent.

        Returns (generated_text, raw_response).
        Does NOT persist — the caller decides whether to save.
        """
        response = self._generator.generate(
            requirement=requirement,
            model_name=model_name,
            temperature=temperature,
        )
        return response.text, response

    # ── Optimisation ──────────────────────────────────────────────────────────

    def optimize_prompt(
        self,
        original_prompt:      str,
        optimization_request: str,
        model_name:           str,
        temperature:          float = 0.7,
        analysis_context:     Optional[str] = None,
    ) -> Tuple[str, LLMResponse]:
        """
        Call the PromptOptimizerAgent.

        Returns (optimised_text, raw_response).
        Does NOT persist — the caller decides whether to save.
        """
        response = self._optimizer.optimize(
            original_prompt=original_prompt,
            optimization_request=optimization_request,
            model_name=model_name,
            temperature=temperature,
            analysis_context=analysis_context,
        )
        return response.text, response

    # ── Persistence ───────────────────────────────────────────────────────────

    def save_new_prompt(
        self,
        name:        str,
        content:     str,
        source_type: str = SourceType.MANUAL,
        model_name:  Optional[str] = None,
        summary:     str = "",
        description: str = "",
    ) -> Tuple[Prompt, PromptVersion]:
        """Create a brand-new Prompt with version 1."""
        now = _now()
        prompt = Prompt(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            current_version=1,
            created_at=now,
            updated_at=now,
        )
        self._repo.create_prompt(prompt)

        file_path = self._storage.save(prompt.id, 1, content)
        version = PromptVersion(
            id=str(uuid.uuid4()),
            prompt_id=prompt.id,
            version=1,
            source_type=source_type,
            parent_version_id=None,
            model_name=model_name,
            file_path=file_path,
            summary=summary or f"Initial version ({source_type})",
            created_at=now,
            content=content,
        )
        self._repo.create_version(version)
        logger.info("Saved new prompt '%s' (id=%s)", name, prompt.id)
        return prompt, version

    def save_new_version(
        self,
        prompt_id:        str,
        content:          str,
        source_type:      str,
        model_name:       Optional[str] = None,
        parent_version_id: Optional[str] = None,
        summary:          str = "",
    ) -> Tuple[Prompt, PromptVersion]:
        """Append a new immutable version to an existing Prompt."""
        prompt = self._repo.get_prompt(prompt_id)
        if not prompt:
            raise ValueError(f"Prompt not found: {prompt_id}")

        new_v = prompt.current_version + 1
        now   = _now()

        file_path = self._storage.save(prompt_id, new_v, content)
        version   = PromptVersion(
            id=str(uuid.uuid4()),
            prompt_id=prompt_id,
            version=new_v,
            source_type=source_type,
            parent_version_id=parent_version_id,
            model_name=model_name,
            file_path=file_path,
            summary=summary or f"Version {new_v} ({source_type})",
            created_at=now,
            content=content,
        )
        self._repo.create_version(version)
        prompt.current_version = new_v
        prompt.updated_at      = now
        self._repo.update_prompt(prompt)
        logger.info(
            "Appended version v%d to prompt '%s'", new_v, prompt.name
        )
        return prompt, version

    # ── Retrieval ─────────────────────────────────────────────────────────────

    def list_prompts(self) -> List[Prompt]:
        return self._repo.list_prompts()

    def get_prompt(self, prompt_id: str) -> Optional[Prompt]:
        return self._repo.get_prompt(prompt_id)

    def list_versions(self, prompt_id: str) -> List[PromptVersion]:
        return self._repo.list_versions(prompt_id)

    def get_version_with_content(self, version_id: str) -> Optional[PromptVersion]:
        version = self._repo.get_version(version_id)
        if version and version.content is None:
            version.content = self._storage.load(version.file_path)
        return version

    def get_latest_version_with_content(
        self, prompt_id: str
    ) -> Optional[PromptVersion]:
        version = self._repo.get_latest_version(prompt_id)
        if version and version.content is None:
            version.content = self._storage.load(version.file_path)
        return version
