"""
Domain models for all phases of Prompt-Iterator.

Phase 1: Prompt, PromptVersion
Phase 2: TestCase, TestRun, Analysis, IterationRound (stubs defined here
         so the full schema can be created at startup and extended later
         without a migration).
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


# ── Shared enums ──────────────────────────────────────────────────────────────

class SourceType(str, Enum):
    GENERATED = "generated"
    OPTIMIZED = "optimized"
    MANUAL    = "manual"


class TestRunStatus(str, Enum):
    """Phase 2: status values for batch test runs."""
    PENDING   = "pending"
    RUNNING   = "running"
    COMPLETED = "completed"
    FAILED    = "failed"
    CANCELED  = "canceled"


# ── Phase 1 models ────────────────────────────────────────────────────────────

@dataclass
class Prompt:
    """Top-level Prompt asset."""
    id:              str
    name:            str
    description:     str
    current_version: int
    created_at:      str
    updated_at:      str


@dataclass
class PromptVersion:
    """
    An immutable snapshot of a Prompt at a specific point in time.
    `content` is loaded on demand from the file system and is not stored
    in SQLite.
    """
    id:               str
    prompt_id:        str
    version:          int
    source_type:      str           # SourceType value
    parent_version_id: Optional[str]
    model_name:       Optional[str]
    file_path:        str
    summary:          str
    created_at:       str
    content:          Optional[str] = None   # populated by storage layer


# ── Phase 2 models (stubs — complete structure defined for schema consistency) ─

@dataclass
class TestCase:
    """Phase 2: A named set of test cases stored as a JSON file."""
    id:               str
    name:             str
    source_type:      str           # "uploaded" | "generated"
    prompt_version_id: Optional[str]
    file_path:        str
    created_at:       str


@dataclass
class TestRun:
    """Phase 2: Execution record for a batch test."""
    id:                str
    prompt_version_id: str
    test_case_id:      Optional[str]
    model_name:        str
    status:            str          # TestRunStatus value
    total:             int
    passed:            int
    failed:            int
    result_file_path:  Optional[str]
    log_file_path:     Optional[str]
    started_at:        Optional[str]
    completed_at:      Optional[str]
    created_at:        str


@dataclass
class Analysis:
    """Phase 2: Structured analysis report derived from a TestRun."""
    id:          str
    test_run_id: str
    file_path:   str
    summary:     str
    created_at:  str


@dataclass
class IterationRound:
    """Phase 2: A single round inside an automated one-click optimization run."""
    id:               str
    workflow_run_id:  str
    round_number:     int
    prompt_version_id: str
    test_run_id:      Optional[str]
    analysis_id:      Optional[str]
    pass_rate:        Optional[float]
    created_at:       str
