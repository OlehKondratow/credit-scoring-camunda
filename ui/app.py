"""
Internal Streamlit portal for credit officers (Polish UI).
Fetches tasks from Camunda Tasklist REST API (OAuth2 client credentials in production).
"""

from __future__ import annotations

import json
import logging
import os
import sys
from typing import Any

import httpx
import streamlit as st

logging.basicConfig(stream=sys.stdout, level=os.environ.get("LOG_LEVEL", "INFO"))
log = logging.getLogger("ui")

TASKLIST_BASE = os.environ.get("CAMUNDA_TASKLIST_BASE_URL", "http://localhost:8082").rstrip("/")
TASKLIST_TOKEN = os.environ.get("CAMUNDA_TASKLIST_TOKEN", "")


def _headers() -> dict[str, str]:
    h = {"Content-Type": "application/json", "Accept": "application/json"}
    if TASKLIST_TOKEN:
        h["Authorization"] = f"Bearer {TASKLIST_TOKEN}"
    return h


@st.cache_data(ttl=30)
def fetch_tasks_mock() -> list[dict[str, Any]]:
    """Placeholder when Tasklist is not reachable (local demo)."""
    return [
        {
            "id": "demo-1",
            "name": "Weryfikacja analityka",
            "processName": "Millennium — kredyt",
            "creationDate": "2026-04-20T10:00:00Z",
            "variables": {
                "final_decision": "MANUAL",
                "risk_score": 62,
                "justification_pl": "Przykładowa treść uzasadnienia po polsku.",
            },
        }
    ]


def fetch_tasks_live() -> list[dict[str, Any]]:
    try:
        with httpx.Client(timeout=15.0) as c:
            r = c.get(f"{TASKLIST_BASE}/v1/tasks/search", headers=_headers(), json={"state": "CREATED"})
        if r.status_code != 200:
            log.warning("tasklist_http_%s", r.status_code)
            return fetch_tasks_mock()
        return r.json()
    except Exception as e:  # noqa: BLE001
        log.warning("tasklist_fallback %s", e)
        return fetch_tasks_mock()


def main() -> None:
    st.set_page_config(page_title="Millennium — decyzje kredytowe", layout="wide")
    st.title("Portal wewnętrzny — obsługa wniosków")
    st.caption("Region danych: europe-central2 (Warszawa). Język interfejsu: polski.")

    use_mock = os.environ.get("TASKLIST_USE_MOCK", "true").lower() == "true"
    tasks = fetch_tasks_mock() if use_mock else fetch_tasks_live()

    for t in tasks:
        with st.expander(f"Zadanie: {t.get('name', '—')} ({t.get('id', '')})"):
            st.write("**Proces:**", t.get("processName", "—"))
            st.write("**Utworzono:**", t.get("creationDate", "—"))
            vars_ = t.get("variables") or {}
            if isinstance(vars_, str):
                try:
                    vars_ = json.loads(vars_)
                except json.JSONDecodeError:
                    vars_ = {}
            st.metric("Ocena ryzyka (0–100)", vars_.get("risk_score", "—"))
            st.write("**Decyzja:**", vars_.get("final_decision", "—"))
            st.subheader("Uzasadnienie (PL)")
            st.write(vars_.get("justification_pl", "Brak danych."))
            st.subheader("Łańcuch rozumowania / explainability")
            st.write(vars_.get("chain_of_thought_pl", "—"))
            chunks = vars_.get("retrieved_chunks") or vars_.get("chunks")
            if chunks:
                st.subheader("Fragmenty dokumentów (RAG)")
                for i, ch in enumerate(chunks[:10], 1):
                    meta = ch.get("metadata", {}) if isinstance(ch, dict) else {}
                    st.markdown(f"**{i}.** `{meta.get('source', '')}` §{meta.get('section', '')}")
                    st.caption((ch.get("text") or "")[:800])


if __name__ == "__main__":
    main()
