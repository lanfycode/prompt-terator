"""
WorkflowService — Phase 2 stub.

Will orchestrate the full one-click optimisation pipeline:
  test-case generation → batch testing → analysis → optimisation → re-test
with stop-condition checking and per-round iteration tracking.
"""
from __future__ import annotations


class WorkflowService:
    """Phase 2: Orchestrates multi-step automated optimisation workflows."""

    def run_one_click_optimization(self, *args, **kwargs):  # noqa: ANN002
        raise NotImplementedError("WorkflowService is a Phase 2 component.")

    def stop_workflow(self, *args, **kwargs):  # noqa: ANN002
        raise NotImplementedError("WorkflowService is a Phase 2 component.")

    def resume_workflow(self, *args, **kwargs):  # noqa: ANN002
        raise NotImplementedError("WorkflowService is a Phase 2 component.")
