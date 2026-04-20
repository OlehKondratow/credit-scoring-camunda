# Millennium Bank — automated credit decision (RAG + Camunda 8)

**Vertex AI** (Vector Search + Gemini), **Camunda 8 / Zeebe**, **GKE (`europe-central2`)**, **Streamlit** dla analityków.

## Layout

| Path | Purpose |
|------|---------|
| `infra/pulumi/` | **Основной IaC (Pulumi):** GCS, Artifact Registry, API |
| `infra/ROLES.md` | Роли: DevOps/SRE, dev-developer, dev-tester, ref-tester, prod-tester, prod-user |
| `infra/ARCHITECTURE.md` | Изоляция сред и namespaces |
| `infra/terraform/` | Справочный Terraform (legacy) |
| `backend/` | FastAPI + LangGraph (`/analyze`) |
| `worker/` | PyZeebe (`ai-loan-analysis`) |
| `ui/` | Streamlit |
| `data/` | `ingest.py` — PDF → chunks → `text-embedding-004` |
| `bpmn/`, `dmn/` | `millennium-loan-process.bpmn`, `scoring-rules.dmn` |
| `k8s/millennium/` | Deployments, Services, HPA, Secret example |
| `docker-compose.yml` | Local: Zeebe + backend + worker + UI |
| `doc/prompt.md` | Plan realizacji (skrócony) |

## Local run

```bash
docker compose up --build
```

- API: `http://localhost:8000/docs`
- UI: `http://localhost:8501`
- Zeebe: `localhost:26500`

Service task type: **`ai-loan-analysis`**, process variable: **`application`** (JSON). On backend timeout the worker throws BPMN error **`AI_SERVICE_TIMEOUT`**.

## Region

Default: **`europe-central2` (Warsaw)** — config, Terraform, manifests.
