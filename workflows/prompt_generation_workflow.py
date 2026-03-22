"""
PromptGenerationWorkflow — thin orchestration wrapper for Phase 1.

Encapsulates the steps:
  collect requirement → call PromptService.generate_prompt → return result

In Phase 2 this layer will expand to support multi-agent coordination,
retry logic, intermediate result persistence, and event emission.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from llm.client import LLMResponse
from services.prompt_service import PromptService
from models.prompt import Prompt, PromptVersion, SourceType
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class GenerationResult:
    text:     str
    response: LLMResponse
    prompt:   Optional[Prompt]        = None
    version:  Optional[PromptVersion] = None
    saved:    bool                    = False


class PromptGenerationWorkflow:

    def __init__(self, prompt_service: Optional[PromptService] = None) -> None:
        self._ps = prompt_service or PromptService()

    def run(
        self,
        requirement: str,
        model_name:  str,
        temperature: float = 0.7,
        save:        bool  = False,
        name:        str   = "",
    ) -> GenerationResult:
        """
        Execute the generation workflow.

        If *save* is True, persists the result as a new Prompt (requires *name*).
        """
        text, response = self._ps.generate_prompt(
            requirement=requirement,
            model_name=model_name,
            temperature=temperature,
        )
        result = GenerationResult(text=text, response=response)

        if save:
            if not name.strip():
                raise ValueError("A prompt name is required when save=True.")
            prompt, version = self._ps.save_new_prompt(
                name=name,
                content=text,
                source_type=SourceType.GENERATED,
                model_name=model_name,
                summary="Generated from requirement",
            )
            result.prompt  = prompt
            result.version = version
            result.saved   = True
            logger.info(
                "GenerationWorkflow: saved '%s' v%d", prompt.name, version.version
            )

        return result
