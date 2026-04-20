"""Hybrid retrieval: semantic + metadata filters (mock or Vertex AI Vector Search)."""

from __future__ import annotations

import hashlib
import logging
from typing import Any

from app.config import get_settings
from app.services import vertex_vector

logger = logging.getLogger(__name__)

_MOCK_CHUNKS: list[dict[str, Any]] = [
    {
        "id": "m1",
        "text": "Par. 4.2 Kredyt hipoteczny może zostać udzielony, gdy dochód jest stabilny i wskaźnik DTI nie przekracza limitów banku.",
        "metadata": {"product_type": "Hipoteka", "source": "regulamin_hipoteka.pdf", "section": "4.2"},
    },
    {
        "id": "m2",
        "text": "Pożyczka gotówkowa: bank ocenia zdolność kredytową na podstawie dochodu i historii w BIK.",
        "metadata": {"product_type": "Pożyczka Gotówkowa", "source": "regulamin_pozyczka.pdf", "section": "2.1"},
    },
    {
        "id": "m3",
        "text": "Rekomendacja S KNF: instytucje powinny stosować konserwatywne parametry scoringu przy wysokim ryzyku.",
        "metadata": {"product_type": "Ogólne", "source": "knf_rekomendacja_s.pdf", "section": "S"},
    },
]


def _score_mock(query: str, chunk: dict[str, Any]) -> float:
    q = query.lower()
    t = chunk["text"].lower()
    overlap = sum(1 for w in q.split() if len(w) > 3 and w in t)
    return float(overlap)


async def _mock_hybrid_search(query: str, product_type: str | None, top_k: int) -> list[dict[str, Any]]:
    candidates = list(_MOCK_CHUNKS)
    if product_type:
        filtered = [
            c for c in candidates if c["metadata"].get("product_type") in (product_type, "Ogólne")
        ]
        if filtered:
            candidates = filtered
    ranked = sorted(candidates, key=lambda c: _score_mock(query, c), reverse=True)[:top_k]
    logger.info("retrieval_mock %s", {"k": len(ranked), "product_type": product_type})
    return [{"score": _score_mock(query, c), **c} for c in ranked]


def _mock_resolvers() -> tuple[dict[str, str], dict[str, dict[str, Any]]]:
    text = {c["id"]: c["text"] for c in _MOCK_CHUNKS}
    meta = {c["id"]: c["metadata"] for c in _MOCK_CHUNKS}
    return text, meta


async def hybrid_search(
    query: str,
    *,
    product_type: str | None,
    top_k: int = 5,
) -> list[dict[str, Any]]:
    settings = get_settings()
    use_vertex = (
        not settings.use_mock_vector_db
        and bool((settings.vector_index_endpoint_id or "").strip())
        and bool((settings.vector_deployed_index_id or "").strip())
    )
    if not use_vertex:
        return await _mock_hybrid_search(query, product_type, top_k)

    text_resolver, metadata_by_id = _mock_resolvers()
    vertex_hits = await vertex_vector.vector_search_with_resolved_text(
        query,
        product_type=product_type,
        top_k=top_k,
        text_resolver=text_resolver,
        metadata_by_id=metadata_by_id,
    )
    if not vertex_hits:
        logger.info("retrieval_vertex_empty_falling_back_to_mock")
        return await _mock_hybrid_search(query, product_type, top_k)
    if all(
        str(h.get("text", "")).startswith("[chunk ") for h in vertex_hits
    ):
        logger.warning(
            "retrieval_vertex_no_resolver_match_falling_back_to_mock",
            extra={"ids": [h.get("id") for h in vertex_hits]},
        )
        return await _mock_hybrid_search(query, product_type, top_k)

    logger.info("retrieval_vertex %s", {"k": len(vertex_hits), "product_type": product_type})
    return vertex_hits


def hash_pesel_reference(pesel: str) -> str:
    return hashlib.sha256(pesel.encode("utf-8")).hexdigest()
