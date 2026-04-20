"""Mock BIK (Biuro Informacji Kredytowej) API — replace with regulated integration in production."""

from __future__ import annotations

import asyncio
import hashlib
import logging
import random
from typing import Any

from app.config import get_settings

logger = logging.getLogger(__name__)


async def fetch_bik_summary(pesel_hash: str) -> dict[str, Any]:
    """
    Returns a deterministic-ish mock profile keyed by PESEL hash (never send raw PESEL).
    """
    settings = get_settings()
    await asyncio.sleep(settings.bik_mock_delay_s)
    seed = int(hashlib.sha256(pesel_hash.encode()).hexdigest()[:8], 16)
    rnd = random.Random(seed)
    overdue = rnd.choice([0, 0, 0, 1, 2])
    active_credits = rnd.randint(0, 3)
    inquiries_90d = rnd.randint(0, 5)
    result = {
        "status": "MOCK_OK",
        "active_credits": active_credits,
        "overdue_installments_90d": overdue,
        "hard_inquiries_90d": inquiries_90d,
        "risk_hint": "niski" if overdue == 0 else "podwyższony",
        "message_pl": (
            "Symulacja BIK: brak przeterminowanych rat."
            if overdue == 0
            else "Symulacja BIK: wykryto przeterminowane raty w oknie 90 dni."
        ),
    }
    logger.info("bik_mock", extra={"extra_json": {"pesel_hash_prefix": pesel_hash[:8], "result": result}})
    return result
