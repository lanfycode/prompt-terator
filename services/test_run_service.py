"""
TestRunService — Phase 2 stub.

Will execute single-turn and batch test runs, track task status, and persist
result files and log files.
"""
from __future__ import annotations


class TestRunService:
    """Phase 2: Executes and tracks test runs."""

    def run_single_test(self, *args, **kwargs):  # noqa: ANN002
        raise NotImplementedError("TestRunService is a Phase 2 component.")

    def run_batch_test(self, *args, **kwargs):  # noqa: ANN002
        raise NotImplementedError("TestRunService is a Phase 2 component.")

    def get_test_run_status(self, *args, **kwargs):  # noqa: ANN002
        raise NotImplementedError("TestRunService is a Phase 2 component.")

    def retry_test_run(self, *args, **kwargs):  # noqa: ANN002
        raise NotImplementedError("TestRunService is a Phase 2 component.")
