"""
OptimizationService — coordinates prompt optimisation and version persistence.

Phase 1: wraps PromptService to load the latest version of a prompt,
         call the optimiser, and save the result as a new version.

Phase 2: the `analysis_context` parameter will be populated automatically
         from AnalysisService results linked to a completed TestRun, allowing
         targeted, evidence-driven optimisation without user intervention.
"""
from __future__ import annotations

from typing import Optional, Tuple

from llm.client import LLMResponse
from models.prompt import Prompt, PromptVersion, SourceType
from services.prompt_service import PromptService
from utils.logger import get_logger

logger = get_logger(__name__)


class OptimizationService:

    def __init__(self, prompt_service: Optional[PromptService] = None) -> None:
        self._ps = prompt_service or PromptService()

    def optimize_and_save(
        self,
        prompt_id:            str,
        optimization_request: str,
        model_name:           str,
        temperature:          float = 0.7,
        analysis_context:     Optional[str] = None,
    ) -> Tuple[Prompt, PromptVersion, LLMResponse]:
        """
        Optimise the latest version of *prompt_id* and persist the result.

        Returns (updated_prompt, new_version, raw_llm_response).
        """
        latest = self._ps.get_latest_version_with_content(prompt_id)
        if not latest or not latest.content:
            raise ValueError(
                f"No content found for prompt_id={prompt_id}. "
                "Save at least one version before optimising."
            )

        optimised_text, response = self._ps.optimize_prompt(
            original_prompt=latest.content,
            optimization_request=optimization_request,
            model_name=model_name,
            temperature=temperature,
            analysis_context=analysis_context,
        )

        summary = f"Optimised: {optimization_request[:80]}"
        prompt, version = self._ps.save_new_version(
            prompt_id=prompt_id,
            content=optimised_text,
            source_type=SourceType.OPTIMIZED,
            model_name=model_name,
            parent_version_id=latest.id,
            summary=summary,
        )
        logger.info(
            "OptimizationService: saved v%d for prompt_id=%s",
            version.version, prompt_id,
        )
        return prompt, version, response
