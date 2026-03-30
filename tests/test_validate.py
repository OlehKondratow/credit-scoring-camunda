from __future__ import annotations

from worker.scoring import REQUIRED_INPUT_KEYS
from worker.validate import validate_credit_application


def test_validate_complete_ok(sample_process_variables: dict[str, object]) -> None:
    out = validate_credit_application(sample_process_variables)
    assert out["creditInputValid"] is True
    assert out["creditValidationErrors"] == ""


def test_validate_missing_keys(sample_process_variables: dict[str, object]) -> None:
    incomplete = {k: v for k, v in sample_process_variables.items() if k != "income"}
    out = validate_credit_application(incomplete)
    assert out["creditInputValid"] is False
    assert "income" in out["creditValidationErrors"]


def test_validate_ignores_dunder_keys(sample_process_variables: dict[str, object]) -> None:
    payload = dict(sample_process_variables)
    payload["__camundaTaskId"] = "x"
    missing_one = {k: v for k, v in payload.items() if k != "app_date"}
    out = validate_credit_application(missing_one)
    assert out["creditInputValid"] is False
    assert "app_date" in out["creditValidationErrors"]


def test_required_keys_match_documented_contract() -> None:
    assert "score_bki" in REQUIRED_INPUT_KEYS
    assert "bki_request_cnt" in REQUIRED_INPUT_KEYS
    assert len(REQUIRED_INPUT_KEYS) == 17
