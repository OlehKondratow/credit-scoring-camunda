"""
Zeebe workers for credit scoring pipeline (single process, multiple job types):

  c8jw-credit-validate — required fields (scoring.REQUIRED_INPUT_KEYS)
  c8jw-credit-score   — joblib model (training/train.py)
  c8jw-credit-route   — risk band + routingHint from defaultProbability

Environment:
  ZEEBE_ADDRESS       — gateway (default 127.0.0.1:26500)
  MODEL_PATH          — joblib bundle for score worker
  CREDIT_THRESHOLD_HIGH / CREDIT_THRESHOLD_MID — route.py thresholds
  WORKERS             — comma-separated job types to register (default: all three)

Legacy single worker only:
  WORKERS=c8jw-credit-score  — same behavior as earlier single-task BPMN

Run from project root:  python worker/run_worker.py
"""
from __future__ import annotations

import asyncio
import logging
import os
import sys
from pathlib import Path

from pyzeebe import ZeebeWorker, create_insecure_channel

from route import route_credit_decision
from scoring import CreditScorer
from validate import validate_credit_application

TASK_VALIDATE = "c8jw-credit-validate"
TASK_SCORE = "c8jw-credit-score"
TASK_ROUTE = "c8jw-credit-route"
DEFAULT_TASKS = f"{TASK_VALIDATE},{TASK_SCORE},{TASK_ROUTE}"

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


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _default_model_path() -> Path:
    raw = os.environ.get("MODEL_PATH", "").strip()
    if raw:
        return Path(raw)
    return _project_root() / "models" / "credit_model.joblib"


def _parse_workers() -> set[str]:
    raw = os.environ.get("WORKERS", DEFAULT_TASKS).strip()
    if not raw:
        return set()
    return {t.strip() for t in raw.split(",") if t.strip()}


async def main() -> None:
    _configure_logging()
    gateway = os.environ.get("ZEEBE_ADDRESS", "127.0.0.1:26500").strip()
    model_path = _default_model_path()
    active = _parse_workers()

    scorer: CreditScorer | None = None
    if TASK_SCORE in active:
        try:
            scorer = CreditScorer(model_path)
        except FileNotFoundError as e:
            _log.error("%s — uruchom training/train.py lub ustaw MODEL_PATH.", e)
            raise SystemExit(1) from e

    channel = create_insecure_channel(grpc_address=gateway)
    worker = ZeebeWorker(channel)

    if TASK_VALIDATE in active:

        @worker.task(task_type=TASK_VALIDATE)
        async def validate_task(**variables):
            payload = dict(variables)
            _log.info("job %s keys=%s", TASK_VALIDATE, sorted(payload.keys()))
            out = validate_credit_application(payload)
            _log.info("validate creditInputValid=%s", out["creditInputValid"])
            return out

    if TASK_SCORE in active:

        @worker.task(task_type=TASK_SCORE)
        async def score_task(**variables):
            payload = dict(variables)
            _log.info("job %s keys=%s", TASK_SCORE, sorted(payload.keys()))
            assert scorer is not None
            result = scorer.score_dict(payload)
            _log.info(
                "score defaultProbability=%s predictedDefault=%s",
                result["defaultProbability"],
                result["predictedDefault"],
            )
            return result

    if TASK_ROUTE in active:

        @worker.task(task_type=TASK_ROUTE)
        async def route_task(**variables):
            payload = dict(variables)
            _log.info("job %s", TASK_ROUTE)
            out = route_credit_decision(**payload)
            _log.info("route band=%s hint=%s", out["creditRiskBand"], out["routingHint"])
            return out

    if not active:
        _log.error("WORKERS jest puste — ustaw np. WORKERS=%s", DEFAULT_TASKS)
        raise SystemExit(1)

    _log.info(
        "gateway=%s workers=%s model=%s",
        gateway,
        ", ".join(sorted(active)),
        model_path.resolve() if scorer else "—",
    )
    await worker.work()


if __name__ == "__main__":
    asyncio.run(main())
