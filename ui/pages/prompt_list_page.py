"""
Prompt Management page — Tab 3 of the workbench.

Features:
  - Paginated prompt list with version counts.
  - Version history for the selected prompt.
  - Content preview for the selected version.
  - Load-to-Optimize: fills the Optimise page's original_box and
    sets prompt_id_state so saves append to the correct prompt.

Cross-page wiring:
  `build()` receives `original_box` and `prompt_id_state` from the
  Optimise page and wires them via a "加载到优化页" button.
"""
from __future__ import annotations

from typing import List, Optional, Tuple

import gradio as gr

from models.prompt import Prompt, PromptVersion
from services.prompt_service import PromptService
from utils.logger import get_logger

logger = get_logger(__name__)


def build(
    prompt_service:  PromptService,
    original_box:    gr.Textbox,
    prompt_id_state: gr.State,
) -> None:
    """Render the Prompt Management tab UI and wire cross-page load events."""

    gr.Markdown(
        "## Prompt 管理\n"
        "查看已保存的所有 Prompt 及其版本历史，并可将任意版本加载到优化页。"
    )

    # ── Layout ────────────────────────────────────────────────────────────────
    with gr.Row():
        # Left: prompt list
        with gr.Column(scale=1):
            gr.Markdown("### Prompt 列表")
            refresh_btn    = gr.Button("🔄 刷新列表", variant="secondary", size="sm")
            prompt_list_box = gr.Textbox(
                label="已保存的 Prompt（ID前8位 | 名称 | 版本 | 更新时间）",
                lines=12,
                max_lines=20,
                interactive=False,
                placeholder="点击【刷新列表】按钮加载…",
            )

        # Right: version history + preview
        with gr.Column(scale=1):
            gr.Markdown("### 版本历史")
            # The selected prompt_id (full) is stored here
            selected_prompt_id = gr.State(value=None)

            prompt_selector = gr.Dropdown(
                label="选择 Prompt（刷新列表后从此下拉选择）",
                choices=[],
                value=None,
                allow_custom_value=True,
                interactive=True,
            )
            load_versions_btn = gr.Button("查看版本", variant="secondary", size="sm")
            version_list_box  = gr.Textbox(
                label="版本历史（版本号 | 来源 | 模型 | 摘要 | 创建时间 | 版本ID）",
                lines=8,
                max_lines=15,
                interactive=False,
                placeholder="选择 Prompt 后点击【查看版本】按钮…",
            )

            gr.Markdown("### 版本内容预览")
            version_id_input = gr.Textbox(
                label="版本 ID（从版本历史最后一列复制）",
                placeholder="粘贴版本 ID 后点击预览…",
            )
            with gr.Row():
                preview_btn          = gr.Button("预览内容", size="sm")
                load_to_optimize_btn = gr.Button(
                    "📤 加载到优化页", variant="primary", size="sm"
                )
            content_preview = gr.Textbox(
                label="版本内容",
                lines=12,
                max_lines=25,
                interactive=False,
            )
            load_status = gr.Textbox(label="操作状态", interactive=False)

    # ── Helper functions ──────────────────────────────────────────────────────

    def _prompt_table(prompts: List[Prompt]) -> str:
        if not prompts:
            return "（暂无已保存的 Prompt）"
        lines = ["  #  ID前8位   名称                          版本  更新时间"]
        lines.append("─" * 68)
        for i, p in enumerate(prompts, 1):
            lines.append(
                f"{i:3}.  {p.id[:8]}  {p.name[:28]:<28}  v{p.current_version:<3}"
                f"  {p.updated_at[:19].replace('T', ' ')}"
            )
        return "\n".join(lines)

    def _version_table(versions: List[PromptVersion]) -> str:
        if not versions:
            return "（无版本记录）"
        lines = []
        for v in versions:
            lines.append(
                f"v{v.version}  [{v.source_type}]  {v.model_name or '—'}\n"
                f"   摘要: {v.summary[:60]}\n"
                f"   时间: {v.created_at[:19].replace('T', ' ')}\n"
                f"   ID  : {v.id}"
            )
            lines.append("─" * 60)
        return "\n".join(lines)

    # ── Event handlers ────────────────────────────────────────────────────────

    def _on_refresh():
        prompts = prompt_service.list_prompts()
        table   = _prompt_table(prompts)
        choices = [f"{p.id[:8]}  {p.name}" for p in prompts]
        return table, gr.update(choices=choices, value=None)

    def _on_load_versions(selector_value: str | None):
        if not selector_value:
            gr.Warning("请先从下拉选择一个 Prompt。")
            return gr.update(), None
        prefix  = selector_value.split()[0]
        prompts = prompt_service.list_prompts()
        match   = next(
            (p for p in prompts if p.id.startswith(prefix) or p.id == selector_value),
            None,
        )
        if not match:
            gr.Warning(f"找不到 Prompt：{selector_value}")
            return gr.update(), None
        versions = prompt_service.list_versions(match.id)
        return _version_table(versions), match.id

    def _on_preview(version_id: str):
        if not version_id.strip():
            return "请输入版本 ID。"
        version = prompt_service.get_version_with_content(version_id.strip())
        if not version:
            return f"找不到版本：{version_id}"
        return version.content or "(内容为空)"

    def _on_load_to_optimize(
        version_id: str,
        current_prompt_id: Optional[str],
    ) -> Tuple[str, str, str]:
        if not version_id.strip():
            return gr.update(), gr.update(), "⚠ 请先输入版本 ID 并点击预览。"
        version = prompt_service.get_version_with_content(version_id.strip())
        if not version:
            return gr.update(), gr.update(), f"❌ 找不到版本：{version_id}"
        content = version.content or ""
        return content, version.prompt_id, f"✅ 已加载版本 v{version.version} 到优化页"

    # ── Wire events ───────────────────────────────────────────────────────────

    refresh_btn.click(
        fn=_on_refresh,
        outputs=[prompt_list_box, prompt_selector],
    )

    load_versions_btn.click(
        fn=_on_load_versions,
        inputs=[prompt_selector],
        outputs=[version_list_box, selected_prompt_id],
    )

    preview_btn.click(
        fn=_on_preview,
        inputs=[version_id_input],
        outputs=[content_preview],
    )

    # Cross-page: load content into the Optimise tab
    load_to_optimize_btn.click(
        fn=_on_load_to_optimize,
        inputs=[version_id_input, selected_prompt_id],
        outputs=[original_box, prompt_id_state, load_status],
    )
