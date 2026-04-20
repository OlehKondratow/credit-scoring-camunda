# GitHub: branch protection и environments

Дополняет **[doc/git-workflow.md](git-workflow.md)** — то, что настраивается **в UI GitHub** (в репозитории нельзя зафиксировать protection в виде одного YAML).

## 1. Default branch

**Settings → General → Default branch:** **`millennium-credit-v2`**.

## 2. Branch protection (рекомендуется)

**Settings → Rules → Rulesets** (или классические *Branch protection rules*) для ветки **`millennium-credit-v2`**:

- Требовать PR перед merge (no direct push), минимум **1 approval**.
- Включить **required status checks**: job’ы **`backend`** и **`worker`** из workflow **CI** (после первого успешного прогона они появятся в списке).
- Опционально: **Require conversation resolution**, **Require linear history**.

Для **`main`** (legacy): по желанию те же правила или только запрет force-push.

Для **`release/**`**: можно отдельное правило с теми же checks и запретом удаления ветки до merge.

## 3. Environments

**Settings → Environments:** создать **`dev`**, **`staging`**, **`production`**.

- У **`production`** включить **Required reviewers** (роль Release Manager по `infra/ROLES.md`).
- Секреты деплоя (GCP, kubeconfig) хранить на уровне environment, не в общих repo secrets без необходимости.

## 4. Секреты и OIDC

Предпочтительно **OIDC / Workload Identity Federation** для GitHub Actions вместо долгоживущих JSON-ключей — см. **`infra/ARCHITECTURE.md`**.

## 5. Теги

Удаление и создание тегов `v*` — только через дисциплину команды; опционально ограничить право создавать релизные теги ролью **maintain** / отдельной группой.
