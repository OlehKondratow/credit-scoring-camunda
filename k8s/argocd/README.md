# Argo CD на GKE (GitOps)

Argo CD ставится **в кластер** один раз; дальше он подтягивает манифесты из git (например `k8s/millennium/`). Инфраструктура GCP по-прежнему через **`infra/pulumi/`**, не через Argo, если не выбрана отдельная политика.

## Требования

- `kubectl` и контекст на целевой GKE (`gcloud container clusters get-credentials …`)
- Для варианта A — [Helm 3](https://helm.sh/)

## A. Установка через Helm (предпочтительно для обновлений)

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
kubectl create namespace argocd

helm upgrade --install argocd argo/argo-cd \
  --namespace argocd \
  --set server.service.type=ClusterIP
```

В проде закрепите версию chart (`helm search repo argo/argo-cd --versions` или [Artifact Hub](https://artifacthub.io/packages/helm/argo/argo-cd)) параметром `--version …`.

## B. Установка официальными манифестами (без Helm)

```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

## Первый доступ (порт-форвард)

Пароль начального пользователя `admin`:

```bash
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d && echo
```

UI:

```bash
kubectl -n argocd port-forward svc/argocd-server 8080:443
```

Откройте `https://localhost:8080`, логин `admin`, пароль из команды выше. Дальше смените пароль / настройте SSO (OIDC).

## Внешний доступ (GKE)

Не оставляйте `argocd-server` с публичным `LoadBalancer` без TLS и политики доступа. Типично: **Ingress** + **ManagedCertificate** (GKE) или **IAP**, либо доступ только из корпоративной сети / VPN.

## Подключение репозитория (приватный GitHub)

Создайте **Secret** с учётными данными (token / deploy key) в namespace `argocd` по [документации Argo CD](https://argo-cd.readthedocs.io/en/stable/user-guide/private-repositories/), затем создайте `Application` (см. `application-millennium-sample.yaml`).

## Применение примера Application

1. Отредактируйте `application-millennium-sample.yaml`: `repoURL`, `targetRevision`, при необходимости `path`.
2. Примените:

```bash
kubectl apply -f k8s/argocd/application-millennium-sample.yaml
```

Проверка: `kubectl -n argocd get applications.argoproj.io`.

## Регион и проект

Кластер обычно в **`europe-central2`** (см. `.cursorrules`). Версии образов и секреты приложений остаются в git или External Secrets — не дублируйте пароли в этом README.
