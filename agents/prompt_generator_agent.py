"""
PromptGeneratorAgent — transforms a natural-language requirement into a
well-structured, production-quality prompt.

Phase 1: direct LLMClient call.
Phase 2 migration path: replace _client.generate() with an ADK LlmAgent
Runner that supports tool use, multi-turn sessions, and persistent state.
"""
from __future__ import annotations

from agents.base_agent import BaseAgent
from llm.client import LLMClient, LLMResponse
from utils.logger import get_logger

logger = get_logger(__name__)

_SYSTEM_INSTRUCTION = """\
You are an expert Prompt Engineer. Your task is to transform a user's natural-language \
requirement into a well-structured, production-quality LLM prompt.

The generated prompt MUST contain the following clearly labelled sections:
1. **Role** — Who the LLM should act as.
2. **Objective** — The goal, stated clearly and concisely.
3. **Constraints** — Boundaries, restrictions, and rules the LLM must obey.
4. **Output Format** — The exact structure expected in the response \
(e.g. JSON object, Markdown list, plain paragraph).
5. **Examples** (recommended) — 1–2 concrete input/output pairs.

Use clear Markdown formatting. Return ONLY the prompt text — no meta-commentary, \
no preamble, and no explanations about the prompt itself.\
"""


class PromptGeneratorAgent(BaseAgent):

    def __init__(self, llm_client: LLMClient) -> None:
        self._client = llm_client

    @property
    def name(self) -> str:
        return "prompt_generator"

    @property
    def system_instruction(self) -> str:
        return _SYSTEM_INSTRUCTION

    def generate(
        self,
        requirement: str,
        model_name:  str,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """Generate a structured prompt from the given requirement."""
        if not requirement.strip():
            raise ValueError("Requirement cannot be empty.")

        user_message = f"User requirement:\n\n{requirement}"
        logger.info("PromptGeneratorAgent.generate  model=%s", model_name)

        return self._client.generate(
            model_name=model_name,
            prompt=user_message,
            system_instruction=self.system_instruction,
            temperature=temperature,
        )
