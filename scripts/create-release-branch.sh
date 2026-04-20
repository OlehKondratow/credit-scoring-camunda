#!/usr/bin/env bash
# Create release/X.Y.Z from up-to-date develop (see doc/git-workflow.md).
set -euo pipefail

usage() {
  echo "Usage: $0 <major.minor.patch>" >&2
  echo "Example: $0 1.2.0  -> creates branch release/1.2.0" >&2
  exit 1
}

[[ "${1:-}" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || usage

VERSION="$1"
BASE="${RELEASE_BASE_BRANCH:-develop}"
REMOTE="${GIT_REMOTE:-origin}"

git fetch "${REMOTE}"
git switch "${BASE}"
git pull "${REMOTE}" "${BASE}"
git switch -c "release/${VERSION}"

echo "Created branch release/${VERSION} from ${BASE}."
echo "Next: push with  git push -u ${REMOTE} release/${VERSION}"
echo "Then: open PR into ${BASE} or merge per team policy; tag v${VERSION} after acceptance."
