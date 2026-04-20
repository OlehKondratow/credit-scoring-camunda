# Contributing

## Branches and releases

See **[doc/git-workflow.md](doc/git-workflow.md)** (integration **`develop`**, production **`main`**, tags **`v*`**). Branch notes: **[doc/branch-notes.md](branch-notes.md)**. GitHub UI: **[doc/github-setup.md](doc/github-setup.md)**.

Release branch helper: `./scripts/create-release-branch.sh 1.2.0` or `make release-branch VERSION=1.2.0`.

## Local checks

```bash
# Backend
cd backend && pip install -r requirements.txt pytest && pytest -q

# Worker
cd worker && pip install -r requirements.txt pytest && PYTHONPATH=. pytest -q
```

CI runs the same on Python **3.11** and **3.12** (`.github/workflows/ci.yml`).

## Code style

- Python: match existing modules; comments in **English** (see `.cursorrules`).
- Infra: **`infra/pulumi/`** is the primary IaC path; avoid duplicating resource names with legacy Terraform without import.

## Security

Do not commit credentials. Use environment variables, Kubernetes Secrets, or GCP Secret Manager. Report vulnerabilities according to **[SECURITY.md](SECURITY.md)**.
