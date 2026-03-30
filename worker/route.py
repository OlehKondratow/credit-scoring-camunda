from __future__ import annotations

import os
from typing import Any


def route_credit_decision(**variables: Any) -> dict[str, Any]:
    """
    Routing from ML score (no extra model). Uses defaultProbability only.
    Env: CREDIT_THRESHOLD_HIGH (default 0.5), CREDIT_THRESHOLD_MID (default 0.25).
    """
    p = float(variables.get("defaultProbability", 0.0))

    t_hi = float(os.environ.get("CREDIT_THRESHOLD_HIGH", "0.5"))
    t_mid = float(os.environ.get("CREDIT_THRESHOLD_MID", "0.25"))

    if p >= t_hi:
        band = "HIGH"
        hint = "MANUAL_UNDERWRITING"
        review = True
    elif p >= t_mid:
        band = "MEDIUM"
        hint = "STANDARD_REVIEW"
        review = True
    else:
        band = "LOW"
        hint = "AUTO_APPROVE"
        review = False

    return {
        "creditRiskBand": band,
        "routingHint": hint,
        "reviewRequired": review,
    }
