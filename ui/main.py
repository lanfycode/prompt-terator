"""
Main Gradio application builder.

Assembles all tabs inside a single gr.Blocks context and wires any
cross-page state that individual page builders expose.
"""
from __future__ import annotations

import gradio as gr

from services.prompt_service import PromptService
from services.optimization_service import OptimizationService
from ui.pages import prompt_generate_page, prompt_optimize_page, prompt_list_page


def create_ui(
    prompt_service:       PromptService,
    optimization_service: OptimizationService,
) -> gr.Blocks:
    """Build and return the Gradio Blocks application."""

    with gr.Blocks(
        title="Prompt Iterator",
        analytics_enabled=False,
    ) as app:
        gr.Markdown(
            "# ✨ Prompt Iterator\n"
            "> Prompt 工程工作台 — 生成、优化、追踪、迭代"
        )

        with gr.Tabs():
            # ── Tab 1: Prompt 生成 ────────────────────────────────────────────
            with gr.Tab("📝 Prompt 生成"):
                prompt_generate_page.build(prompt_service)

            # ── Tab 2: Prompt 优化 ────────────────────────────────────────────
            with gr.Tab("🔧 Prompt 优化"):
                # build() returns shared components for cross-page wiring
                original_box, prompt_id_state = prompt_optimize_page.build(
                    prompt_service, optimization_service
                )

            # ── Tab 3: Prompt 管理 ────────────────────────────────────────────
            with gr.Tab("📂 Prompt 管理"):
                prompt_list_page.build(
                    prompt_service,
                    original_box=original_box,
                    prompt_id_state=prompt_id_state,
                )

    return app
