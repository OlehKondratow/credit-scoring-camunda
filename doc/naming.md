# Имена: репозиторий, ветки, папка

**`Credit-Scoring-V2`** не используем как «официальное» имя продукта — это устаревший технический ярлык. Публичное имя контура: **Millennium Credit** (см. `doc/prompt.md`).

## Что считать каноном

| Сущность | Рекомендуемое имя |
|----------|-------------------|
| **Продукт / документация** | Millennium Bank AI Loan Officer / Millennium Credit |
| **Default branch на GitHub** | **`millennium-credit-v2`** (не переименовывать в `Credit-Scoring-V2`) |
| **Remote** | `git@github.com:OlehKondratow/credit-scoring-camunda.git` — имя **репозитория** на GitHub можно сменить в *Settings → General → Repository name* (например на `millennium-credit`); GitHub перенастроит URL, добавьте новый `remote url`. |
| **Релизные теги** | **`v1.0.0`**, `v1.1.0`, … (SemVer) |
| **Локальная папка клона** | Любое удобное, напр. `~/src/millennium-credit` — на код не влияет. |

## Что убрать / не создавать повторно

- **Git-тег `Credit-Scoring-V2`** — не семантический и путает с версией; лучше удалить (локально и на `origin`), если создавали по ошибке:

  ```bash
  git tag -d Credit-Scoring-V2
  git push origin :refs/tags/Credit-Scoring-V2
  ```

- Не делать **default branch** с именем `Credit-Scoring-V2` — держать **`millennium-credit-v2`**.

## GitHub: смена имени репозитория

1. *Repository → Settings → General → Repository name* — задать новое (например `millennium-credit`).
2. Обновить `git remote`:

   ```bash
   git remote set-url origin git@github.com:OlehKondratow/НОВОЕ_ИМЯ.git
   ```

3. Проверить **CI badges**, **Argo CD** `repoURL`, ссылки в доках — заменить старый URL.
