"""
Abstract base for all agents in Prompt-Iterator.

Phase 1: Agents wrap LLMClient for straightforward single-turn model calls.
Phase 2: Agents can be migrated to full Google ADK LlmAgent/Runner
         orchestration when session state, tools, and multi-step workflows
         are required.
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class BaseAgent(ABC):

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique agent identifier (lower_snake_case)."""

    @property
    @abstractmethod
    def system_instruction(self) -> str:
        """System prompt sent with every request via this agent."""
