# Pulumi (Python) — основной IaC

Стек: **GCS** (бакет эмбеддингов + **raw PDF**), **BigQuery** dataset `millennium_analytics`, **Artifact Registry**, API **storage**, **bigquery**, **aiplatform**, **artifactregistry**. Экспорты: `gcp_project`, `gcp_region`, `cluster_name`, `artifact_repository_id`, `vector_embeddings_bucket`, `raw_regulations_bucket`, `bigquery_dataset`, `artifact_registry_url`.

**Кто что делает:** стеки `dev` / `staging` / `prod` и роли — **`../ROLES.md`**.

## Требования

- **`pulumi` CLI** (отдельно от `pip`): пакеты в `requirements.txt` — это только Python SDK для программы. CLI: [установка](https://www.pulumi.com/docs/install/) или `curl -fsSL https://get.pulumi.com | sh`. После установки добавьте в `PATH`: `export PATH="$HOME/.pulumi/bin:$PATH"` (иначе будет `pulumi: command not found`).
- Учётные данные GCP: обычно `gcloud auth application-default login`. Если видите **`invalid_grant` / Bad Request** на ADC, но `gcloud auth print-access-token` работает, выполните повторно `gcloud auth application-default login` **или** для одного запуска: `PULUMI_USE_GCLOUD_USER_TOKEN=1 pulumi preview` / **`../../scripts/pulumi-with-gcloud-token.sh preview`** (обёртка в репозитории). В **`__main__.py`** провайдер тогда берёт свежий пользовательский токен через `gcloud` (только для локальной отладки, не для CI).
- Альтернатива: `GOOGLE_APPLICATION_CREDENTIALS` на JSON ключ SA (не коммитить).
- **State:** для командного стека — `pulumi login` (SaaS или self-hosted). Локально без аккаунта Pulumi Cloud: `pulumi login --local`. Если стек с шифрованием секретов, задайте `PULUMI_CONFIG_PASSPHRASE` (или `PULUMI_CONFIG_PASSPHRASE_FILE`) перед `stack init` / `preview` / `up`.

## Запуск

```bash
cd infra/pulumi
python3 -m venv venv && . venv/bin/activate
pip install -r requirements.txt
pulumi stack init dev
pulumi config set gcp:project YOUR_PROJECT_ID
pulumi config set credit-scoring:region europe-central2
pulumi preview
pulumi up
```

`pulumi config set credit-scoring:clusterName millennium-credit-gke` — имя репозитория Artifact Registry (см. `__main__.py`).

Для **prod** используйте отдельный stack и backend state; `up` — из CI после approval (см. `ROLES.md`).

Не смешивайте с **Terraform** на те же имена ресурсов в одном GCP-проекте без осознанного импорта.

## Опционально: GitHub Actions → GCP (OIDC / Workload Identity)

Модуль `workload_identity_github.py` создаёт **Workload Identity Pool**, OIDC-провайдер для `https://token.actions.githubusercontent.com`, сервисный аккаунт и привязку `roles/iam.workloadIdentityUser` для репозитория **без** выдачи JSON-ключей в GitHub.

**Включение** (один раз, от админа проекта):

```bash
pulumi config set credit-scoring:enableGithubWif true
pulumi config set credit-scoring:githubOwner YOUR_GITHUB_ORG_OR_USER
pulumi config set credit-scoring:githubRepo credit-scoring-camunda
pulumi up
```

После `up` возьмите из вывода **`github_workload_identity_provider`** и **`github_actions_service_account_email`**, добавьте в GitHub → Settings → Secrets:

- `GCP_WORKLOAD_IDENTITY_PROVIDER` — полное имя провайдера (`projects/…/locations/…/providers/…`).
- `GCP_GITHUB_ACTIONS_SA_EMAIL` — email SA.

**Важно:** модуль **не** назначает SA роли вроде `Editor` на проект — добавьте минимально необходимые роли для `pulumi preview`/`up` (часто отдельная кастомная роль или согласованный набор на dev-проект). См. `../ROLES.md`.

Workflow: **`.github/workflows/pulumi-preview.yml`** (ветка `develop`, путь `infra/pulumi/**`).

## Отладка IaC

| Шаг | Команда / действие |
|-----|---------------------|
| Зависимости Python | `cd infra/pulumi && python3 -m venv venv && . venv/bin/activate && pip install -r requirements.txt` (как в `Pulumi.yaml`: `virtualenv: venv`) |
| CLI Pulumi | [Установка](https://www.pulumi.com/docs/install/) — затем `pulumi version` |
| Логин в state (если не local) | `pulumi login` — для команды часто backend в GCS/S3 |
| Конфиг проекта GCP | `pulumi config set gcp:project YOUR_PROJECT_ID` и при необходимости `pulumi config set credit-scoring:region europe-central2` |
| План без применения | `pulumi preview` — смотреть **+/-** ресурсов и ошибки IAM/API |
| Учётные данные GCP | `gcloud auth application-default login` или `GOOGLE_APPLICATION_CREDENTIALS` на JSON key с правами на проект |
| Типичные ошибки | **403 API not enabled** — стек включает `storage`, `bigquery`, `aiplatform`, `artifactregistry` через `google_project_service`; подождите минуту после первого `up`. **403 IAM** — у субъекта нет прав на проект. **Dataset location** — регион dataset совпадает с политикой организации. |

Проверка программы без GCP: в venv выполните `python -c "import pulumi_gcp, pulumi_random"` — импорты должны проходить.
