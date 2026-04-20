# Millennium Bank — automated credit decision (RAG + Camunda 8)

[![CI](https://github.com/OlehKondratow/credit-scoring-camunda/actions/workflows/ci.yml/badge.svg?branch=millennium-credit-v2)](https://github.com/OlehKondratow/credit-scoring-camunda/actions/workflows/ci.yml)

**Vertex AI** (Vector Search + Gemini), **Camunda 8 / Zeebe**, **GKE (`europe-central2`)**, **Streamlit** dla analityków.

| Doc | Purpose |
|-----|---------|
| [doc/prompt.md](doc/prompt.md) | Handoff, plan, enterprise blueprint |
| [doc/git-workflow.md](doc/git-workflow.md) | Branches, `release/*`, tags |
| [doc/github-setup.md](doc/github-setup.md) | Branch protection, Environments (GitHub UI) |
| [doc/naming.md](doc/naming.md) | Repo / branch / tag naming (avoid `Credit-Scoring-V2` as brand) |
| [doc/cli-console.md](doc/cli-console.md) | CLI commands (Pulumi, `kubectl`, Docker) |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Tests, PR expectations |
| [SECURITY.md](SECURITY.md) | Vulnerability reporting |

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
| `scripts/` | `create-release-branch.sh` — ветка `release/X.Y.Z` |
| `.github/workflows/ci.yml` | CI: `pytest` backend + worker (Python 3.11 / 3.12) |

## Local run

```bash
docker compose up --build
```

Tests:

```bash
make test
```

- API: `http://localhost:8000/docs`
- UI: `http://localhost:8501`
- Zeebe: `localhost:26500`

Service task type: **`ai-loan-analysis`**, process variable: **`application`** (JSON). On backend timeout the worker throws BPMN error **`AI_SERVICE_TIMEOUT`**.

## Region

Default: **`europe-central2` (Warsaw)** — config, Terraform, manifests.
