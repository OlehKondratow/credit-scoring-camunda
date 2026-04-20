# Millennium Bank AI Loan Officer — план реализации

Пошаговый план от инфраструктуры до мониторинга в GKE. Регион данных: **`europe-central2` (Варшава)**.

---

### Этап 1: Инфраструктура

1. **GCP:** проект; API: Vertex AI, GKE, Artifact Registry, Cloud Storage.
2. **GKE:** **Standard** (не Autopilot) — совместимость с Camunda Platform / Zeebe. Регион `europe-central2`. См. `infra/pulumi/`, роли — `infra/ROLES.md`.
3. **Camunda 8:** SaaS или self-managed; API Client (Client ID / Secret) для Tasklist/Orchestrate.
4. **Vertex AI Vector Search:** индекс + endpoint после первой загрузки эмбеддингов в GCS (см. `data/ingest.py`).

---

### Этап 2: Данные (RAG)

1. PDF регламентов (Millennium / NBP / внутренние политики — по лицензии).
2. Чанки ~800 токенов, overlap 10%; `PyMuPDF` в `data/ingest.py`.
3. Эмбеддинги **`text-embedding-004`**; метаданные: `source`, `section`, `product_type` (фильтрация в retrieval).

---

### Этап 3: Backend (LangGraph + FastAPI)

1. Состояние графа: заявка, контекст RAG, BIK (mock), DMN-снимок, вердикт.
2. Узлы: маскирование PII → (опц.) BIK → retrieval → правила DMN-стиля → Gemini → рефлексия → ответ.
3. API: **`POST /analyze`** (`backend/`). Логи JSON → Cloud Logging.

---

### Этап 4: Camunda 8

1. **BPMN:** процесс **`millennium-loan-process`** (`bpmn/millennium-loan-process.bpmn`): service task **`ai-loan-analysis`** (retries 3), затем DMN **`scoring-rules`**.
2. Переменные процесса: **`application`** (JSON); после воркера — `risk_score`, `final_decision`, `justification_pl` и др.
3. **Worker:** `worker/` (PyZeebe). Таймаут HTTP к backend → **BPMN error** `AI_SERVICE_TIMEOUT` (fallback в модели процесса).

---

### Этап 5: UI и наблюдаемость

1. **Streamlit** (`ui/`): Tasklist API или mock; explainability (фрагменты RAG + uzasadnienie).
2. **Compliance (EU/PL):** польский UI/ответы; PESEL/PII не в LLM без маскирования; human-in-the-loop для крупных решений (KNF).

---

### Этап 6: Деплой

1. Образы: `backend`, `worker`, `ui` → Artifact Registry.
2. **Kubernetes:** `k8s/millennium/` — Deployment, Service, HPA, Secret; Workload Identity для backend.
3. Секреты: Gemini / Camunda через Kubernetes Secrets, не в git.

---

### Структура репозитория (фактическая)

| Путь | Назначение |
|------|------------|
| `infra/pulumi/` | Pulumi (основной IaC: GCS, Artifact Registry, API); роли — `infra/ROLES.md` |
| `backend/` | FastAPI + LangGraph |
| `worker/` | PyZeebe |
| `ui/` | Streamlit |
| `data/` | Ingest PDF |
| `bpmn/`, `dmn/` | Модели Camunda |
| `k8s/millennium/` | Манифесты |
| `docker-compose.yml` | Локально: Zeebe + сервисы |

---

### Чеклист качества

- Retries на service task (3) в BPMN.
- Тесты на маскирование PII.
- Probes в K8s; readiness backend осмысленно (не только `/healthz` при необходимости Vertex).
- Учёт токенов/стоимости в логах для продакшена.

---

### Сценарий end-to-end

1. Заявка (Streamlit или API) → старт процесса Camunda.
2. Воркер вызывает backend: RAG + Gemini → `risk_score`, uzasadnienie po polsku.
3. DMN классифициuje `risk_score` → `riskTier`.
4. Analityk w Tasklist — **Potwierdź** przy decyzji manualnej.

MVP: zacznij od **ingestion** (etap 2), potem podłącz Vector Search i wyłącz mocki w backendzie.
