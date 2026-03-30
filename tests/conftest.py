from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def demo_model_path(tmp_path_factory: pytest.TempPathFactory) -> Path:
    out_dir = tmp_path_factory.mktemp("models")
    out = out_dir / "credit_model.joblib"
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "training" / "train.py"),
            "--demo",
            "--out",
            str(out),
            "--seed",
            "42",
        ],
        check=True,
        cwd=str(ROOT),
    )
    return out


@pytest.fixture
def sample_process_variables() -> dict[str, object]:
    """Minimal valid variables aligned with REQUIRED_INPUT_KEYS."""
    return {
        "app_date": "15FEB2014",
        "education": "GRD",
        "sex": "M",
        "age": 35,
        "car": "Y",
        "car_type": "Y",
        "decline_app_cnt": 0,
        "good_work": 1,
        "score_bki": -1.2,
        "bki_request_cnt": 2,
        "region_rating": 50,
        "home_address": 2,
        "work_address": 3,
        "income": 45_000,
        "sna": 3,
        "first_time": 1,
        "foreign_passport": "N",
    }
