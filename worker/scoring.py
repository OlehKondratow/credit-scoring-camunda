from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

# Must match training/train.py
CAT_COLS = [
    "education",
    "sex",
    "car",
    "car_type",
    "good_work",
    "home_address",
    "work_address",
    "foreign_passport",
    "sna",
    "month",
]

REQUIRED_INPUT_KEYS = frozenset(
    [
        "app_date",
        "education",
        "sex",
        "age",
        "car",
        "car_type",
        "decline_app_cnt",
        "good_work",
        "score_bki",
        "bki_request_cnt",
        "region_rating",
        "home_address",
        "work_address",
        "income",
        "sna",
        "first_time",
        "foreign_passport",
    ]
)


def _native_map(d: dict[Any, Any]) -> dict[Any, Any]:
    out: dict[Any, Any] = {}
    for k, v in d.items():
        if hasattr(k, "item"):
            k = k.item()
        out[k] = float(v) if v is not None and not isinstance(v, str) else v
    return out


def apply_feature_engineering(df: pd.DataFrame, state: dict[str, Any]) -> pd.DataFrame:
    df = df.copy()
    mode_edu = state["education_mode"]
    df["education"] = df["education"].fillna(mode_edu)
    for col in ("home_address", "work_address"):
        df[col] = df[col].astype(object)
    for c in ("age", "decline_app_cnt", "bki_request_cnt", "income"):
        df[c] = np.log(pd.to_numeric(df[c], errors="coerce").fillna(0) + 1.0)

    df["app_date"] = pd.to_datetime(df["app_date"], format="%d%b%Y", errors="coerce")
    df["month"] = df["app_date"].dt.month
    bad_month = df["month"].isna()
    if bad_month.any():
        fallback = int(state.get("month_mode", 1))
        df.loc[bad_month, "month"] = fallback
    df["month"] = df["month"].astype(object)
    df = df.drop(columns=["app_date"], errors="ignore")

    reg = _native_map(state["median_income_by_region"])
    age_inc = _native_map(state["median_income_by_age"])
    age_bki = _native_map(state["median_bki_by_age"])

    rr = pd.to_numeric(df["region_rating"], errors="coerce")
    df["mean_income_region"] = rr.map(reg)
    df["mean_income_region"] = pd.to_numeric(df["mean_income_region"], errors="coerce").fillna(
        state["fill_mean_income_region"]
    )

    df["mean_income_age"] = df["age"].map(age_inc)
    df["mean_income_age"] = pd.to_numeric(df["mean_income_age"], errors="coerce").fillna(
        state["fill_mean_income_age"]
    )

    df["mean_bki_age"] = df["age"].map(age_bki)
    df["mean_bki_age"] = pd.to_numeric(df["mean_bki_age"], errors="coerce").fillna(
        state["fill_mean_bki_age"]
    )

    return df


def variables_to_features(variables: dict[str, Any], state: dict[str, Any]) -> pd.DataFrame:
    missing = sorted(REQUIRED_INPUT_KEYS - variables.keys())
    if missing:
        raise ValueError(f"missing process variables: {missing}")
    row = {k: variables[k] for k in sorted(REQUIRED_INPUT_KEYS)}
    if "client_id" in variables:
        row["client_id"] = variables["client_id"]
    raw = pd.DataFrame([row])
    engineered = apply_feature_engineering(raw, state)
    engineered = engineered.drop(columns=["client_id"], errors="ignore")
    dummy = pd.get_dummies(engineered, columns=CAT_COLS, drop_first=True)
    columns: list[str] = state["column_order"]
    return dummy.reindex(columns=columns, fill_value=0)


class CreditScorer:
    def __init__(self, model_path: str | Path) -> None:
        path = Path(model_path)
        if not path.is_file():
            raise FileNotFoundError(f"model bundle not found: {path}")
        bundle = joblib.load(path)
        self.model = bundle["model"]
        self.state: dict[str, Any] = bundle["state"]
        self.version: str = str(bundle.get("version", self.state.get("version", "1")))

    def score_dict(self, variables: dict[str, Any]) -> dict[str, Any]:
        X = variables_to_features(variables, self.state)
        proba = float(self.model.predict_proba(X)[0, 1])
        pred = 1 if proba >= 0.5 else 0
        return {
            "defaultProbability": round(proba, 6),
            "predictedDefault": pred,
            "creditMlModelVersion": self.version,
        }
