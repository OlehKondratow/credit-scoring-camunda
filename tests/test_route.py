from __future__ import annotations

import pytest
from worker.route import route_credit_decision


@pytest.mark.parametrize(
    ("probability", "expected_band", "expected_hint", "expected_review"),
    [
        (0.0, "LOW", "AUTO_APPROVE", False),
        (0.24, "LOW", "AUTO_APPROVE", False),
        (0.25, "MEDIUM", "STANDARD_REVIEW", True),
        (0.49, "MEDIUM", "STANDARD_REVIEW", True),
        (0.5, "HIGH", "MANUAL_UNDERWRITING", True),
        (0.99, "HIGH", "MANUAL_UNDERWRITING", True),
    ],
)
def test_route_default_thresholds(
    monkeypatch: pytest.MonkeyPatch,
    probability: float,
    expected_band: str,
    expected_hint: str,
    expected_review: bool,
) -> None:
    monkeypatch.delenv("CREDIT_THRESHOLD_HIGH", raising=False)
    monkeypatch.delenv("CREDIT_THRESHOLD_MID", raising=False)
    out = route_credit_decision(defaultProbability=probability)
    assert out["creditRiskBand"] == expected_band
    assert out["routingHint"] == expected_hint
    assert out["reviewRequired"] is expected_review


def test_route_respects_custom_thresholds(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CREDIT_THRESHOLD_HIGH", "0.8")
    monkeypatch.setenv("CREDIT_THRESHOLD_MID", "0.4")
    assert route_credit_decision(defaultProbability=0.79)["creditRiskBand"] == "MEDIUM"
    assert route_credit_decision(defaultProbability=0.8)["creditRiskBand"] == "HIGH"


def test_route_missing_probability_defaults_to_zero(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CREDIT_THRESHOLD_HIGH", raising=False)
    monkeypatch.delenv("CREDIT_THRESHOLD_MID", raising=False)
    out = route_credit_decision()
    assert out["creditRiskBand"] == "LOW"
