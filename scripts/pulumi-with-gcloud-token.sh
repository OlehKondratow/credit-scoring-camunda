#!/usr/bin/env bash
# Local helper when Application Default Credentials are expired (invalid_grant)
# but `gcloud auth print-access-token` still works. Not for CI — use OIDC there.
set -euo pipefail
export PULUMI_USE_GCLOUD_USER_TOKEN=1
exec pulumi "$@"
