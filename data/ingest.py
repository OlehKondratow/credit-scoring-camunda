#!/usr/bin/env python3
"""
Ingest public PDF regulations, chunk text, embed with text-embedding-004, export JSONL for Vertex Vector Search batch upload.
Metadata supports hybrid filtering: product_type (e.g. Hipoteka, Pożyczka Gotówkowa).

Usage:
  export GOOGLE_CLOUD_PROJECT=...
  export GOOGLE_CLOUD_REGION=europe-central2
  python ingest.py --pdf-dir ./pdfs --out gs://bucket/prefix/embeddings.jsonl

Local test without GCP:
  python ingest.py --pdf-dir ./pdfs --out ./out/embeddings.jsonl --dry-run
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("ingest")

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None  # type: ignore[assignment]


def chunk_text(text: str, max_chars: int = 3200, overlap_ratio: float = 0.1) -> list[str]:
    """Character-based chunks (~800 tokens heuristic at ~4 chars/token)."""
    if not text.strip():
        return []
    overlap = int(max_chars * overlap_ratio)
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + max_chars)
        chunks.append(text[start:end].strip())
        if end >= len(text):
            break
        start = max(0, end - overlap)
    return [c for c in chunks if c]


def embed_texts_vertex(texts: list[str], project: str, region: str) -> list[list[float]]:
    import vertexai
    from vertexai.language_models import TextEmbeddingModel

    vertexai.init(project=project, location=region)
    model = TextEmbeddingModel.from_pretrained("text-embedding-004")
    out: list[list[float]] = []
    batch = 16
    for i in range(0, len(texts), batch):
        part = texts[i : i + batch]
        emb = model.get_embeddings(part)
        for e in emb:
            vals = getattr(e, "values", None)
            if vals is not None:
                out.append(list(vals))
            else:
                out.append([0.0] * 768)
    return out


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--pdf-dir", type=Path, required=True)
    p.add_argument("--out", type=str, required=True, help="Local path or gs://bucket/prefix/file.jsonl")
    p.add_argument("--product-type", type=str, default="Hipoteka", help="Metadata filter: product_type")
    p.add_argument("--dry-run", action="store_true", help="Skip Vertex embedding API (zero vectors).")
    args = p.parse_args()

    if fitz is None:
        log.error("PyMuPDF (fitz) required.")
        sys.exit(1)

    project = os.environ.get("GOOGLE_CLOUD_PROJECT", "")
    region = os.environ.get("GOOGLE_CLOUD_REGION", "europe-central2")

    records: list[dict] = []
    for pdf in sorted(args.pdf_dir.glob("*.pdf")):
        doc = fitz.open(pdf)
        full = "".join(page.get_text() for page in doc)
        doc.close()
        for i, ch in enumerate(chunk_text(full)):
            rid = hashlib.sha256(f"{pdf.name}-{i}".encode()).hexdigest()[:24]
            records.append(
                {
                    "id": rid,
                    "text": ch,
                    "metadata": {
                        "source": pdf.name,
                        "section": str(i),
                        "product_type": args.product_type,
                    },
                }
            )

    texts = [r["text"] for r in records]
    if args.dry_run or not project:
        vectors = [[0.0] * 768 for _ in texts]
        log.info("dry_run: %s chunks, zero vectors", len(texts))
    else:
        import vertexai

        vertexai.init(project=project, location=region)
        vectors = embed_texts_vertex(texts, project, region)

    lines = []
    for r, vec in zip(records, vectors, strict=True):
        lines.append(
            json.dumps(
                {
                    "id": r["id"],
                    "embedding": vec,
                    "restricts": [],
                    "metadata": r["metadata"],
                    "text": r["text"][:500],
                },
                ensure_ascii=False,
            )
        )

    out = args.out
    if out.startswith("gs://"):
        from google.cloud import storage

        bucket, _, blob = out.replace("gs://", "").partition("/")
        client = storage.Client(project=project)
        b = client.bucket(bucket)
        b.blob(blob).upload_from_string("\n".join(lines) + "\n", content_type="application/jsonl")
        log.info("uploaded gs://%s/%s", bucket, blob)
    else:
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        Path(out).write_text("\n".join(lines) + "\n", encoding="utf-8")
        log.info("wrote %s lines -> %s", len(lines), out)


if __name__ == "__main__":
    main()
