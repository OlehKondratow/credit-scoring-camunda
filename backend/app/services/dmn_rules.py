"""Deterministic checks aligned with DMN-style rules (age, product, BIK mock signals)."""

from __future__ import annotations

from typing import Any, Literal


def evaluate_dmn(
    *,
    age_years: int | None,
    product_type: str,
    bik: dict[str, Any],
) -> dict[str, Any]:
    """
    Returns structured DMN outcome. Polish messages for officer transparency.
    """
    reasons: list[str] = []
    passed = True

    if age_years is None:
        passed = False
        reasons.append("Brak możliwości ustalenia wieku (PESEL).")
    elif age_years < 18:
        passed = False
        reasons.append("Wymóg pełnoletności: klient poniżej 18 lat.")

    overdue = int(bik.get("overdue_installments_90d") or 0)
    if overdue > 0:
        passed = False
        reasons.append("BIK (symulacja): przeterminowane raty w oknie 90 dni.")

    product = (product_type or "").strip()
    if product and product not in ("Hipoteka", "Pożyczka Gotówkowa", "Kredyt konsumencki"):
        reasons.append(f"Niestandardowy produkt w żądaniu: {product} — wymagana ręczna weryfikacja.")

    decision: Literal["PASS", "REJECT", "REVIEW"] = "PASS"
    if not passed:
        decision = "REJECT"
    elif any("Niestandardowy" in r for r in reasons):
        decision = "REVIEW"

    return {
        "decision": decision,
        "reasons_pl": reasons,
        "product_type": product,
    }
