"""
Optional: Workload Identity Federation for GitHub Actions → GCP (OIDC, no JSON keys).

Enable with:
  pulumi config set credit-scoring:enableGithubWif true
  pulumi config set credit-scoring:githubOwner OlehKondratow
  pulumi config set credit-scoring:githubRepo credit-scoring-camunda

This module creates the pool, OIDC provider, a service account, and
`roles/iam.workloadIdentityUser` for the GitHub repo principal.
It does **not** grant broad project roles on that SA — add least-privilege
roles separately (console, IaC policy, or follow-up stack) before CI runs `pulumi up`.

See: https://github.com/google-github-actions/auth#workload-identity-federation
"""

from __future__ import annotations

import pulumi
import pulumi_gcp as gcp


def provision(
    *,
    provider: gcp.Provider,
    project_id: str,
    region: str,
) -> None:
    _ = region  # reserved for future regional constraints
    cfg = pulumi.Config("credit-scoring")
    if not cfg.get_bool("enableGithubWif"):
        return

    owner = cfg.require("githubOwner")
    repo = cfg.require("githubRepo")
    pool_id = cfg.get("githubWifPoolId") or "github-actions-pool"
    provider_id = cfg.get("githubWifProviderId") or "github-provider"
    sa_id = cfg.get("githubActionsSaId") or "github-actions-ci"

    iam_api = gcp.projects.Service(
        "iam_api_for_wif",
        project=project_id,
        service="iam.googleapis.com",
        disable_on_destroy=False,
        opts=pulumi.ResourceOptions(provider=provider),
    )

    pool = gcp.iam.WorkloadIdentityPool(
        "github_wif_pool",
        workload_identity_pool_id=pool_id,
        display_name="GitHub Actions",
        description="OIDC federation for GitHub Actions (Millennium Credit)",
        opts=pulumi.ResourceOptions(provider=provider, depends_on=[iam_api]),
    )

    # GitHub OIDC: keep mapping minimal; attribute_condition must reference assertion.* claims (GCP validation).
    repo_fq = f"{owner}/{repo}"
    wif_provider = gcp.iam.WorkloadIdentityPoolProvider(
        "github_wif_provider",
        workload_identity_pool_id=pool.workload_identity_pool_id,
        workload_identity_pool_provider_id=provider_id,
        display_name="GitHub OIDC",
        attribute_mapping={
            "google.subject": "assertion.sub",
            "attribute.actor": "assertion.actor",
            "attribute.repository": "assertion.repository",
            "attribute.repository_owner": "assertion.repository_owner",
        },
        # Restrict tokens to this repo (CEL over incoming OIDC claims).
        attribute_condition=f'assertion.repository == "{repo_fq}"',
        oidc=gcp.iam.WorkloadIdentityPoolProviderOidcArgs(
            issuer_uri="https://token.actions.githubusercontent.com",
        ),
        opts=pulumi.ResourceOptions(provider=provider, depends_on=[pool]),
    )

    sa = gcp.serviceaccount.Account(
        "github_actions_ci",
        account_id=sa_id,
        display_name="GitHub Actions CI",
        opts=pulumi.ResourceOptions(provider=provider),
    )

    proj = gcp.organizations.get_project(project_id=project_id)

    principal_member = pulumi.Output.all(proj.number, pool.workload_identity_pool_id).apply(
        lambda args: (
            "principalSet://iam.googleapis.com/"
            f"projects/{args[0]}/locations/global/workloadIdentityPools/{args[1]}"
            f"/attribute.repository/{repo_fq}"
        )
    )

    gcp.serviceaccount.IAMMember(
        "github_actions_wi_user",
        service_account_id=sa.name,
        role="roles/iam.workloadIdentityUser",
        member=principal_member,
        opts=pulumi.ResourceOptions(provider=provider, depends_on=[wif_provider, sa]),
    )

    pulumi.export(
        "github_workload_identity_provider",
        pulumi.Output.all(proj.number, pool.workload_identity_pool_id).apply(
            lambda args: (
                f"projects/{args[0]}/locations/global/workloadIdentityPools/{args[1]}"
                f"/providers/{provider_id}"
            )
        ),
    )
    pulumi.export("github_actions_service_account_email", sa.email)
