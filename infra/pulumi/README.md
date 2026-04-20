# Pulumi (Python) — основной IaC

Стек: **GCS** (бакет эмбеддингов + **raw PDF**), **BigQuery** dataset `millennium_analytics`, **Artifact Registry**, API **storage**, **bigquery**, **aiplatform**, **artifactregistry**. Экспорты: `vector_embeddings_bucket`, `raw_regulations_bucket`, `bigquery_dataset`, `artifact_registry_url`.

**Кто что делает:** стеки `dev` / `staging` / `prod` и роли — **`../ROLES.md`**.

## Требования

- `pulumi` CLI
- `gcloud auth application-default login` или `GOOGLE_APPLICATION_CREDENTIALS`

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
