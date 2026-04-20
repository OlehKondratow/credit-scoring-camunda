"""
Zeebe worker: task type `ai-loan-analysis`.
Calls FastAPI backend /analyze and completes job with risk_score, final_decision, justification_pl.
On HTTP timeout: raises BusinessError -> BPMN error event (e.g. AI_SERVICE_TIMEOUT).
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys

import httpx
from pyzeebe import Job, ZeebeWorker, create_insecure_channel
from pyzeebe.errors.pyzeebe_errors import BusinessError

from app.logging_json import setup_logging

TASK_TYPE = "ai-loan-analysis"
DEFAULT_GATEWAY = "zeebe:26500"
BACKEND_URL = os.environ.get("BACKEND_URL", "http://backend:8000").rstrip("/")
AI_TIMEOUT_S = float(os.environ.get("AI_TIMEOUT_S", "45"))
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

setup_logging(LOG_LEVEL)
log = logging.getLogger("ai-worker")


async def main() -> None:
    gateway = os.environ.get("ZEEBE_ADDRESS", DEFAULT_GATEWAY).strip()
    channel = create_insecure_channel(grpc_address=gateway)
    worker = ZeebeWorker(channel)

    @worker.task(task_type=TASK_TYPE, timeout_ms=int((AI_TIMEOUT_S + 15) * 1000))
    async def ai_loan_analysis(job: Job, application: dict | None = None) -> dict:
        if not application:
            raise BusinessError("MISSING_APPLICATION", "Brak zmiennej process 'application'.")

        url = f"{BACKEND_URL}/analyze"
        log.info("job_start job_key=%s", job.key)
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(AI_TIMEOUT_S)) as client:
                r = await client.post(url, json={"application": application})
        except httpx.TimeoutException as e:
            log.warning("ai_timeout job_key=%s", job.key)
            raise BusinessError(
                "AI_SERVICE_TIMEOUT",
                "Przekroczono czas oczekiwania na usługę AI (fallback ręczny).",
            ) from e
        except httpx.RequestError as e:
            log.exception("ai_request_error")
            raise BusinessError(
                "AI_BACKEND_UNAVAILABLE",
                f"Backend AI niedostępny: {e!s}",
            ) from e

        if r.status_code >= 500:
            raise BusinessError(
                "AI_BACKEND_ERROR",
                f"Błąd serwera AI: HTTP {r.status_code}",
            )
        if r.status_code >= 400:
            raise BusinessError(
                "AI_BAD_REQUEST",
                f"Niepoprawne żądanie: HTTP {r.status_code} {r.text[:200]}",
            )

        data = r.json()
        out = {
            "risk_score": int(data.get("risk_score", 0)),
            "final_decision": str(data.get("final_decision", "MANUAL")),
            "justification_pl": str(data.get("justification_pl", "")),
            "chain_of_thought_pl": str(data.get("chain_of_thought_pl", "")),
            "retrieved_chunks": data.get("retrieved_chunks") or [],
            "dmn_snapshot": data.get("dmn") or {},
            "bik_snapshot": data.get("bik") or {},
            "llm_reasoning_pl": str(data.get("llm_reasoning_pl", "")),
            "reflection_pl": str(data.get("reflection_pl", "")),
        }
        log.info("job_complete job_key=%s decision=%s", job.key, out["final_decision"])
        return out

    log.info("worker_started task=%s gateway=%s backend=%s", TASK_TYPE, gateway, BACKEND_URL)
    await worker.work()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
