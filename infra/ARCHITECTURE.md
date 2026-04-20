# Infrastructure: изоляция для нескольких разработчиков

Цель: **разделить риски** между людьми и средами, не дублируя без нужды весь GCP, и сохранить **предсказуемый** Pulumi + GitOps.

**Роли (DevOps, dev, тест, prod-user):** см. **`ROLES.md`**. Основной IaC: **`pulumi/`**.

---

## 1. Уровни изоляции (от сильной к мягкой)

| Уровень | Что отделяется | Когда использовать |
|---------|------------------|----------------------|
| **A. Отдельный GCP project** на команду / «песочницу» | Квота, биллинг, IAM, полный blast radius | Enterprise, строгий compliance, отдельный billing |
| **B. Один project, разные Terraform state** (`dev` / `staging` / `prod`) | Разный `terraform.tfvars` + backend prefix; разные SA в CI | Рекомендуемый минимум для prod vs non-prod |
| **C. Один GKE, namespace на среду** (`dev`, `staging`, `prod`) | Рабочие нагрузки и секреты | Экономия; нужны NetworkPolicy / RBAC |
| **D. Namespace на разработчика** `dev-<github>` | Изоляция preview/feature в shared dev-кластере | Быстрые итерации без второго кластера |

Практичный pet-проект: **B + C** (иногда **D** для «своей» песочницы в dev).

---

## 2. Рекомендуемая модель для команды

### Облако (GCP)

- **Один project** `my-camunda8-project` (или `…-dev` и `…-prod` — если готовы платить за два проекта).
- **Разные service account для CI:**
  - `ci-terraform-dev@…` — только `roles/editor` или узкий набор на **non-prod** ресурсы.
  - `ci-terraform-prod@…` — минимальные роли, **только** из protected branch + approval.
- **State Terraform:**
  - backend GCS: префиксы `env/dev/terraform.tfstate`, `env/prod/terraform.tfstate` (или **отдельные buckets**).
- **Не один ключ на всё:** GitHub Actions / Cloud Build → **OIDC → Workload Identity Federation**, без JSON в репо.

### IaC (Terraform в `infra/terraform/`)

- Переменные **`environment`** (например `dev`, `staging`, `prod`) и опционально **`developer_id`** — попадают в **labels** ресурсов (учёт, фильтры в консоли).
- **`k8s_namespace`**: для общего dev — `millennium-credit-dev`; для персонального песочника — `millennium-credit-dev-<github>`.
- **Workload Identity** в `workload_identity.tf` должен совпадать с **реальным** namespace в манифестах (`k8s/millennium/`).

### Приложения (K8s)

- **Kustomize overlays:** `overlays/dev`, `overlays/prod` — только отличия (image tag, replicas, env).
- **Не применять prod из feature-ветки:** в CI — `plan` на PR, `apply` в prod только с `main` + review.

### GitOps (по желанию)

- **Argo CD / Flux** — только манифесты приложений; Terraform по-прежнему для **GKE / сеть / IAM / GCS / AR**.

---

## 3. Что НЕ дублировать на каждого разработчика

- Один **shared dev-кластер** + namespaces дешевле, чем GKE на человека.
- Один **Artifact Registry** с путём образа `…/credit-backend:dev-<sha>` — достаточно; отдельный registry на dev обычно избыточен.

---

## 4. Связь с переменными Terraform

См. `terraform/variables.tf`: `environment`, `developer_id`, `common_labels`.

Примеры значений: `terraform/envs/README.md`.

---

## 5. Краткий чеклист безопасности

1. Раздельный **state** для prod и non-prod.  
2. Разные **SA** / роли CI для dev и prod.  
3. **Branch protection** + обязательный `terraform plan` в PR.  
4. **Namespace + RBAC + ResourceQuota** в shared GKE.  
5. Секреты — **Secret Manager** / External Secrets, не в Git.
