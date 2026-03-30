from __future__ import annotations

from pathlib import Path

import pytest
from worker.scoring import CreditScorer, variables_to_features

Vars = dict[str, object]


def test_scorer_roundtrip(demo_model_path: Path, sample_process_variables: Vars) -> None:
    scorer = CreditScorer(demo_model_path)
    result = scorer.score_dict(sample_process_variables)
    assert "defaultProbability" in result
    assert "predictedDefault" in result
    assert "creditMlModelVersion" in result
    assert 0.0 <= result["defaultProbability"] <= 1.0
    assert result["predictedDefault"] in (0, 1)
    assert result["creditMlModelVersion"]


def test_scorer_missing_variable_raises(
    demo_model_path: Path,
    sample_process_variables: Vars,
) -> None:
    scorer = CreditScorer(demo_model_path)
    bad = {k: v for k, v in sample_process_variables.items() if k != "region_rating"}
    with pytest.raises(ValueError, match="missing|region_rating"):
        scorer.score_dict(bad)


def test_variables_to_features_allows_client_id(
    demo_model_path: Path,
    sample_process_variables: Vars,
) -> None:
    scorer = CreditScorer(demo_model_path)
    payload = dict(sample_process_variables)
    payload["client_id"] = "c-001"
    X = variables_to_features(payload, scorer.state)
    assert "client_id" not in X.columns
    assert X.shape[0] == 1
