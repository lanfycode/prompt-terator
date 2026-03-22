"""Reusable Gradio model-selector dropdown component."""
from __future__ import annotations

import gradio as gr

from llm.model_registry import get_model_names, DEFAULT_MODEL_NAME


def create_model_selector(
    label: str = "选择模型",
    value: str | None = None,
) -> gr.Dropdown:
    """Return a pre-configured, interactive model-selector Dropdown."""
    return gr.Dropdown(
        choices=get_model_names(),
        value=value or DEFAULT_MODEL_NAME,
        label=label,
        interactive=True,
    )
