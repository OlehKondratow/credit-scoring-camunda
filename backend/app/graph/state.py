"""Shared LangGraph state (typed)."""

from __future__ import annotations

from typing import Any, Literal, TypedDict


class AgentState(TypedDict, total=False):
    application_raw: dict[str, Any]
    application_masked: dict[str, Any]
    applicant_age: int | None
    bik: dict[str, Any]
    retrieved_chunks: list[dict[str, Any]]
    dmn: dict[str, Any]
    llm_reasoning_pl: str
    reflection_pl: str
    risk_score: int
    final_decision: Literal["APPROVED", "REJECTED", "MANUAL"]
    justification_pl: str
    chain_of_thought_pl: str
    error: str | None
