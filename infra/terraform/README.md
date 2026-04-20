# Terraform (GCP)

Рабочий каталог: все `*.tf` и `terraform.tfvars` здесь.

**Изоляция для нескольких разработчиков:** см. **`../ARCHITECTURE.md`**, примеры **`envs/`**.

## Быстрый запуск

```bash
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars
# project_id, при необходимости create_gke_cluster = false

terraform init
terraform plan
terraform apply
```

## Существующий кластер `camunda-stable`

Не удаляется этим стеком. Чтобы **не создавать второй GKE**, задайте `create_gke_cluster = false` в `terraform.tfvars`.

## Удаление ресурсов стека

```bash
cd infra/terraform
terraform destroy
```
