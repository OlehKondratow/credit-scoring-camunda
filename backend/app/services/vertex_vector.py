"""
Vertex AI: query embedding (text-embedding-004) and optional Vector Search neighbors.
When index endpoint + deployed index are not configured, callers should fall back to mock retrieval.

Neighbor responses contain datapoint IDs; mapping ID → chunk text requires a sidecar store (GCS/DB)
or Vertex AI Search with data store — see doc/ml-data-rag.md.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from app.config import get_settings

logger = logging.getLogger(__name__)


def embed_query_sync(text: str) -> list[float]:
    """768-dim embedding for text-embedding-004."""
    settings = get_settings()
    if not settings.google_cloud_project:
        raise RuntimeError("GOOGLE_CLOUD_PROJECT not set")

    import vertexai
    from vertexai.language_models import TextEmbeddingModel

    vertexai.init(project=settings.google_cloud_project, location=settings.google_cloud_region)
    model = TextEmbeddingModel.from_pretrained(settings.embedding_model)
    emb = model.get_embeddings([text])[0]
    vals = getattr(emb, "values", None)
    if vals is None:
        return [0.0] * 768
    return list(vals)


async def find_neighbors_async(
    embedding: list[float],
    *,
    top_k: int,
) -> list[dict[str, Any]]:
    """
    Calls Matching Engine index endpoint if configured. Returns list of {id, distance, ...}.
    Empty list if not configured or on error (caller falls back to mock RAG).
    """
    settings = get_settings()
    endpoint = (settings.vector_index_endpoint_id or "").strip()
    deployed = (settings.vector_deployed_index_id or "").strip()
    if not endpoint or not deployed:
        return []

    def _call() -> list[dict[str, Any]]:
        from google.cloud import aiplatform

        aiplatform.init(
            project=settings.google_cloud_project,
            location=settings.google_cloud_region,
        )
        ep = aiplatform.MatchingEngineIndexEndpoint(index_endpoint_name=endpoint)
        # queries: one query = one dense vector (768 floats for text-embedding-004).
        resp = ep.find_neighbors(
            deployed_index_id=deployed,
            queries=[embedding],
            num_neighbors=top_k,
        )
        out: list[dict[str, Any]] = []
        if not resp:
            return out
        for neighbor_list in resp:
            for n in neighbor_list:
                out.append(
                    {
                        "id": getattr(n, "id", ""),
                        "distance": getattr(n, "distance", None),
                        "embedding_metadata": getattr(n, "embedding_metadata", None),
                    }
                )
        return out[:top_k]

    try:
        return await asyncio.to_thread(_call)
    except Exception:
        logger.exception("vertex_find_neighbors_failed")
        return []


async def vector_search_with_resolved_text(
    query: str,
    *,
    product_type: str | None,
    top_k: int,
    text_resolver: dict[str, str],
    metadata_by_id: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """
    Runs vector search and attaches text from text_resolver (datapoint_id -> chunk text).
    metadata_by_id can supply chunk metadata (e.g. source, product_type) from export / index.
    """
    emb = await asyncio.to_thread(embed_query_sync, query)
    neighbors = await find_neighbors_async(emb, top_k=top_k)
    results: list[dict[str, Any]] = []
    meta = metadata_by_id or {}
    for n in neighbors:
        nid = str(n.get("id", ""))
        text = text_resolver.get(nid, "")
        md = dict(meta.get(nid, {}))
        if not text:
            text = f"[chunk {nid}]"
        results.append(
            {
                "id": nid,
                "score": 1.0 - float(n.get("distance") or 0.0),
                "text": text,
                "metadata": md,
            }
        )
    if product_type:
        results = [
            r
            for r in results
            if r["metadata"].get("product_type") in (product_type, "Ogólne")
            or product_type in r.get("text", "")
        ]
    return results[:top_k]
