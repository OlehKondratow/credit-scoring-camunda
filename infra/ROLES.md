# Роли: DevOps / разработка / тест / прод

Инфраструктура как код: **Pulumi** (`infra/pulumi/`). Остальное в `infra/` — справочные/legacy примеры.

Ниже — **рекомендуемая матрица** (GCP IAM + Pulumi + K8s + Git). Подстройте названия групп в **Google Workspace / Cloud Identity** и в **GitHub/GitLab Teams**.

---

## Полный список ролей

1. **devops / sre / cloud-eng** — платформа, инциденты, IaC  
2. **dev-developer** — разработка фич  
3. **dev-tester** — тесты в dev  
4. **ref-tester** — регресс на staging / ref  
5. **prod-tester** — UAT на проде (ограниченно)  
6. **prod-user** — бизнес-пользователь (кредитный офицер и т.п.)  
7. **security / compliance** — аудит, политики, соответствие; без смены инфраструктуры «втихую»  
8. **break-glass (инцидент)** — временный повышенный доступ по runbook при инциденте  
9. **release-manager** — человеческий gate релиза в prod (совместно с CI)  
10. **data-engineer** — данные, GCS, BigQuery, пайплайн ingest  
11. **ML Engineer** — эмбеддинги, Vector Search, качество RAG, eval  

---

## Роли и доступ

| Роль | Назначение | GCP (типичные роли) | Pulumi | Kubernetes | Git / CI |
|------|------------|---------------------|--------|------------|----------|
| **devops / sre / cloud-eng** | Платформа, сеть, кластер, пайплайны, state, инциденты | `roles/owner` или набор: `compute.admin`, `container.admin`, `iam.serviceAccountAdmin`, `resourcemanager.projectIamAdmin` (по принципу least privilege) | Все стеки: `preview`/`up` для **dev**, **staging**, **prod**; state backend; секреты CI | `cluster-admin` или отдельная RBAC-роль платформы | Админ репо; merge в `main`; настройка OIDC |
| **dev-developer** | Фичи, локально и в dev | `roles/editor` на **dev-проект** *или* нет прямого GCP — только через CI | Стек **`dev`**: `preview` всегда; **`up`** — по политике (свой sandbox-проект или запрет) | Namespace **`dev`** / **`dev-<login>`**; без `cluster-admin` | Feature-ветки; PR; **не** merge в `main` без review |
| **dev-tester** | Функциональное тестирование в dev | Часто **без** GCP Console; или `roles/viewer` на dev-проект | **Нет** (или только `preview` read-only через CI артефакт) | Деплой **тестовых** образов в `dev` через CI, read logs | Ветки тестов; возможно read-only к репо |
| **ref-tester** | Регресс на **референсной / staging** среде (как прод, не прод) | `viewer` на **staging/ref** проект | Стек **`staging`**: только **`preview`**; **`up`** — по отдельному approval от DevOps | Namespace **`staging`** / **`ref`**; нет доступа к `prod` | Ветка `release/*` или теги; deploy в staging из CI |
| **prod-tester** | UAT / приёмка на **проде** (ограниченно) | Минимум: `viewer` + доступ к **тестовым** данным/флагам приложения | **Нет** Pulumi на prod | **Нет** `kubectl` к prod без break-glass; работа через **UI** (Streamlit / Tasklist) и тестовые учётки | Read-only или только тикеты; **не** infra |
| **prod-user** | Кредитный офицер / бизнес | Только **приложение** (Camunda Tasklist, Streamlit) | Нет | Нет | Нет |
| **security / compliance** | Контроль IAM, Audit Logs, организационные политики, evidence для аудита (SOC2/RODO и т.д.); **не** меняют прод без процесса | Без Owner: `roles/logging.viewer`, `roles/cloudasset.viewer`, `roles/iam.securityReviewer` / `roles/orgpolicy.policyViewer` (по модели); **нет** `container.admin` если не согласовано | **Нет** `pulumi up` в prod; read-only артефакты / политики | **Нет** prod `kubectl` без break-glass | Review security PR (политики, секреты); без merge в `main` без второй пары глаз при необходимости |
| **break-glass (инцидент)** | Временный доступ выше обычного при **SEV**-инциденте: восстановление, отладка прод, по **runbook** и тикету | Только **ограниченное окно** и **учётка под инцидент**: временный `roles/owner` / break-glass SA или elevation через **Privileged Access Manager** / аналог; всё в **Cloud Audit Log** | **Нет** «на каждый день»; в инциденте — по политике (например только DevOps on-call + approval security) | `kubectl` / `cluster-admin` на **prod** **временно**, с записью команд / postmortem | Не заменяет CI: после инцидента — отзыв прав, разбор (RCA) |
| **release-manager** | Утверждает **production release**: чеклист (тесты, безопасность, изменения), согласование окна | Обычно **без** прямого GCP или `roles/viewer` на prod для чтения версий/артефактов | **Нет** `pulumi up`; может видеть `preview` из CI | **Нет** | **Approve** environment / release job в CI; теги `v*`; не обязан писать Pulumi |
| **data-engineer** | Сырые PDF → GCS, пайплайн `data/ingest.py`, JSONL в бакет эмбеддингов, метаданные, загрузки в **BigQuery** (`millennium_analytics`) без сырого PII | `roles/storage.objectAdmin` на data-бакеты (или префиксы), `roles/bigquery.dataEditor` + `roles/bigquery.jobUser`; **без** `container.admin` и без секретов приложения | Согласует имена ресурсов с Pulumi; **не** GKE | **Нет** | PR на пайплайны данных; без deploy инфраструктуры кластера |

---

## ML Engineer (детализация Vertex, RAG)

Роль **data-engineer** — см. таблицу **«Роли и доступ»** выше (данные, GCS, BigQuery, ingest).

| Роль | Задачи | GCP (типично) | Pulumi / данные | Kubernetes |
|------|--------|---------------|-----------------|------------|
| **ML Engineer** | Эмбеддинги (`text-embedding-004`), индекс Vector Search, деплой на endpoint, offline eval (`data/eval_rag.py`), качество RAG, стоимость запросов | `roles/aiplatform.user`, `roles/storage.objectViewer` на бакеты эмбеддингов; при настройке индекса — `roles/aiplatform.admin` в **dev** только | Читает стек; **не** `up` в prod без CI; может `preview` для dev | Обычно **нет**; образы через CI |

**Принцип:** ML/Data не получают `container.admin` и Owner, если не ведут платформу. Доступ к **PII** — только через приложение и политики маскирования; в BigQuery — хеши/агрегаты, не открытый PESEL.

---

## Pulumi: как разнести стеки (рекомендация)

| Stack | Среда | Кто делает `pulumi up` |
|-------|--------|-------------------------|
| `dev` | Песочница / общий dev GCP | DevOps + (опционально) разработчики в свой проект |
| `staging` / `ref` | Референс перед продом | Только DevOps / CI |
| `prod` | Прод | Только CI после merge + approval; вручную — break-glass DevOps |

**State:** отдельный backend на stack (например префикс в GCS `pulumi-state/dev|staging|prod`) или отдельные проекты GCP.

---

## Что ещё нужно (чеклист)

1. **Именованные учётки в GCP** (группы ↔ роли IAM), не «все editor».  
2. **Секреты** — Secret Manager; CI читает через OIDC, люди — через IAM + аудит.  
3. **Соглашение по именам**: `ref-tester` = тесты на **staging**; **prod-tester** = только согласованные сценарии UAT в prod **без** прав на инфраструктуру.  
4. **Документ break-glass**: кто входит в пул **break-glass (инцидент)**, как оформляется тикет, длительность окна, отзыв прав и обязательный postmortem (см. строку в таблице выше).

Итог: для зрелого процесса используйте полный список ролей (включая **security / compliance**, **break-glass**, **release-manager**, **data-engineer**, **ML Engineer**).
