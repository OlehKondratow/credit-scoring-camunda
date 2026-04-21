# CODEOWNERS: 11 ролей и 6 учётных записей GitHub

Документ связывает **логические роли** из [`infra/ROLES.md`](../infra/ROLES.md) (полный список из 11 пунктов) с **шестью пользователями GitHub**, которые участвуют в ревью через [`.github/CODEOWNERS`](../.github/CODEOWNERS).

Форк для примера: [kwazar-0/credit-scoring-camunda](https://github.com/kwazar-0/credit-scoring-camunda). Логины ниже должны совпадать с реальными `@username` на GitHub; при смене ника обновите и этот файл, и `CODEOWNERS`.

## Шесть учётных записей GitHub

| # | GitHub | Типичный фокус в матрице ролей |
|---|--------|--------------------------------|
| U1 | `@kwazar-0` | Платформа, владелец форка, инциденты IaC |
| U2 | `@OlehKondratow` | Разработка приложения, ML/RAG, релизный код |
| U3 | `@tempb59-commits` | QA (dev/ref), процессы в BPMN/DMN с точки зрения тестирования |
| U4 | `@geraltwilkbialy-cloud` | Security / compliance (политики, чувствительные документы) |
| U5 | `@olehkondracki-prog` | Data / пайплайны, поддержка разработки |
| U6 | `@tempb418-ux` | Co-platform: CI/CD, второй голос по `infra`/`k8s` |

## Одиннадцать ролей → кто из шести участвует в ревью кода

| # | Роль (как в ROLES.md) | Первичные владельцы ревью (GitHub) | Примечание |
|---|------------------------|-------------------------------------|------------|
| 1 | devops / sre / cloud-eng | U1, U6 | `infra/`, `k8s/`, корневой `Makefile`, `docker-compose` |
| 2 | dev-developer | U2, U5 | `backend/`, `worker/`, `ui/` |
| 3 | dev-tester | U3 | Совместно на `bpmn/`, `dmn/`; CI — U3, U1, U6 |
| 4 | ref-tester | U3 | Те же зоны процессов; релизные ветки по [git-workflow.md](git-workflow.md) |
| 5 | prod-tester | — | Нет путей в git: UAT через приложение |
| 6 | prod-user | — | Нет доступа к репозиторию |
| 7 | security / compliance | U4, U1 | `SECURITY.md`, корневые политики `*.md` (совместно) |
| 8 | break-glass (инцидент) | U1 | Не рутинный CODEOWNER; runbook вне этого файла |
| 9 | release-manager | U2, U1 | Теги `v*`, согласование через CI/Environment |
| 10 | data-engineer | U5, U2 | `data/` (ingest, выгрузки) |
| 11 | ML Engineer | U2, U5 | Модели/RAG рядом с backend и `data/` |

**Итог:** в Git не создаётся 11 команд — шесть людей покрывают ревью по зонам репозитория; роли 5–6 и 8 не требуют отдельных строк в `CODEOWNERS`.

## Связь с GitHub Teams (организация)

При переносе в **GitHub Organization** замените строки в `CODEOWNERS` на `@org/team-name` по [github-setup.md](github-setup.md); матрица «роль → team» остаётся в `ROLES.md`.
