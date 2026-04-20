"""
Pulumi program: GCS (embeddings + raw PDFs), BigQuery analytics, Artifact Registry, key APIs.
Configure: pulumi config set gcp:project PROJECT

Optional (enterprise CI): GitHub OIDC → GCP — см. workload_identity_github.py и infra/pulumi/README.md.
"""

import os
import subprocess

import pulumi
import pulumi_gcp as gcp
import pulumi_random as random

from workload_identity_github import provision as provision_github_wif


def _gcp_provider_args(project: str, reg: str) -> dict:
    """
    If Application Default Credentials are stale (invalid_grant), use a fresh user token:
      PULUMI_USE_GCLOUD_USER_TOKEN=1 pulumi preview
    CI should use OIDC / SA JSON via normal ADC, not this.
    """
    args = {"project": project, "region": reg}
    if os.environ.get("PULUMI_USE_GCLOUD_USER_TOKEN", "").lower() in ("1", "true", "yes"):
        tok = subprocess.run(
            ["gcloud", "auth", "print-access-token"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        args["access_token"] = pulumi.Output.secret(tok)
    return args


gcp_cfg = pulumi.Config("gcp")
project_id = gcp_cfg.require("project")

# Namespace matches README / Pulumi.*.yaml: `pulumi config set credit-scoring:region ...`
cfg = pulumi.Config("credit-scoring")
region = cfg.get("region") or "europe-central2"
cluster_name = cfg.get("clusterName") or "millennium-credit-gke"
repo_id = cluster_name.replace("_", "-") + "-docker"

provider = gcp.Provider("gcp", **_gcp_provider_args(project_id, region))

suffix = random.RandomString(
    "bucket_suffix",
    length=4,
    lower=True,
    upper=False,
    numeric=True,
    special=False,
)

artifactregistry_api = gcp.projects.Service(
    "artifactregistry_api",
    project=project_id,
    service="artifactregistry.googleapis.com",
    disable_on_destroy=False,
    opts=pulumi.ResourceOptions(provider=provider),
)

aiplatform_api = gcp.projects.Service(
    "aiplatform_api",
    project=project_id,
    service="aiplatform.googleapis.com",
    disable_on_destroy=False,
    opts=pulumi.ResourceOptions(provider=provider),
)

bigquery_api = gcp.projects.Service(
    "bigquery_api",
    project=project_id,
    service="bigquery.googleapis.com",
    disable_on_destroy=False,
    opts=pulumi.ResourceOptions(provider=provider),
)

storage_api = gcp.projects.Service(
    "storage_api",
    project=project_id,
    service="storage.googleapis.com",
    disable_on_destroy=False,
    opts=pulumi.ResourceOptions(provider=provider),
)

bucket_name = pulumi.Output.concat(project_id, "-pulumi-emb-", suffix.result)
raw_bucket_name = pulumi.Output.concat(project_id, "-pulumi-raw-", suffix.result)

bucket = gcp.storage.Bucket(
    "vector_embeddings",
    name=bucket_name,
    location=region,
    uniform_bucket_level_access=True,
    opts=pulumi.ResourceOptions(provider=provider, depends_on=[storage_api]),
)

raw_pdfs_bucket = gcp.storage.Bucket(
    "raw_regulations",
    name=raw_bucket_name,
    location=region,
    uniform_bucket_level_access=True,
    opts=pulumi.ResourceOptions(provider=provider, depends_on=[storage_api]),
)

bq_dataset = gcp.bigquery.Dataset(
    "millennium_analytics",
    dataset_id="millennium_analytics",
    project=project_id,
    location=region,
    friendly_name="Millennium loan / RAG analytics",
    description="Query logs, offline eval exports, token/cost aggregates (no raw PII).",
    opts=pulumi.ResourceOptions(provider=provider, depends_on=[bigquery_api]),
)

repo = gcp.artifactregistry.Repository(
    "app",
    repository_id=repo_id,
    location=region,
    format="DOCKER",
    description="credit-backend, credit-worker, credit-ui (Pulumi sample)",
    opts=pulumi.ResourceOptions(provider=provider, depends_on=[artifactregistry_api]),
)

pulumi.export("gcp_project", project_id)
pulumi.export("gcp_region", region)
pulumi.export("cluster_name", cluster_name)
pulumi.export("artifact_repository_id", repo_id)
pulumi.export("vector_embeddings_bucket", bucket.name)
pulumi.export("raw_regulations_bucket", raw_pdfs_bucket.name)
pulumi.export("bigquery_dataset", bq_dataset.dataset_id)
pulumi.export("artifact_registry_url", pulumi.Output.concat(region, "-docker.pkg.dev/", project_id, "/", repo_id))

provision_github_wif(provider=provider, project_id=project_id, region=region)
