"""Mask Polish PII before external LLM calls (GDPR-oriented heuristic layer)."""

from __future__ import annotations

import copy
import re

_PESEL_RE = re.compile(r"\b\d{11}\b")
# Very rough street / postal patterns (Polish context)
_ADDRESS_HINT = re.compile(
    r"\b(ul\.?|al\.?|os\.?)\s+[\w\s\-\.]+,?\s*\d{2}-\d{3}\s+[\w\s\-]+\b",
    re.IGNORECASE,
)


def mask_pesel(text: str) -> str:
    return _PESEL_RE.sub("[PESEL]", text)


def mask_names(text: str) -> str:
    """Heuristic: lines like 'Imię i nazwisko: Jan Kowalski'."""
    out = text
    out = re.sub(
        r"(?im)^(Imię\s+i\s+nazwisko|Nazwisko|Imię)\s*:\s*.+$",
        r"\1: [NAZWISKO]",
        out,
    )
    return out


def mask_addresses(text: str) -> str:
    return _ADDRESS_HINT.sub("[ADRES]", text)


def mask_application_payload(payload: dict) -> dict:
    """Return shallow-copied dict with sensitive fields redacted for logging/LLM."""
    data = copy.deepcopy(payload)
    for key in ("pesel", "PESEL", "pesel_number"):
        if key in data and data[key]:
            data[key] = "[PESEL]"
    for key in ("full_name", "imie_nazwisko", "applicant_name"):
        if key in data and data[key]:
            data[key] = "[IMIĘ_NAZWISKO]"
    for key in ("address", "adres"):
        if key in data and data[key]:
            data[key] = "[ADRES]"
    notes = data.get("notes") or data.get("uwagi")
    if isinstance(notes, str):
        t = mask_pesel(notes)
        t = mask_addresses(t)
        if "notes" in data:
            data["notes"] = t
        if "uwagi" in data:
            data["uwagi"] = t
    return data


def mask_free_text(text: str) -> str:
    t = mask_pesel(text)
    t = mask_addresses(t)
    t = mask_names(t)
    return t
