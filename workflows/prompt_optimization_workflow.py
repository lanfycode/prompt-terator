"""
PromptOptimizationWorkflow — thin orchestration wrapper for Phase 1.

Encapsulates the steps:
  load latest version → call OptimizationService.optimize_and_save → return result

Phase 2 will extend this to accept structured analysis results from
AnalysisService and to trigger the next test round automatically.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from llm.client import LLMResponse
from services.optimization_service import OptimizationService
from models.prompt import Prompt, PromptVersion
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class OptimizationResult:
    prompt:   Prompt
    version:  PromptVersion
    response: LLMResponse


class PromptOptimizationWorkflow:

    def __init__(
        self,
        optimization_service: Optional[OptimizationService] = None,
    ) -> None:
        self._os = optimization_service or OptimizationService()

    def run(
        self,
        prompt_id:            str,
        optimization_request: str,
        model_name:           str,
        temperature:          float = 0.7,
        analysis_context:     Optional[str] = None,
    ) -> OptimizationResult:
        """
        Execute the optimisation workflow for an existing prompt.

        *analysis_context* is reserved for Phase 2 (analysis-driven optimisation).
        """
        prompt, version, response = self._os.optimize_and_save(
            prompt_id=prompt_id,
            optimization_request=optimization_request,
            model_name=model_name,
            temperature=temperature,
            analysis_context=analysis_context,
        )
        logger.info(
            "OptimizationWorkflow: '%s' → v%d", prompt.name, version.version
        )
        return OptimizationResult(
            prompt=prompt, version=version, response=response
        )
