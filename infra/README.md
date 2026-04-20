# Infrastructure (`infra/`)

## Единый подход: **Pulumi**

Основной IaC для этого репозитория — **`pulumi/`** (Python). Здесь же описаны **роли** и изоляция: **`ROLES.md`**, **`ARCHITECTURE.md`**.

Каталог **`terraform/`** оставлен как **справочный** пример (HCL); новые изменения платформы ориентируйте на Pulumi, чтобы не плодить два источника правды.

| Документ | Содержимое |
|----------|------------|
| **`ROLES.md`** | DevOps/SRE, dev-developer, dev-tester, ref-tester, prod-tester, prod-user + опциональные роли |
| **`ARCHITECTURE.md`** | Уровни изоляции (project / state / namespace), GitOps |

## Быстрый старт (Pulumi)

```bash
cd infra/pulumi
python3 -m venv venv && . venv/bin/activate
pip install -r requirements.txt
pulumi stack init dev
pulumi config set gcp:project YOUR_PROJECT_ID
pulumi up
```

Подробнее: **`pulumi/README.md`**.

## Прочие каталоги (опционально)

| Каталог | Назначение |
|---------|------------|
| **`terraform/`** | Legacy / reference Terraform |
| **`cdktf/`** | CDK for Terraform (пример) |
| **`config-connector/`**, **`crossplane/`** | Примеры CR в K8s |

Регион по умолчанию: **`europe-central2`**.
