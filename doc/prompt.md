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
| **Default branch на GitHub** | Рекомендуется **`develop`** (интеграция); **`main`** — production. См. **[doc/git-workflow.md](git-workflow.md)**, **[doc/branch-notes.md](branch-notes.md)**. |
| **Ветка `main`** | **Production** — защищённая линия для прода (см. github-setup). |
| **Тег релиза** | **`v1.0.0`** — снимок нового контура (при необходимости обновлять осторожно на remote). |

Клон по умолчанию после настройки тянет **`develop`**. Production: `git switch main`.

**Ветки, `release/*`, теги `v*`, окружения:** см. **[doc/git-workflow.md](git-workflow.md)**.

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

*Документ обновлён для переноса контекста в новый диалог; детали IaC — в `infra/`, RAG — в `doc/ml-data-rag.md`, шпаргалка CLI — в `doc/cli-console.md`, Git — в `doc/git-workflow.md`, имена репо/тегов — в `doc/naming.md`.*

---

## 9. Enterprise blueprint (расширенная цель)

Ниже — **мастер-спецификация** для enterprise-контура (IAM, GitOps, сеть, GKE). Часть пунктов **ещё не реализована** в коде репозитория; сверяйте с §1–8 и с `infra/ROLES.md`. Типичные отличия от текущего кода:

- **Camunda:** в этом репо — **Camunda 8 / Zeebe** + воркеры **Python** (`worker/`), scoring — **FastAPI + LangGraph** (`backend/`). Стек **Spring Boot + Camunda** относится к **self-managed Camunda Platform** (Operate/Tasklist/Zeebe), если вы его разворачиваете отдельно, а не к прикладному коду scoring.
- **IaC:** в репозитории Pulumi на **Python** (`infra/pulumi/`), не TypeScript. VPC / мульти-пул GKE — **отдельный слой**, не дублируйте имена ресурсов с текущим `__main__.py` без импорта.
- **Ветки:** **`develop`** (интеграция), **`main`** (prod), `release/*`, `feature/*`, `hotfix/*` — см. §2 и **[doc/git-workflow.md](git-workflow.md)**.

Это итоговый, детальный промпт для настройки enterprise-инфраструктуры: облако, Kubernetes, безопасность и процессы вокруг Camunda. Используйте для Pulumi/Terraform (отдельные стеки) или как инструкцию архитекторам.

### 9.1. Context & Governance
**Project:** Millennium Credit Scoring (Camunda-based).
**Stack:** GCP, GKE, Pulumi (IaC), Camunda 8 (Zeebe + при необходимости self-managed Platform на Java), Google Identity (SSO) — по политике организации.
**Principle:** Least Privilege, GitOps-only changes, Zero Trust for Production.

### 9.2. Role & Access Matrix (IAM & RBAC)
Настрой инфраструктуру так, чтобы уровни доступа соответствовали следующим спецификациям:

### **A. Infrastructure & Management**
* **DevOps / SRE / Cloud-Eng:** Полный доступ к IaC (Pulumi), создание кластеров, управление VPC и мониторингом. В GKE — `cluster-admin`.
* **Release-Manager:** Единственная роль с правом апрува GitHub Environments для деплоя в `prod`. В облаке — `Viewer`.
* **Security / Compliance:** Доступ `Security Reviewer` в GCP. В GKE — `view` ко всем неймспейсам. Настройка **Gatekeeper/OPA** политик (запрет privileged containers).

### **B. Development & Quality Assurance**
* **Dev-Developer:** `Admin` в неймспейсе `dev`. Возможность деплоить, удалять поды, смотреть логи, делать `port-forward`.
* **Dev-Tester:** `View` доступ в `dev`. Доступ к Swagger UI и Camunda Cockpit (Read-only).
* **Ref-Tester (Staging):** `Edit` в неймспейсе `ref` (Staging). Право перезапускать сервисы для тестов регресса.

### **C. Production & Business**
* **Prod-Tester (UAT):** Право создавать процессы в Camunda через API/UI в `prod`, но без доступа к инфраструктуре K8s.
* **Prod-User (Credit Officer):** Доступ только к Camunda Tasklist (Task-Worker).
* **Break-glass:** Временный доступ `Owner` через **GCP PAM** (Privileged Access Manager) с обязательным указанием ID инцидента.

### **D. Data & AI Layers**
* **Data-Engineer:** `BigQuery Admin` и `Storage Admin`. Доступ к пайплайнам миграции данных из SQL в Data Lake.
* **ML-Engineer:** Доступ к **Vertex AI**, **Vector Search** и бакетам с эмбеддингами. Право деплоить модели как Sidecar-контейнеры.

### 9.3. Deployment Lifecycle (GitOps)
Реализуй Pipeline в GitHub Actions со следующей логикой (аутентификацию в GCP по возможности через **OIDC / Workload Identity Federation**, а не долгоживущие JSON-ключи — см. `infra/ARCHITECTURE.md`):

1.  **Branch `develop` → env `DEV`:**
    * Trigger: Push.
    * Action: `pulumi up --stack dev`.
2.  **Branch `release/*` → env `REF` / staging:**
    * Trigger: merge PR.
    * Action: `pulumi up --stack ref` (или `staging`), регрессионные тесты.
3.  **Branch `main` → env `PROD`:**
    * Trigger: manual approval (**Release-Manager**).
    * Policy: drift detection / запрет обхода Git для прод-изменений.



### 9.4. Technical Requirements (IaC Task)
Сгенерируй код Pulumi (в этом репозитории канон — **Python**; TypeScript допустим как отдельный стек), который создаёт:
1.  **Network:** VPC с 3 подсетями (dev, ref, prod) и Private Google Access.
2.  **GKE:** Региональный кластер с 3 пулами узлов:
    * `pool-dev`: Spot-инстансы (экономия).
    * `pool-prod`: Стандартные инстансы с включенным Shielded GKE.
3.  **Namespaces:** например `credit-dev`, `credit-ref`, `credit-prod` (в репо сейчас пример — `millennium-credit`; согласуйте имена).
4.  **RBAC Bindings:** Маппинг Google-групп (напр. `devs@company.com`) на роли внутри неймспейсов.
5.  **Secrets:** Интеграция с **GCP Secret Manager** через `ExternalSecrets` Operator.

### 9.5. Application Layer (Camunda Platform & Security)
Для **self-managed Camunda 8 Platform** (Operate / Tasklist / Zeebe и др.) типично Java/Spring; настройте по политике организации:

* **Auth:** Google OAuth2 / OIDC (SSO).
* **Database:** Cloud SQL (PostgreSQL) с **IAM Auth** или секретами из Secret Manager (без паролей в git).
* **Audit:** логи и история процессов — в **Cloud Logging** / **BigQuery** для аудита.

Прикладной scoring в **этом** репозитории — **не** Spring Boot, а **FastAPI** (`backend/`) и воркеры **Python** (`worker/`); связка с Camunda через Zeebe.

**Результат (цель blueprint):** архитектура с разделением обязанностей (SoD) и политиками, блокирующими несанкционированные изменения.

Ниже — отдельный **системный промпт** для ИИ или как финальная спецификация внедрения (11 ролей, ветки, GCP/GKE). Сверяйте с §9.1–9.4: канон IaC в этом репозитории — **Pulumi на Python** (`infra/pulumi/`).

---

# System Prompt: Millennium Credit Infrastructure & Governance

**Context:** Ты — Lead Cloud Architect & DevSecOps Engineer. Твоя задача — спроектировать и реализовать инфраструктуру для кредитного конвейера на базе Camunda (remote: `git@github.com:OlehKondratow/credit-scoring-camunda.git`).

## 1. Технический Стек
* **Cloud:** GCP (Google Cloud Platform).
* **IaC:** Pulumi (**Python** — как в `infra/pulumi/`; TypeScript только как отдельный стек, если команда согласует).
* **Orchestration:** GKE Standard; неймспейсы согласовать с кластером (например `credit-dev` / `credit-ref` / `credit-prod` или `millennium-credit` в манифестах — единообразно в Pulumi и `k8s/`).
* **CI/CD:** GitHub Actions + Workload Identity Federation.
* **Auth:** Google OAuth2 (SSO) для Camunda и RBAC для GKE.

## 2. Модель Ролей (Matrix 11)
Реализуй разграничение прав для следующих ролей через 4 группы доступа GitHub (`platform`, `engineers`, `quality`, `compliance`):
1.  **Platform (SRE/DevOps/Cloud):** Полный контроль IaC, GKE Cluster Admin.
2.  **Security/Compliance:** Аудит логов, управление политиками (OPA/Gatekeeper), без права "тихих" правок.
3.  **Engineers (Dev/ML/Data):** `Admin` в Namespace `dev`. Доступ к Vertex AI и BigQuery.
4.  **Quality (Testers/Release-Manager):** Управление Environment Gates, аппрув деплоя в `ref` и `prod`.
5.  **Business (Prod-Users):** Только прикладной доступ в Camunda UI (через SSO).
6.  **Incident (Break-glass):** Процедура временного повышения прав через GCP PAM.

## 3. Архитектура Ветвления & CI/CD
Настрой логику пайплайнов на основе текущей структуры веток:
* **`develop` (Env: DEV):** Автодеплой в `namespace: credit-dev`.
* **`release/*` (Env: REF):** Деплой в `namespace: credit-ref` после аппрува от `Ref-Tester`.
* **`main` (Env: PROD):** Деплой в `namespace: credit-prod` только после ручного аппрува `Release-Manager` и `SRE`.
* **Branch Protection:** Запрет прямого пуша в `main` и `develop`. Использование `CODEOWNERS` для обязательного ревью `/infra/` командой `platform`.

## 4. Задачи для реализации (Tasks)
1.  **Pulumi Code:** Создать GKE кластер, настроить `RoleBinding` для каждой из 11 ролей, привязав их к Google Groups.
2.  **Network:** Настроить `NetworkPolicies`, изолирующие трафик между `dev`, `ref` и `prod`.
3.  **Secrets:** Реализовать передачу секретов из GCP Secret Manager в K8s через External Secrets Operator.
4.  **Camunda:** Настроить конфигурацию Spring Boot для авторизации через Google Identity, разделяя права в Camunda Cockpit на основе email домена.

## 5. Формат вывода
* Предоставь структуру `.github/workflows/`.
* Предоставь файл `.github/CODEOWNERS`.
* Предоставь фрагмент Pulumi кода для создания RBAC и Environments.
* Напиши `scripts/emergency-access.sh` для реализации роли Break-glass.

---
