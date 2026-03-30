"""
Zeebe worker: ML credit scoring (logistic regression bundle from training/train.py).

Environment:
  ZEEBE_ADDRESS  — gateway host:port (default 127.0.0.1:26500)
  MODEL_PATH     — joblib bundle (default ./models/credit_model.joblib relative to CWD)
"""
from __future__ import annotations

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Any

from pyzeebe import ZeebeWorker, create_insecure_channel

from .scoring import CreditScorer

TASK_TYPE = "c8jw-credit-score"

_log = logging.getLogger("credit-score-worker")


def _configure_logging() -> None:
    level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(message)s",
        stream=sys.stdout,
        force=True,
    )


def _default_model_path() -> Path:
    raw = os.environ.get("MODEL_PATH", "").strip()
    if raw:
        return Path(raw)
    return Path.cwd() / "models" / "credit_model.joblib"


async def main() -> None:
    _configure_logging()
    gateway = os.environ.get("ZEEBE_ADDRESS", "127.0.0.1:26500").strip()
    model_path = _default_model_path()

    try:
        scorer = CreditScorer(model_path)
    except FileNotFoundError as e:
        _log.error("%s — run training/train.py first (or set MODEL_PATH).", e)
        raise SystemExit(1) from e

    channel = create_insecure_channel(grpc_address=gateway)
    worker = ZeebeWorker(channel)

    @worker.task(task_type=TASK_TYPE)
    async def credit_score_task(**variables: Any) -> dict[str, Any]:
        payload = dict(variables)
        _log.info("job task_type=%s keys=%s", TASK_TYPE, sorted(payload.keys()))
        result = scorer.score_dict(payload)
        _log.info("score defaultProbability=%s predictedDefault=%s", result["defaultProbability"], result["predictedDefault"])
        return result

    _log.info("worker listening gateway=%s task_type=%s model=%s", gateway, TASK_TYPE, model_path.resolve())
    await worker.work()


if __name__ == "__main__":
    asyncio.run(main())
