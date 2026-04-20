# ML, Data & RAG (Vertex AI, GCP)

Регион данных по умолчанию: **`europe-central2`**. Код и переменные окружения — в `backend/`, пайплайн данных — в `data/`, инфраструктура — в `infra/pulumi/`.

---

## 1. Компоненты

| Слой | Технология | Назначение |
|------|------------|------------|
| **Источники** | PDF регламенты, NBP, внутренние политики (по лицензии) | Сырой текст для RAG |
| **Landing** | **GCS** bucket `raw-pdfs` (Pulumi: `raw_regulations_bucket`) | Неизменяемое хранение PDF |
| **Обработка** | `data/ingest.py` — PyMuPDF, чанки, overlap | Подготовка к эмбеддингам |
| **Эмбеддинги** | **`text-embedding-004`** (768 dim) | Векторизация для Vector Search |
| **Векторный индекс** | **Vertex AI Vector Search** (Matching Engine) | Семантический поиск + фильтры по метаданным |
| **Гибридный поиск** | metadata `product_type`, `source`, `section` | Ограничение домена (Hipoteka vs Pożyczka) |
| **LLM** | **Gemini 1.5 Pro** (Vertex) | Рассуждение с ограничением по контексту RAG |
| **Аналитика / eval** | **BigQuery** dataset `millennium_analytics` | Логи запросов, offline-оценка качества, стоимость токенов |
| **Оркестрация приложения** | LangGraph в `backend/` | Mask PII → retrieve → rules → LLM → reflect |

---

## 2. Поток данных (RAG)

```text
PDF → GCS (raw) → chunk → embed (text-embedding-004) → JSONL / batch →
→ Vertex Vector Search index deploy → backend retrieve → Gemini → odpowiedź PL
```

**Оценка качества (offline):** `data/eval_rag.py` — вопросы с эталонным `source`; метрика hit@k по попаданию источника в top-k.

---

## 3. Конфигурация backend (env)

| Переменная | Описание |
|------------|----------|
| `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_REGION` | Vertex / GCS |
| `USE_MOCK_VECTOR_DB` | `true` — без Vector Search |
| `VECTOR_INDEX_ENDPOINT_ID` | Полный resource name endpoint |
| `VECTOR_DEPLOYED_INDEX_ID` | ID деплоя индекса на endpoint |
| `EMBEDDING_MODEL` | По умолчанию `text-embedding-004` |

---

## 4. Роли (расширение)

См. **`infra/ROLES.md`**: **ML Engineer**, **Data Engineer** — доступ к Vertex, BigQuery, бакетам; без `container.admin`, если не нужен GKE.

---

## 5. Соответствие регуляторам (EU/PL)

- Данные и индексы в **EU** (`europe-central2`).
- PII не в логах BigQuery в открытом виде — только хеши/псевдонимы.
- Обоснование решений на польском — для audytu (см. основной `doc/prompt.md`).

---

## 6. Ссылки по коду

| Путь | Содержимое |
|------|------------|
| `data/ingest.py` | Ingest PDF → JSONL эмбеддингов |
| `data/eval_rag.py` | Offline eval hit@k (mock или сопоставление с источником) |
| `backend/app/services/retrieval.py` | Гибридный поиск |
| `backend/app/services/vertex_vector.py` | Эмбеддинг запроса + вызов Vector Search (когда настроено) |
| `infra/pulumi/__main__.py` | GCS (raw + embeddings), BigQuery, API |
