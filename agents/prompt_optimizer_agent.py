"""
PromptOptimizerAgent — rewrites an existing prompt according to explicit
optimization instructions, optionally incorporating analysis context.

Phase 1: direct LLMClient call with optional analysis_context parameter.
Phase 2 migration path: analysis_context will be populated automatically
by AnalysisService and injected here through the WorkflowService.
"""
from __future__ import annotations

from agents.base_agent import BaseAgent
from llm.client import LLMClient, LLMResponse
from utils.logger import get_logger

logger = get_logger(__name__)

_SYSTEM_INSTRUCTION = """\
You are an expert Prompt Engineer specialising in prompt optimisation.
You will receive an existing prompt and a set of optimisation instructions.

Your job is to produce an improved version that:
- Preserves the original intent, role, and core objective.
- Applies the requested improvements precisely and completely.
- Enhances clarity, specificity, and effectiveness.
- Does NOT introduce content unrelated to the optimisation request.

Return ONLY the optimised prompt text. No explanations, no meta-commentary.\
"""

_TEMPLATE = """\
## Original Prompt

{original_prompt}

## Optimisation Instructions

{optimization_request}\
"""


class PromptOptimizerAgent(BaseAgent):

    def __init__(self, llm_client: LLMClient) -> None:
        self._client = llm_client

    @property
    def name(self) -> str:
        return "prompt_optimizer"

    @property
    def system_instruction(self) -> str:
        return _SYSTEM_INSTRUCTION

    def optimize(
        self,
        original_prompt:      str,
        optimization_request: str,
        model_name:           str,
        temperature:          float = 0.7,
        analysis_context:     str | None = None,
    ) -> LLMResponse:
        """
        Optimize *original_prompt* following *optimization_request*.

        Args:
            analysis_context: Phase 2 — structured failure analysis to guide
                              targeted optimisation.  Pass None in Phase 1.
        """
        if not original_prompt.strip():
            raise ValueError("Original prompt cannot be empty.")
        if not optimization_request.strip():
            raise ValueError("Optimisation request cannot be empty.")

        user_message = _TEMPLATE.format(
            original_prompt=original_prompt,
            optimization_request=optimization_request,
        )

        # Phase 2: prepend analysis results when available
        if analysis_context:
            user_message = (
                f"## Test-Failure Analysis\n\n{analysis_context}\n\n"
                + user_message
            )

        logger.info("PromptOptimizerAgent.optimize  model=%s", model_name)

        return self._client.generate(
            model_name=model_name,
            prompt=user_message,
            system_instruction=self.system_instruction,
            temperature=temperature,
        )
