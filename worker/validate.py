from __future__ import annotations

from typing import Any

from .scoring import REQUIRED_INPUT_KEYS


def validate_credit_application(variables: dict[str, Any]) -> dict[str, Any]:
    """Check required process variables; does not mutate the input dict."""
    keys = {k for k in variables if not str(k).startswith("__")}
    missing = sorted(REQUIRED_INPUT_KEYS - keys)
    if missing:
        return {
            "creditInputValid": False,
            "creditValidationErrors": "brak pól: " + ", ".join(missing),
        }
    return {
        "creditInputValid": True,
        "creditValidationErrors": "",
    }
