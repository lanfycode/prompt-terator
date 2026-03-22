"""
Unified LLM call client — the single entry-point for all model interactions.

Phase 1: Wraps google-genai directly for straightforward single-turn calls.
Phase 2: The same interface can be backed by a full Google ADK Runner when
         multi-step, session-aware agent orchestration is required.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional

from config import GEMINI_API_KEY
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class LLMResponse:
    """Structured result returned by every model call."""
    text:          str
    model_name:    str
    temperature:   float
    prompt_tokens: int
    output_tokens: int
    latency_ms:    float


class LLMClient:
    """
    Singleton wrapper around the Google Generative AI (Gemini) SDK.

    All agents delegate to this class so that:
    - API key management is centralised.
    - Call metadata (latency, token counts) is captured uniformly.
    - Switching the underlying SDK in Phase 2/3 requires changing only this file.
    """

    _instance: Optional["LLMClient"] = None

    def __init__(self) -> None:
        if not GEMINI_API_KEY:
            raise EnvironmentError(
                "GEMINI_API_KEY is not set. "
                "Copy .env.example → .env and fill in your key."
            )
        # Import lazily so the module can be imported without the package
        # being installed (useful in tests that mock the client).
        from google import genai as _genai
        self._client = _genai.Client(api_key=GEMINI_API_KEY)
        logger.info("LLMClient initialised.")

    @classmethod
    def get_instance(cls) -> "LLMClient":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def generate(
        self,
        model_name:        str,
        prompt:            str,
        system_instruction: Optional[str] = None,
        temperature:       float = 0.7,
        max_output_tokens: int   = 8192,
    ) -> LLMResponse:
        """
        Send a single generation request and return a structured response.

        Raises RuntimeError on API failure so callers receive a clear,
        loggable message rather than a raw SDK exception.
        """
        from google.genai import types

        config_kwargs: dict = {
            "temperature":       temperature,
            "max_output_tokens": max_output_tokens,
        }
        if system_instruction:
            config_kwargs["system_instruction"] = system_instruction

        config = types.GenerateContentConfig(**config_kwargs)

        logger.info("→ model=%s  temperature=%.2f", model_name, temperature)
        t0 = time.monotonic()

        try:
            raw = self._client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=config,
            )
        except Exception as exc:
            logger.error("Model call failed [%s]: %s", model_name, exc)
            raise RuntimeError(f"LLM call failed ({model_name}): {exc}") from exc

        latency_ms = (time.monotonic() - t0) * 1000
        usage = raw.usage_metadata

        # Field names differ slightly across SDK versions — guard both.
        prompt_tokens  = (
            getattr(usage, "prompt_token_count",  None)
            or getattr(usage, "input_token_count",  0)
        ) if usage else 0
        output_tokens  = (
            getattr(usage, "candidates_token_count", None)
            or getattr(usage, "output_token_count",  0)
        ) if usage else 0

        result = LLMResponse(
            text=raw.text or "",
            model_name=model_name,
            temperature=temperature,
            prompt_tokens=prompt_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
        )
        logger.info(
            "← tokens_in=%d  tokens_out=%d  latency=%.0fms",
            result.prompt_tokens, result.output_tokens, result.latency_ms,
        )
        return result
