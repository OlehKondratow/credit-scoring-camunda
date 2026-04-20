"""LangGraph: Mask_PII -> Retrieve -> DMN -> LLM -> Reflect -> Format."""

from __future__ import annotations

import logging
from typing import Any

from langgraph.graph import END, StateGraph

from app.config import get_settings
from app.graph.state import AgentState
from app.services import dmn_rules, pesel, pii, retrieval
from app.services.bik_mock import fetch_bik_summary

logger = logging.getLogger(__name__)


async def _mask_pii(state: AgentState) -> AgentState:
    raw = state.get("application_raw") or {}
    pesel_raw = str(raw.get("pesel") or raw.get("PESEL") or "")
    age = pesel.pesel_age_years(pesel_raw) if pesel_raw.isdigit() and len(pesel_raw) == 11 else None
    masked = pii.mask_application_payload(raw)
    return {
        **state,
        "applicant_age": age,
        "application_masked": masked,
        "error": None,
    }


async def _fetch_bik(state: AgentState) -> AgentState:
    raw = state.get("application_raw") or {}
    pesel_raw = str(raw.get("pesel") or raw.get("PESEL") or "")
    h = retrieval.hash_pesel_reference(pesel_raw) if pesel_raw else "unknown"
    bik = await fetch_bik_summary(h)
    return {**state, "bik": bik}


async def _retrieve(state: AgentState) -> AgentState:
    masked = state.get("application_masked") or {}
    product = str(masked.get("product_type") or masked.get("product") or "")
    income = masked.get("income")
    debt = masked.get("debt")
    q = f"Ocena zdolności kredytowej; dochód {income}; zobowiązania {debt}; produkt {product}"
    settings = get_settings()
    chunks = await retrieval.hybrid_search(q, product_type=product or None, top_k=settings.mock_vector_top_k)
    return {**state, "retrieved_chunks": chunks}


async def _dmn_rules(state: AgentState) -> AgentState:
    masked = state.get("application_masked") or {}
    product = str(masked.get("product_type") or masked.get("product") or "")
    dmn = dmn_rules.evaluate_dmn(
        age_years=state.get("applicant_age"),
        product_type=product,
        bik=state.get("bik") or {},
    )
    return {**state, "dmn": dmn}


async def _llm_reason(state: AgentState) -> AgentState:
    settings = get_settings()
    chunks = state.get("retrieved_chunks") or []
    ctx = "\n".join(f"- {c.get('text')}" for c in chunks[:8])
    dmn = state.get("dmn") or {}
    bik = state.get("bik") or {}

    if settings.use_mock_llm or not settings.google_cloud_project:
        reasoning = (
            "Wstępna ocena (symulacja LLM): na podstawie fragmentów regulaminu i danych wejściowych "
            f"proponuję kontynuację analizy. DMN: {dmn.get('decision')}. BIK (symulacja): {bik.get('risk_hint')}."
        )
        return {**state, "llm_reasoning_pl": reasoning}

    try:
        from langchain_google_vertexai import ChatVertexAI

        llm = ChatVertexAI(
            model_name=settings.llm_model,
            project=settings.google_cloud_project,
            location=settings.google_cloud_region,
        )
        system = (
            "Jesteś analitykiem kredytowym Banku Millennium. Odpowiadaj po polsku. "
            "Uwzględnij Rekomendację S KNF oraz polskie Prawo bankowe tylko jako ogólne zasady etyki kredytu. "
            "Korzystaj wyłącznie z podanego kontekstu dokumentów wewnętrznych."
        )
        human = f"Kontekst dokumentów:\n{ctx}\n\nWynik reguł (DMN): {dmn}\nSymulacja BIK: {bik}\nDane (zanonimizowane): {state.get('application_masked')}"
        msg = llm.invoke([("system", system), ("human", human)])
        text = getattr(msg, "content", str(msg))
        return {**state, "llm_reasoning_pl": str(text)}
    except Exception as e:  # noqa: BLE001
        logger.exception("llm_invoke_failed")
        return {**state, "llm_reasoning_pl": f"Nie udało się wywołać modelu ({e!s}). Użyj trybu mock."}


async def _reflect(state: AgentState) -> AgentState:
    settings = get_settings()
    base = state.get("llm_reasoning_pl") or ""
    if settings.use_mock_llm or not settings.google_cloud_project:
        reflection = (
            "Refleksja: odpowiedź jest spójna z kontekstem RAG i nie zawiera danych osobowych. "
            "Należy zweryfikować zgodność z aktualnymi przepisami w produkcji."
        )
        return {**state, "reflection_pl": reflection}
    try:
        from langchain_google_vertexai import ChatVertexAI

        llm = ChatVertexAI(
            model_name=settings.llm_model,
            project=settings.google_cloud_project,
            location=settings.google_cloud_region,
        )
        prompt = (
            "Oceń krytycznie poniższą rekomendację pod kątem zgodności z Rekomendacją S KNF "
            "i polskim Prawem bankowym (wysokie poziom). Zwróć 2–3 zdania po polsku.\n\n"
            f"Rekomendacja:\n{base}"
        )
        msg = llm.invoke(prompt)
        text = getattr(msg, "content", str(msg))
        return {**state, "reflection_pl": str(text)}
    except Exception as e:  # noqa: BLE001
        return {**state, "reflection_pl": f"Refleksja niedostępna: {e!s}"}


async def _format(state: AgentState) -> AgentState:
    dmn = state.get("dmn") or {}
    decision = dmn.get("decision")
    bik = state.get("bik") or {}
    income = float((state.get("application_masked") or {}).get("income") or 0)
    debt = float((state.get("application_masked") or {}).get("debt") or 0)
    dti = (debt / income) if income > 0 else 1.0
    risk = int(max(0, min(100, round(100 - dti * 120))))
    if bik.get("overdue_installments_90d", 0) and bik.get("overdue_installments_90d", 0) > 0:
        risk = min(risk, 40)
    if decision == "REJECT":
        final: Any = "REJECTED"
    elif decision == "REVIEW":
        final = "MANUAL"
    else:
        final = "APPROVED" if risk >= 55 else "MANUAL"

    justification = (
        f"Rekomendacja modelu: {state.get('llm_reasoning_pl', '')[:800]}\n\n"
        f"Refleksja zgodności: {state.get('reflection_pl', '')}\n\n"
        f"Reguły DMN: {decision}. BIK (symulacja): {bik.get('message_pl', '')}"
    )
    cot = (
        "Łańcuch rozumowania: (1) maskowanie PII, (2) symulacja BIK, "
        "(3) wyszukiwanie hybrydowe RAG, (4) reguły DMN, (5) rozumowanie LLM, (6) refleksja."
    )
    return {
        **state,
        "risk_score": risk,
        "final_decision": final,
        "justification_pl": justification.strip(),
        "chain_of_thought_pl": cot,
    }


def build_graph():
    g = StateGraph(AgentState)
    g.add_node("mask_pii", _mask_pii)
    g.add_node("fetch_bik", _fetch_bik)
    g.add_node("retrieve", _retrieve)
    g.add_node("dmn_rules", _dmn_rules)
    g.add_node("llm", _llm_reason)
    g.add_node("reflect", _reflect)
    g.add_node("format", _format)

    g.set_entry_point("mask_pii")
    g.add_edge("mask_pii", "fetch_bik")
    g.add_edge("fetch_bik", "retrieve")
    g.add_edge("retrieve", "dmn_rules")
    g.add_edge("dmn_rules", "llm")
    g.add_edge("llm", "reflect")
    g.add_edge("reflect", "format")
    g.add_edge("format", END)

    return g.compile()


GRAPH = build_graph()
