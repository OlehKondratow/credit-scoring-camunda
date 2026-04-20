# GitHub Setup & Governance: Millennium Credit Enterprise

Этот документ описывает техническую реализацию 11 ролей и процессов управления доступом в репозитории **Millennium Credit** (ветки и legacy: **[doc/branch-notes.md](branch-notes.md)**).

**Замена плейсхолдеров:** везде `@org/...` замените на реальное имя **GitHub Organization** (например `@MillenniumBank/platform-admin`).

**Ветки:** **`main`** — production, **`develop`** — интеграция. Рекомендуемая **default branch** на GitHub: **`develop`**. Поток Git: **[doc/git-workflow.md](git-workflow.md)**.

## 1. Структура Команд (Teams)
Вместо настройки прав для каждого пользователя, мы используем группы. Один сотрудник может состоять в нескольких командах.

| GitHub Team | Роли (из ROLES.md) | Доступ к Repo |
| :--- | :--- | :--- |
| **`@org/platform-admin`** | DevOps, SRE, Cloud-Eng, Security | **Admin** |
| **`@org/engineers`** | Dev-Developer, ML Engineer, Data-Engineer | **Write** |
| **`@org/quality-gate`** | Dev-Tester, Ref-Tester, Prod-Tester, Release-Manager | **Read** (Write в `/tests`) |
| **`@org/compliance`** | Security / Compliance (Auditors) | **Read** |

---

## 2. Защита веток (Branch Protection & Rulesets)

### Ветка: `main` (Production)
* **Require a pull request before merging:** Включено.
* **Required approvals:** Минимум 2 (один от `@org/platform-admin`, один от `@org/quality-gate`).
* **Code Owners:** Обязательный аппрув от владельцев путей (см. раздел 3).
* **Restrict pushes:** Только автоматизация (CI/CD Bot).

### Ветка: `develop` (Development / Integration)
* **Require a pull request before merging:** Включено.
* **Required approvals:** 1 (любой из `@org/engineers` или `@org/platform-admin`).
* **Status Checks:** Обязательное прохождение CI тестов и линтеров.

---

## 3. Владение кодом (CODEOWNERS)
Файл `.github/CODEOWNERS` жестко закрепляет зоны ответственности, исключая "тихие" правки.

```text
# Инфраструктура и безопасность (IaC)
/infra/                @org/platform-admin

# Данные и ML
/ml-research/          @org/engineers @org/platform-admin
/data-pipelines/       @org/engineers

# Бизнес-логика Camunda (BPMN/DMN)
/backend/processes/    @org/engineers @org/quality-gate

# Документация
/doc/                  @org/engineers @org/platform-admin
```

Пути вроде `/ml-research/` или `/backend/processes/` — целевые; подставьте фактические каталоги репозитория (например `bpmn/` для BPMN, `backend/` для API) или добавьте правила, когда появятся новые деревья.

---

## 4. Среды развертывания (Environments)
Настраиваются в *Settings -> Environments*. Каждая среда имеет свои секреты (GCP Keys) и правила аппрува.

### **Environment: `development`**
* **Deployment branch:** `develop`.
* **Reviewers:** Нет (автодеплой после мерджа).
* **Role Map:** Доступно для `dev-developer`, `dev-tester`.

### **Environment: `reference` (Staging)**
* **Deployment branch:** `release/*`, `develop`.
* **Reviewers:** `@org/quality-gate` (Роль: `ref-tester`).
* **Purpose:** Регрессионное тестирование перед выходом в прод.

### **Environment: `production`**
* **Deployment branch:** `main`.
* **Required Reviewers:**
  * Один из `@org/quality-gate` (роль: `release-manager`).
  * Один из `@org/platform-admin` (роль: SRE).
* **Wait Timer:** Опционально 15 минут для возможности отмены (Safety Gate).



---

## 5. Обработка Инцидентов (Break-Glass)
В случае критического сбоя (инцидента), когда стандартный цикл PR слишком медленный:
1. **SRE** использует временный токен доступа (через GCP PAM).
2. В GitHub используется временное "Emergency Override" (доступно только Admin), позволяющее мержить без аппрувов.
3. **Security / Compliance** проводят пост-мортем аудит логов на основе созданного в этот момент тикета.

---

## 6. Настройка CI/CD (GitHub Actions)
Для реализации разделения прав на уровне облака:
* Секрет `${{ secrets.GCP_SA_DEV }}` доступен только в окружении `development`.
* Секрет `${{ secrets.GCP_SA_PROD }}` доступен только в окружении `production` и защищен `Required Reviewers`.

---

**Итого:** 11 ролей сводятся к 4 группам в GitHub, которые управляют кодом через 3 барьера (Environments). Это обеспечивает прозрачность: мы всегда знаем, кто написал код (`engineers`), кто его проверил (`quality`), и кто разрешил выкатку в облако (`platform`).