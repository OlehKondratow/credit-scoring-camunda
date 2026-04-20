#!/usr/bin/env bash
# Break-glass: do NOT use for routine access. Follow org runbook + GCP Privileged Access Manager (PAM).
# This script only documents the intent; elevation is done in GCP Console / PAM with ticket ID.

set -euo pipefail

echo "Break-glass access is not granted by this repository script." >&2
echo "Use your organization's incident process: open SEV ticket, request time-bound elevation via GCP PAM," >&2
echo "and record commands / postmortem per infra/ROLES.md." >&2
exit 1
