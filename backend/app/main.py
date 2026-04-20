"""FastAPI entrypoint for the Agentic RAG engine."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.config import get_settings
from app.graph.agent import GRAPH
from app.logging_config import setup_logging

setup_logging(get_settings().log_level)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Millennium Credit Agent",
    version="0.1.0",
    description="Agentic RAG backend (internal). Responses include Polish officer-facing fields.",
)


class AnalyzeRequest(BaseModel):
    application: dict[str, Any] = Field(
        ...,
        description="Raw application payload (may contain PESEL — masked before LLM).",
    )


class AnalyzeResponse(BaseModel):
    risk_score: int = Field(..., ge=0, le=100)
    final_decision: str
    justification_pl: str
    chain_of_thought_pl: str
    retrieved_chunks: list[dict[str, Any]]
    dmn: dict[str, Any]
    bik: dict[str, Any]
    llm_reasoning_pl: str
    reflection_pl: str


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok", "region": get_settings().google_cloud_region}


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(body: AnalyzeRequest) -> AnalyzeResponse:
    if not body.application:
        raise HTTPException(status_code=400, detail="application is required")
    try:
        out = await GRAPH.ainvoke({"application_raw": body.application})
    except Exception as e:  # noqa: BLE001
        logger.exception("graph_failed")
        raise HTTPException(status_code=500, detail=str(e)) from e

    return AnalyzeResponse(
        risk_score=int(out.get("risk_score") or 0),
        final_decision=str(out.get("final_decision") or "MANUAL"),
        justification_pl=str(out.get("justification_pl") or ""),
        chain_of_thought_pl=str(out.get("chain_of_thought_pl") or ""),
        retrieved_chunks=list(out.get("retrieved_chunks") or []),
        dmn=dict(out.get("dmn") or {}),
        bik=dict(out.get("bik") or {}),
        llm_reasoning_pl=str(out.get("llm_reasoning_pl") or ""),
        reflection_pl=str(out.get("reflection_pl") or ""),
    )
