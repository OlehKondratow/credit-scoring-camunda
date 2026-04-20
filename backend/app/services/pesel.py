"""Polish PESEL helpers (age only — do not log raw PESEL)."""

from __future__ import annotations

import datetime as dt


def pesel_age_years(pesel: str, today: dt.date | None = None) -> int | None:
    """Return age in full years from PESEL or None if invalid."""
    if len(pesel) != 11 or not pesel.isdigit():
        return None
    y = int(pesel[0:2])
    m = int(pesel[2:4])
    d = int(pesel[4:6])
    if m < 1 or m > 32 or d < 1 or d > 31:
        return None
    # century encoding
    if 1 <= m <= 12:
        century = 1900
        month = m
    elif 21 <= m <= 32:
        century = 2000
        month = m - 20
    elif 41 <= m <= 52:
        century = 2100
        month = m - 40
    elif 61 <= m <= 72:
        century = 2200
        month = m - 60
    elif 81 <= m <= 92:
        century = 1800
        month = m - 80
    else:
        return None
    year = century + y
    try:
        birth = dt.date(year, month, d)
    except ValueError:
        return None
    today = today or dt.date.today()
    age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
    return max(0, age)
