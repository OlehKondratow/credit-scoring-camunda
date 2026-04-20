"""Smoke tests for Zeebe worker constants."""

from app.main import TASK_TYPE


def test_ai_loan_analysis_task_type() -> None:
    assert TASK_TYPE == "ai-loan-analysis"
