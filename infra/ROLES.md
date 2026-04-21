# Роли: DevOps / разработка / тест / прод

Инфраструктура как код: **Pulumi** (`infra/pulumi/`). Остальное в `infra/` — справочные/legacy примеры.

Ниже — **рекомендуемая матрица** (GCP IAM + Pulumi + K8s + Git). Подстройте названия групп в **Google Workspace / Cloud Identity** и в **GitHub/GitLab Teams**. Практическое создание объектов доступа — раздел **«Пошаговая инструкция по созданию доступов»**.

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

## Пошаговая инструкция по созданию доступов

Цель: из **11 логических ролей** получить **конкретные объекты** в IdP, GCP, GKE, Git и приложении. **Не нужно** создавать **11 команд GitHub** — обычно **4 группы** на git + **группы Google** + **IAM** (см. **[doc/github-setup.md](../doc/github-setup.md)**).

### Этап 0. Пререквизиты

1. Зафиксировать **модель окружений**: отдельные GCP-проекты и/или папки (см. **[ARCHITECTURE.md](ARCHITECTURE.md)**): хотя бы **dev**, **staging/ref**, **prod**.
2. Иметь роль **Organization Admin** (или эквивалент) в **Google Cloud** и **GitHub Organization** для создания групп и политик.
3. Согласовать **префикс имён** групп (например `millennium-…`) и список людей по ролям (таблица выше).

### Этап 1. Группы в Google Workspace / Cloud Identity

Создайте **группы** (или используйте существующие), которые будут principal’ами для IAM и (опционально) для синхронизации с GitHub.

| Группа (пример имени) | Покрываемые роли из списка из 11 |
|------------------------|----------------------------------|
| `…-platform` | devops / sre / cloud-eng |
| `…-developers` | dev-developer |
| `…-qa-dev` | dev-tester |
| `…-qa-ref` | ref-tester |
| `…-release-approvers` | release-manager |
| `…-security` | security / compliance |
| `…-data` | data-engineer |
| `…-ml` | ML Engineer |
| `…-breakglass` | break-glass (пустая; членство только на время инцидента) |

**prod-tester** и **prod-user** часто **не** маппятся на GCP-группы с широкими правами: доступ через **приложение** (Camunda, Streamlit) и отдельные учётные записи продукта.

Добавьте людей в группы согласно оргструктуре.

### Этап 2. Проекты GCP и привязка IAM к группам

В каждом **проекте** (или на уровне папки org):

1. Откройте **IAM & Admin → IAM**.
2. **Grant access**: principal = **Google Group** (`group@…`), роль = из колонки «GCP» в таблице **«Роли и доступ»** (например на dev-проект для `…-developers`: `roles/editor` или суженный custom role).
3. Повторите для **staging** и **prod** с **least privilege**: на prod у разработческих групп — **нет** Editor/Owner без исключения по политике.

**Сервисные аккаунты (SA)** для приложений и CI создайте отдельно; людям **не** выдавайте ключи SA в обход Secret Manager/OIDC.

### Этап 3. Kubernetes (GKE): namespaces и RBAC

1. Создайте **namespaces** под среды (например `credit-dev`, `credit-ref`, `credit-prod` — согласуйте с манифестами в `k8s/`).
2. Создайте **Role** / **ClusterRole** с минимальными правами (просмотр подов, логов, `exec` только где нужно).
3. **RoleBinding**: субъект = группа Google (если включён **GKE Identity** / привязка групп) **или** отдельные пользователи — по модели кластера.
4. **Не** давайте `cluster-admin` группам разработки; платформенная группа — по политике (отдельная RBAC-роль платформы).

### Этап 4. GitHub: Teams и доступ к репозиторию

1. В **GitHub Organization** создайте **Teams** по **[doc/github-setup.md](../doc/github-setup.md)** (обычно: `platform-admin`, `engineers`, `quality-gate`, `compliance`).
2. Назначьте членов: вручную или через **SCIM** из IdP (если настроено).
3. На репозитории `credit-scoring-camunda`: **Team → роль** (Read / Write / Maintain / Admin) по матрице в github-setup.
4. Включите **branch protection** на `main` и `develop`, заполните **CODEOWNERS** (пути `/infra/` → platform). Матрица **11 ролей** и **6 учёток** GitHub для ревью: **[doc/github-codeowners-matrix.md](../doc/github-codeowners-matrix.md)**.
5. Создайте **Environments** `development`, `reference` (или `staging`), `production` с **Required reviewers** на production.

### Этап 5. CI/CD: OIDC / Workload Identity Federation

1. В GCP создайте **Workload Identity Pool** и **Provider** для **GitHub** (issuer `https://token.actions.githubusercontent.com`).
2. Свяжите **provider** с **сервисным аккаунтом**, у которого минимальные роли на деплой (Artifact Registry, GKE, отдельно по средам).
3. В репозитории **не** храните JSON-ключи SA для prod; секреты — в **Environment secrets** или только OIDC + IAM.

Подробности — **[ARCHITECTURE.md](ARCHITECTURE.md)** (OIDC).

### Этап 6. Секреты приложения и инфраструктуры

1. Секреты приложения (Camunda, Vertex, БД) — в **Secret Manager**; доступ по **IAM** только нужным SA и ролям.
2. В кластере — **External Secrets Operator** или аналог, без копирования секретов в git.

### Этап 7. Camunda и продуктовые UI

1. Настройте **OIDC / SSO** для Operate / Tasklist (по политике банка).
2. Создайте **группы/роли в Camunda** для **prod-user** и **prod-tester**; маппинг с корпоративными группами.
3. **Streamlit** / аналитика — отдельная авторизация, без лишнего GCP для бизнес-пользователей.

### Этап 8. Break-glass

1. Оформите **runbook**: тикет инцидента, максимальная длительность окна, кто из **…-breakglass** / on-call может запросить elevation через **GCP PAM** (или аналог).
2. После инцидента — **отзыв** временных прав, **RCA**.

### Этап 9. Проверка матрицы

Пройдите по строкам таблицы **«Роли и доступ»** и для каждой роли отметьте:

- [ ] Группа в Google создана и заполнена (если применимо).
- [ ] IAM на нужных проектах выдан.
- [ ] RBAC в GKE согласован (если применимо).
- [ ] GitHub Team и права на репо согласованы.
- [ ] CI: нет избыточных секретов; prod деплой только с approval.

---

## Pulumi: как разнести стеки (рекомендация)

| Stack | Среда | Кто делает `pulumi up` |
|-------|--------|-------------------------|
| `dev` | Песочница / общий dev GCP | DevOps + (опционально) разработчики в свой проект |
| `staging` / `ref` | Референс перед продом | Только DevOps / CI |
| `prod` | Прод | Только CI после merge + approval; вручную — break-glass DevOps |

**State:** отдельный backend на stack (например префикс в GCS `pulumi-state/dev|staging|prod`) или отдельные проекты GCP.

---

## Что ещё нужно (краткий чеклист)

Детали — в **пошаговой инструкции** выше.

1. **Именованные группы в GCP** (группы ↔ роли IAM), не «все editor».  
2. **Секреты** — Secret Manager; CI через OIDC; люди — IAM + аудит.  
3. **Имена сред**: `ref-tester` = staging/ref; **prod-tester** = UAT в prod **без** прав на инфраструктуру.  
4. **Break-glass runbook**: пул участников, тикет, окно доступа, отзыв, postmortem.

Итог: зрелый процесс покрывает все **11 ролей** из списка; технические объекты создаются по этапам 0–9, а не «одной кнопкой».
