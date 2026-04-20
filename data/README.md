# Data & RAG pipeline

## Структура (рекомендуемая)

```text
data/
├── README.md           # этот файл
├── requirements.txt    # зависимости ingest + eval
├── ingest.py           # PDF → чанки → text-embedding-004 → JSONL (GCS или локально)
├── eval_rag.py         # Offline оценка: hit@k по эталонному source
├── fixtures/           # Примеры (не коммитьте большие PDF из продакшена)
│   └── questions_sample.jsonl
└── pdfs/               # Локальные PDF для тестов (в .gitignore)
```

## Команды

```bash
cd data
python3 -m venv .venv && . .venv/bin/activate
pip install -r ../backend/requirements.txt -r requirements.txt

# Ingest
export GOOGLE_CLOUD_PROJECT=...
export GOOGLE_CLOUD_REGION=europe-central2
python ingest.py --pdf-dir ./pdfs --out gs://BUCKET/vector-index/embeddings.jsonl

# Eval (mock retrieval в репозитории)
python eval_rag.py --questions fixtures/questions_sample.jsonl --top-k 5
```

## Связь с Vertex

После загрузки JSONL в GCS — создание индекса и deploy на endpoint в **Console** или через gcloud (см. `doc/ml-data-rag.md`). Pulumi поднимает бакеты и BigQuery; сам индекс Matching Engine часто создают отдельным шагом из-за формата батча.
