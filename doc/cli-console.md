# CLI / console — Millennium Credit

Копируемые команды. Значения ниже соответствуют целевой конфигурации репозитория и активному GCP-проекту **`my-camunda8-project`**.

| Параметр | Значение |
|----------|-----------|
| **GCP project** | `my-camunda8-project` |
| **Регион данных (Vertex, GCS, BQ, Artifact Registry в манифестах)** | `europe-central2` |
| **Имя репозитория Docker (Pulumi `credit-scoring:clusterName`)** | `millennium-credit-gke` → образы: `…/millennium-credit-gke-docker/…` |
| **Kubernetes namespace** | `millennium-credit` |
| **Job type Zeebe** | `ai-loan-analysis` |
| **GKE в проекте (существующий кластер)** | `camunda-stable`, зона `europe-west3-c` |

Путь к клону на диске в примерах: **`/data/projects/Credit-Scoring-V2`**.

Дополнительно: `doc/prompt.md`, `doc/ml-data-rag.md`, `infra/pulumi/README.md`.

---

## Локально: Docker Compose (Zeebe + backend + worker + UI)

```bash
cd /data/projects/Credit-Scoring-V2
docker compose up --build
```

- API: `http://127.0.0.1:8000` — `GET /healthz`, `POST /analyze`
- Streamlit: `http://127.0.0.1:8501`
- Zeebe gateway: `127.0.0.1:26500`

---

## Локально: worker без Compose

```bash
cd /data/projects/Credit-Scoring-V2/worker
pip install -r requirements.txt
export PYTHONPATH="${PWD}"
export ZEEBE_ADDRESS=127.0.0.1:26500
export BACKEND_URL=http://127.0.0.1:8000
export AI_TIMEOUT_S=45
python -m app.main
```

---

## Pulumi (`infra/pulumi/`)

```bash
cd /data/projects/Credit-Scoring-V2/infra/pulumi
python3 -m venv venv && . venv/bin/activate
pip install -r requirements.txt
```

Локальный backend state Pulumi (если `pulumi: command not found` — CLI не в `PATH`, см. `infra/pulumi/README.md`):

```bash
export PATH="${HOME}/.pulumi/bin:${PATH}"
pulumi login --local
export PULUMI_CONFIG_PASSPHRASE='changeme'
pulumi stack init dev
pulumi config set gcp:project my-camunda8-project
pulumi config set credit-scoring:region europe-central2
pulumi config set credit-scoring:clusterName millennium-credit-gke
gcloud auth application-default login
pulumi preview
pulumi up
pulumi stack output --json
```

Экспорты: `gcp_project`, `gcp_region`, `artifact_repository_id`, `artifact_registry_url`, `vector_embeddings_bucket`, `raw_regulations_bucket`, `bigquery_dataset` — см. `infra/pulumi/__main__.py`.

---

## GCP и kubectl

Активный проект и список кластеров:

```bash
gcloud config set project my-camunda8-project
gcloud container clusters list --project=my-camunda8-project
```

Kubeconfig для **текущего** кластера Camunda в этом проекте:

```bash
gcloud container clusters get-credentials camunda-stable \
  --zone=europe-west3-c \
  --project=my-camunda8-project
kubectl config current-context
kubectl get ns
```

Манифесты Millennium (`k8s/millennium/`) рассчитаны на образы в **`europe-central2-docker.pkg.dev`**. Отдельный кластер в **`europe-central2`** под этот стек нужно создать и настроить (IaC / консоль); кластер **`camunda-stable`** находится в **`europe-west3-c`**.

---

## Kubernetes: `k8s/millennium/`

В `deployment-*.yaml` замените плейсхолдер **`PROJECT_ID`** на **`my-camunda8-project`** (или примените через `envsubst` / правку в редакторе).

Секреты не коммитить: скопировать `secret-env.example.yaml` → `secret-env.yaml`, выставить `GOOGLE_CLOUD_PROJECT: "my-camunda8-project"` и токены.

```bash
cd /data/projects/Credit-Scoring-V2
kubectl apply -f k8s/millennium/namespace.yaml
kubectl apply -f k8s/millennium/secret-env.yaml
kubectl apply -f k8s/millennium/serviceaccount-backend.yaml
kubectl apply -f k8s/millennium/deployment-backend.yaml
kubectl apply -f k8s/millennium/deployment-worker.yaml
kubectl apply -f k8s/millennium/deployment-ui.yaml
kubectl -n millennium-credit get pods,svc
kubectl -n millennium-credit logs deploy/credit-worker -f
kubectl -n millennium-credit logs deploy/credit-backend -f
```

---

## Образы: сборка и push (регион `europe-central2`)

После `pulumi up` проверьте `artifact_registry_url` в выводе стека.

```bash
export REGION=europe-central2
export PROJECT_ID=my-camunda8-project
export REPO=millennium-credit-gke-docker

docker build -t credit-backend:latest /data/projects/Credit-Scoring-V2/backend
docker tag credit-backend:latest \
  ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/credit-backend:latest
gcloud auth configure-docker ${REGION}-docker.pkg.dev --project=${PROJECT_ID}
docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/credit-backend:latest
```

Аналогично: контексты сборки `worker/` → `credit-worker`, `ui/` → `credit-ui`; теги должны совпадать с `deployment-*.yaml`.

---

## GitOps: Argo CD

Установка в кластер и пример `Application` для `k8s/millennium/`: **`k8s/argocd/README.md`**.

---

## BPMN

Процесс: `bpmn/millennium-loan-process.bpmn` — service task с типом **`ai-loan-analysis`**, затем DMN `scoring-rules`.
