#!/usr/bin/env python3
"""
Offline RAG evaluation: check if ground-truth source appears in top-k retrieved chunks.
Uses the same mock corpus as backend retrieval.

Usage:
  cd data && python eval_rag.py --questions fixtures/questions_sample.jsonl
  # Or: PYTHONPATH=../backend python eval_rag.py ...
Dependencies: install backend deps (e.g. pip install -r ../backend/requirements.txt).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))


async def _run(question: str, product_type: str | None, top_k: int) -> list[dict]:
    from app.services.retrieval import hybrid_search

    return await hybrid_search(question, product_type=product_type, top_k=top_k)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--questions", type=Path, required=True, help="JSONL: question, ground_truth_source, optional product_type")
    p.add_argument("--top-k", type=int, default=5)
    args = p.parse_args()

    if not args.questions.is_file():
        print("File not found:", args.questions, file=sys.stderr)
        sys.exit(1)

    hits = 0
    total = 0
    for line in args.questions.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        q = row["question"]
        want = row.get("ground_truth_source", "")
        pt = row.get("product_type")
        total += 1
        got = asyncio.run(_run(q, pt, args.top_k))
        sources = [c.get("metadata", {}).get("source", "") for c in got]
        ok = any(want in s or s in want for s in sources if want)
        if ok:
            hits += 1
        print(f"{'OK' if ok else 'MISS'}  {q[:60]}...  sources={sources}")

    print(f"\nhit@{args.top_k} (source match): {hits}/{total}")


if __name__ == "__main__":
    main()
