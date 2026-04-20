# Примеры `terraform.tfvars` по средам

Копируйте в **`terraform.tfvars`** (не коммитьте секреты) или используйте `-var-file=envs/dev.tfvars`.

## Общий dev (shared cluster / shared namespace)

Файл: **`dev-shared.tfvars.example`** — см. ниже.

## Prod (отдельный state backend обязателен)

Файл: **`prod.tfvars.example`** — отдельный GCS prefix для state, отдельный CI SA.

## Per-developer sandbox (только labels + свой `k8s_namespace`)

Задайте `developer_id = "alice"` и в Kubernetes создайте namespace `millennium-credit-dev-alice`; в `workload_identity.tf` биндинг должен совпадать с `k8s_namespace` + `backend_ksa_name`.

---

### dev-shared.tfvars.example

```hcl
project_id   = "my-camunda8-project"
region       = "europe-central2"
environment  = "dev"
cluster_name = "millennium-credit-dev-gke"

# Один namespace на команду
k8s_namespace = "millennium-credit-dev"

create_gke_cluster = true
# developer_id = ""
```

### prod.tfvars.example

```hcl
project_id   = "my-camunda8-project-prod"
region       = "europe-central2"
environment  = "prod"
cluster_name = "millennium-credit-prod-gke"

k8s_namespace = "millennium-credit"

create_gke_cluster     = true
deletion_protection    = true
```
