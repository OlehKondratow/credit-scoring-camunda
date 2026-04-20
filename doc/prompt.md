# Millennium Bank AI Loan Officer — контекст для продолжения работы

Краткий handoff для нового чата: что за проект, как устроен **`infra/`**, Git, ограничения и что делать дальше.

---

## 1. Продукт

**Автоматизированное кредитное решение:** RAG (Vertex AI) + **Camunda 8 / Zeebe** + FastAPI (LangGraph) + Streamlit, деплой в **GKE**, регион данных **`europe-central2` (Warsaw)**.

---

## 2. Репозиторий Git (важно)

| Что | Значение |
|-----|-----------|
| **Remote** | `git@github.com:OlehKondratow/credit-scoring-camunda.git` |
| **Default branch на GitHub** | **`millennium-credit-v2`** — актуальный код Millennium (RAG, Pulumi, новый worker/UI). |
| **Ветка `main`** | Сохранена **старая** линия (классический Camunda 8 credit scoring demo). **Не** затирать force-push без необходимости. |
| **Тег релиза** | **`v1.0.0`** — снимок нового контура (при необходимости обновлять осторожно на remote). |

Клон по умолчанию тянет **`millennium-credit-v2`**. Старая история: `git fetch origin main && git switch main`.

---

## 3. Каталог `infra/` (источник правды по IaC)

| Путь | Назначение |
|------|------------|
| **`infra/pulumi/`** | **Основной IaC (Python).** GCS (embeddings + raw PDF), BigQuery `millennium_analytics`, Artifact Registry; включение API: **storage**, **bigquery**, **aiplatform**, **artifactregistry**. Конфиг: `pulumi config set gcp:project …`, `credit-scoring:region`, `credit-scoring:clusterName`. Venv: **`infra/pulumi/venv`** (`Pulumi.yaml`: `virtualenv: venv`). |
| **`infra/pulumi/README.md`** | Запуск, экспорты (`vector_embeddings_bucket`, `raw_regulations_bucket`, `bigquery_dataset`, `artifact_registry_url`), отладка `pulumi preview`. |
| **`infra/README.md`** | Обзор: Pulumi = основной путь; остальное — справочно. |
| **`infra/ARCHITECTURE.md`** | Изоляция: GCP project / state / namespace; OIDC вместо JSON-ключей; GitOps (Argo/Flux) — по желанию для приложений; Terraform в тексте исторически — для prod применять **Pulumi** как канон. |
| **`infra/ROLES.md`** | Полный список ролей (в т.ч. security/compliance, break-glass, release-manager, data-engineer, ML Engineer) + матрица GCP/Pulumi/K8s/Git. |
| **`infra/terraform/`** | **Справочный** HCL; не плодить второй источник правды с Pulumi на одних и тех же именах ресурсов без импорта. |
| **`infra/cdktf/`**, **`config-connector/`**, **`crossplane/`** | Примеры/альтернативы, опционально. |

**Кластер:** планируется **GKE Standard** (не **Autopilot**) — совместимость с Camunda Platform / Zeebe. Сам кластер в этом репо описан концептуально; создание — отдельный слой (раньше Terraform/GKE модули, в продолжении — согласовать с Pulumi или отдельным модулем).

---

## 4. Прикладной код (фактическая структура)

| Путь | Назначение |
|------|------------|
| `backend/` | FastAPI + LangGraph, `POST /analyze`; retrieval: mock или Vertex (`USE_MOCK_VECTOR_DB`, `VECTOR_INDEX_ENDPOINT_ID`, `VECTOR_DEPLOYED_INDEX_ID`). См. `backend/app/services/retrieval.py`, `vertex_vector.py`. |
| `worker/` | PyZeebe, job type **`ai-loan-analysis`**, таймаут → BPMN error **`AI_SERVICE_TIMEOUT`**. |
| `ui/` | Streamlit. |
| `data/` | `ingest.py`, `eval_rag.py`; зависимости: `pip install -r ../backend/requirements.txt -r requirements.txt` для eval. |
| `bpmn/`, `dmn/` | `millennium-loan-process.bpmn`, `scoring-rules.dmn`. |
| `k8s/millennium/` | Манифесты K8s. |
| `docker-compose.yml` | Локально: Zeebe + backend + worker + UI. |
| `doc/ml-data-rag.md` | ML/Data/RAG и env backend. |

---

## 5. План реализации (этапы — что ещё добивать)

1. **GCP / Pulumi:** `pulumi up` в dev; при необходимости отдельные стеки staging/prod; state backend для команд.  
2. **GKE Standard** + деплой образов из Artifact Registry; Workload Identity + секреты (Gemini, Camunda) не в git.  
3. **Данные RAG:** PDF → GCS raw → `data/ingest.py` → эмбеддинги → индекс **Vertex Vector Search** + endpoint; выключить моки в backend.  
4. **Camunda:** деплой BPMN/DMN; секреты клиента Orchestration/Tasklist.  
5. **Наблюдаемость / compliance:** логи JSON → Cloud Logging; BigQuery для аналитики без сырого PII.

---

## 6. Чеклист качества (напоминание)

- BPMN: retries на service task к AI (например 3).  
- Тесты на маскирование PII.  
- Probes в K8s; readiness осмысленный при Vertex.  
- Учёт токенов/стоимости в проде.

---

## 7. Сценарий E2E (целевой)

1. Заявка (Streamlit или API) → процесс Camunda.  
2. Worker дергает backend: RAG + LLM → `risk_score`, uzasadnienie PL.  
3. DMN по `risk_score` → уровень риска / маршрут.  
4. Аналитик в Tasklist при ручном шаге.

**MVP-порядок:** ingestion → индекс Vertex → отключить mock Vector DB → интеграционные тесты worker ↔ backend.

---

## 8. CLI / console

Команды для терминала (Docker, Pulumi, `gcloud`/`kubectl`, push образов): **[doc/cli-console.md](cli-console.md)**.

---

*Документ обновлён для переноса контекста в новый диалог; детали IaC — в `infra/`, RAG — в `doc/ml-data-rag.md`, шпаргалка CLI — в `doc/cli-console.md`.*
