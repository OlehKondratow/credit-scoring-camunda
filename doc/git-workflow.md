# Git: ветки, релизы и окружения

Согласовано с `doc/prompt.md` (§2), `infra/ROLES.md` и §9 blueprint в `prompt.md`. Remote по умолчанию: `git@github.com:OlehKondratow/credit-scoring-camunda.git`. Имена репозитория, тегов и папки клона: **[doc/naming.md](naming.md)**.

---

## 1. Ветки (текущая договорённость)

| Ветка / шаблон | Назначение |
|----------------|------------|
| **`millennium-credit-v2`** | Основная линия **Millennium** (RAG, Pulumi, worker, UI). **Default branch** на GitHub для нового кода. |
| **`main`** | Историческая линия (классический Camunda demo). **Не** смешивать с Millennium без осознанного merge. Не force-push без необходимости. |
| **`feature/<issue>-<slug>`** | Фичи и рефакторинг. Живут недолго; merge в `millennium-credit-v2` через PR. |
| **`release/<major.minor.patch>`** | Стабилизация перед релизом: только исправления регресса/доков; ответвляется от `millennium-credit-v2`. После релиза — merge обратно в `millennium-credit-v2` (и при политике команды — в долгоживущую prod-ветку, см. ниже). |
| **`hotfix/<issue>-<slug>`** | Срочный патч от тега **`v*`** в проде; после — merge в `millennium-credit-v2` и повторный тег. |

Опционально (если команда хочет явный GitFlow):

| **`develop`** | Интеграция фич перед `millennium-credit-v2`; имеет смысл только при нескольких командах и чётком процессе. |

---

## 2. Теги и GitHub Releases

- Формат: **`vMAJOR.MINOR.PATCH`** (SemVer), например `v1.1.0`.
- Тег ставится на коммит, который **отдаётся в прод** (или в эталонный артефакт CI).
- **GitHub Release** с changelog — по шаблону команды; приложение к релизу — не бинарники с секретами, а ссылки на образы в Artifact Registry и номер Pulumi-стека при необходимости.

Существующий ориентир: тег **`v1.0.0`** — снимок контура Millennium; обновлять на remote осторожно.

---

## 3. Поток работы (кратко)

1. От **`millennium-credit-v2`** создать **`feature/…`**, работать, открыть **PR** → после review merge в `millennium-credit-v2`.
2. Перед релизом: создать **`release/1.2.0`** от актуального `millennium-credit-v2`, заморозить фичи, только фиксы; прогнать тесты / staging.
3. После приёмки: **тег `v1.2.0`** на merge-коммит (или на коммит в `release/…` по политике), **GitHub Release**, деплой по CI с approval (**Release Manager**, см. `ROLES.md`).
4. **`main`** трогать только для линии legacy или отдельного процесса слияния — не как основную для Millennium.

---

## 4. Соответствие окружениям (ориентир)

| Окружение | Типичная привязка Git |
|-----------|------------------------|
| **dev** | последний `millennium-credit-v2` (или nightly) |
| **staging / ref** | `release/*` или выбранный коммит + образ `:rc` |
| **prod** | тег **`v*`** + approval; без деплоя «с любого» коммита |

CI: **`.github/workflows/ci.yml`** — push на `millennium-credit-v2`, `main`, `release/**`, `feature/**`, `hotfix/**`, теги `v*`; PR в `millennium-credit-v2`, `main`, `release/**`. OIDC/WIF для деплоя — см. `infra/ARCHITECTURE.md`.

---

## 5. Настройки на GitHub (рекомендации)

Пошагово (UI): **[doc/github-setup.md](github-setup.md)**.

- **Branch protection** на `millennium-credit-v2`: required PR, required status checks, запрет прямого push при возможности.
- **Environments** `dev` / `staging` / `production` с required reviewers на `production`.
- Запрет секретов в истории: pre-commit или `git-secrets` / сканирование в CI.

---

## 6. Полезные команды

```bash
git fetch origin
git switch millennium-credit-v2
git pull origin millennium-credit-v2

git switch -c feature/123-short-desc
# … commits …
git push -u origin feature/123-short-desc
```

Создание релизной ветки (скрипт из репозитория):

```bash
./scripts/create-release-branch.sh 1.2.0
# или: make release-branch VERSION=1.2.0
```

Или вручную:

```bash
git switch millennium-credit-v2 && git pull
git switch -c release/1.2.0
# только фиксы, затем merge в millennium-credit-v2
git tag -a v1.2.0 -m "Millennium release 1.2.0"
git push origin v1.2.0
```
