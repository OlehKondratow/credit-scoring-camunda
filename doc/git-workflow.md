# Git: ветки, релизы и окружения

Согласовано с `doc/prompt.md` (§2), `infra/ROLES.md`, **[doc/github-setup.md](github-setup.md)** и **[doc/branch-notes.md](branch-notes.md)**. Remote по умолчанию: `git@github.com:OlehKondratow/credit-scoring-camunda.git`. Имена репозитория, тегов и папки клона: **[doc/naming.md](naming.md)**.

---

## 1. Ветки (корпоративная схема)

| Ветка / шаблон | Назначение |
|----------------|------------|
| **`main`** | **Production** — защищённая линия; в прод выкатывается только согласованный код (см. Environments в github-setup). |
| **`develop`** | **Интеграция** — основной поток разработки Millennium; сюда мержатся фичи. Рекомендуемая **default branch** на GitHub после настройки (см. branch-notes). |
| **`feature/<issue>-<slug>`** | Фичи и рефакторинг; от `develop`, merge в `develop` через PR. |
| **`release/<major.minor.patch>`** | Стабилизация перед релизом; от `develop`; после релиза — merge в `main` и обратно в `develop`, тег **`v*`** (по политике команды). |
| **`hotfix/<issue>-<slug>`** | Срочный патч от тега **`v*`** в проде; merge в `main` и `develop`. |

**Legacy:** ветка **`millennium-credit-v2`** — см. удаление в **[doc/branch-notes.md](branch-notes.md)**.

---

## 2. Теги и GitHub Releases

- Формат: **`vMAJOR.MINOR.PATCH`** (SemVer), например `v1.1.0`.
- Тег ставится на коммит, который **отдаётся в прод** (или в эталонный артефакт CI).
- **GitHub Release** с changelog — по шаблону команды; вложения — ссылки на образы в Artifact Registry и стек Pulumi, без секретов.

Существующий ориентир: **`v1.0.0`** / **`v1.1.0`** — снимки контура; переписывать теги на remote только осознанно.

---

## 3. Поток работы (кратко)

1. От **`develop`** создать **`feature/…`**, работать, **PR** → merge в **`develop`**.
2. Перед релизом: **`release/1.2.0`** от актуального **`develop`**, только фиксы; тесты / staging.
3. После приёмки: merge **`release/…` → `main`**, **тег `v1.2.0`**, **GitHub Release**, деплой с approval (**Release Manager**, см. `ROLES.md`).
4. Синхронизация: merge **`main` → `develop`** после релиза (или cherry-pick), если политика требует полного совпадения.

---

## 4. Соответствие окружениям (ориентир)

| Окружение | Типичная привязка Git |
|-----------|------------------------|
| **dev** | последний **`develop`** |
| **staging / ref** | **`release/*`** или коммит + образ `:rc` |
| **prod** | **`main`** + тег **`v*`** + approval |

CI: **`.github/workflows/ci.yml`** — push на **`develop`**, **`main`**, **`release/**`, **`feature/**`, **`hotfix/**`, теги `v*`; PR в **`develop`**, **`main`**, **`release/**` OIDC/WIF — см. `infra/ARCHITECTURE.md`.

---

## 5. Настройки на GitHub

Пошагово: **[doc/github-setup.md](github-setup.md)**. Кратко: **branch protection** на **`main`** и **`develop`**, **Environments**, **CODEOWNERS**.

---

## 6. Полезные команды

```bash
git fetch origin
git switch develop
git pull origin develop

git switch -c feature/123-short-desc
# … commits …
git push -u origin feature/123-short-desc
```

Создание релизной ветки:

```bash
./scripts/create-release-branch.sh 1.2.0
# или: make release-branch VERSION=1.2.0
```

Вручную:

```bash
git switch develop && git pull
git switch -c release/1.2.0
# фиксы, затем PR в main + develop по процессу
git tag -a v1.2.0 -m "Millennium release 1.2.0"
git push origin v1.2.0
```
