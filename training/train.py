#!/usr/bin/env python3
"""
Train logistic regression credit scorer (feature logic aligned with
github.com/0leh-kondratov/credit-scoring notebook). Writes joblib bundle for worker/.

Usage:
  python training/train.py --data data/train.csv
  python training/train.py --demo   # synthetic CSV, no download

Output (default): models/credit_model.joblib
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

# Must match worker/scoring.py
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

BUNDLE_VERSION = "1"


def _root() -> Path:
    return Path(__file__).resolve().parent.parent


def make_synthetic_dataset(n: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    edu = rng.choice(["SCH", "GRD", "UGR", "PGR", "ACD"], size=n, p=[0.3, 0.25, 0.25, 0.15, 0.05])
    sex = rng.choice(["M", "F"], size=n)
    age = rng.integers(22, 70, size=n)
    car = rng.choice(["Y", "N"], size=n, p=[0.4, 0.6])
    car_type = np.where(car == "Y", rng.choice(["Y", "N"], size=n), "N")
    decline = rng.poisson(0.5, size=n)
    good_work = rng.integers(0, 2, size=n)
    score_bki = rng.normal(-1.5, 0.8, size=n)
    bki_req = rng.poisson(2, size=n)
    region = rng.choice([30, 40, 50, 60], size=n)
    home_a = rng.integers(1, 4, size=n)
    work_a = rng.integers(1, 5, size=n)
    income = rng.integers(15_000, 120_000, size=n)
    sna = rng.integers(1, 6, size=n)
    first_time = rng.integers(0, 2, size=n)
    passport = rng.choice(["Y", "N"], size=n, p=[0.2, 0.8])
    day = rng.integers(1, 28, size=n)
    months = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
    mon = rng.choice(months, size=n)
    year = rng.integers(2013, 2016, size=n)
    app_date = [f"{d:02d}{m}{y}" for d, m, y in zip(day, mon, year, strict=True)]
    score = 0.15 * (age < 35) + 0.2 * (income < 30_000) + 0.25 * (score_bki > -1.0)
    score += rng.normal(0, 0.15, size=n)
    default = (score > 0.45).astype(int)
    return pd.DataFrame(
        {
            "client_id": np.arange(10_000, 10_000 + n),
            "app_date": app_date,
            "education": edu,
            "sex": sex,
            "age": age,
            "car": car,
            "car_type": car_type,
            "decline_app_cnt": decline,
            "good_work": good_work,
            "score_bki": score_bki,
            "bki_request_cnt": bki_req,
            "region_rating": region,
            "home_address": home_a,
            "work_address": work_a,
            "income": income,
            "sna": sna,
            "first_time": first_time,
            "foreign_passport": passport,
            "default": default,
        }
    )


def preprocess_split_train_stats(
    train_df: pd.DataFrame,
) -> tuple[pd.DataFrame, dict]:
    df = train_df.copy()
    education_mode = df["education"].mode(dropna=True).iloc[0]
    df["education"] = df["education"].fillna(education_mode)
    df[["home_address", "work_address"]] = df[["home_address", "work_address"]].astype(object)

    for c in ("age", "decline_app_cnt", "bki_request_cnt", "income"):
        df[c] = np.log(pd.to_numeric(df[c], errors="coerce").fillna(0) + 1.0)

    df["app_date"] = pd.to_datetime(df["app_date"], format="%d%b%Y", errors="coerce")
    df["month"] = df["app_date"].dt.month
    month_mode = int(df["month"].mode(dropna=True).iloc[0]) if df["month"].notna().any() else 1
    df["month"] = df["month"].fillna(month_mode).astype(int)
    df["month"] = df["month"].astype(object)
    df = df.drop(columns=["app_date"])

    median_income_by_region = df.groupby("region_rating")["income"].median().to_dict()
    median_income_by_age = df.groupby("age")["income"].median().to_dict()
    median_bki_by_age = df.groupby("age")["score_bki"].median().to_dict()

    df["mean_income_region"] = df["region_rating"].map(median_income_by_region)
    fill_mr = float(df["mean_income_region"].median())
    df["mean_income_region"] = df["mean_income_region"].fillna(fill_mr)

    df["mean_income_age"] = df["age"].map(median_income_by_age)
    fill_ma = float(df["mean_income_age"].median())
    df["mean_income_age"] = df["mean_income_age"].fillna(fill_ma)

    df["mean_bki_age"] = df["age"].map(median_bki_by_age)
    fill_ba = float(df["mean_bki_age"].median())
    df["mean_bki_age"] = df["mean_bki_age"].fillna(fill_ba)

    state = {
        "version": BUNDLE_VERSION,
        "education_mode": education_mode,
        "cat_cols": CAT_COLS,
        "median_income_by_region": median_income_by_region,
        "median_income_by_age": median_income_by_age,
        "median_bki_by_age": median_bki_by_age,
        "fill_mean_income_region": fill_mr,
        "fill_mean_income_age": fill_ma,
        "fill_mean_bki_age": fill_ba,
        "month_mode": month_mode,
    }
    return df, state


def apply_test_preprocess(test_df: pd.DataFrame, state: dict) -> pd.DataFrame:
    df = test_df.copy()
    df["education"] = df["education"].fillna(state["education_mode"])
    df[["home_address", "work_address"]] = df[["home_address", "work_address"]].astype(object)

    for c in ("age", "decline_app_cnt", "bki_request_cnt", "income"):
        df[c] = np.log(pd.to_numeric(df[c], errors="coerce").fillna(0) + 1.0)

    df["app_date"] = pd.to_datetime(df["app_date"], format="%d%b%Y", errors="coerce")
    df["month"] = df["app_date"].dt.month
    df["month"] = df["month"].fillna(state["month_mode"]).astype(int)
    df["month"] = df["month"].astype(object)
    df = df.drop(columns=["app_date"])

    df["mean_income_region"] = df["region_rating"].map(state["median_income_by_region"])
    df["mean_income_region"] = df["mean_income_region"].fillna(state["fill_mean_income_region"])

    df["mean_income_age"] = df["age"].map(state["median_income_by_age"])
    df["mean_income_age"] = df["mean_income_age"].fillna(state["fill_mean_income_age"])

    df["mean_bki_age"] = df["age"].map(state["median_bki_by_age"])
    df["mean_bki_age"] = df["mean_bki_age"].fillna(state["fill_mean_bki_age"])

    return df


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, help="train.csv path (Kaggle-style columns)")
    ap.add_argument("--out", type=Path, default=None, help="joblib output path")
    ap.add_argument("--demo", action="store_true", help="train on synthetic data")
    ap.add_argument("--seed", type=int, default=10)
    ap.add_argument("--test-size", type=float, default=0.25)
    ap.add_argument(
        "--tuned",
        action="store_true",
        help="use notebook-style L2 C=500.5 (otherwise simple balanced LR)",
    )
    args = ap.parse_args()
    root = _root()
    out_path = args.out or (root / "models" / "credit_model.joblib")

    if args.demo:
        full = make_synthetic_dataset(n=1200, seed=args.seed)
    elif args.data:
        p = args.data if args.data.is_absolute() else root / args.data
        if not p.is_file():
            print(f"File not found: {p}", file=sys.stderr)
            return 1
        full = pd.read_csv(p)
    else:
        print("Provide --data path or --demo", file=sys.stderr)
        return 1

    if "default" not in full.columns:
        print("Dataset must include 'default' column", file=sys.stderr)
        return 1

    train_raw, test_raw = train_test_split(
        full,
        test_size=args.test_size,
        stratify=full["default"],
        random_state=args.seed,
        shuffle=True,
    )

    train_fe, state = preprocess_split_train_stats(train_raw)
    test_fe = apply_test_preprocess(test_raw, state)

    train_d = pd.get_dummies(train_fe, columns=CAT_COLS, drop_first=True)
    X_train = train_d.drop(columns=["client_id", "default"], errors="ignore")
    y_train = train_d["default"]

    test_d = pd.get_dummies(test_fe, columns=CAT_COLS, drop_first=True)
    X_test = test_d.reindex(columns=X_train.columns, fill_value=0)
    y_test = test_d["default"]

    state["column_order"] = X_train.columns.tolist()

    if args.tuned:
        model = LogisticRegression(
            class_weight="balanced",
            C=500.5,
            penalty="l2",
            solver="lbfgs",
            max_iter=400,
            random_state=args.seed,
        )
    else:
        model = LogisticRegression(
            class_weight="balanced",
            max_iter=2000,
            solver="lbfgs",
            random_state=args.seed,
        )

    model.fit(X_train, y_train)
    proba = model.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, proba)
    print(f"holdout ROC-AUC: {auc:.4f}  rows_train={len(X_train)} rows_test={len(X_test)}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    bundle = {"version": BUNDLE_VERSION, "model": model, "state": state}
    joblib.dump(bundle, out_path)
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
