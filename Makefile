.PHONY: test test-backend test-worker
.PHONY: compose-up compose-down
.PHONY: release-branch

# Create release/X.Y.Z from develop (requires clean tree). Example: make release-branch VERSION=1.2.0
release-branch:
	@test -n "$(VERSION)" || (echo "Usage: make release-branch VERSION=1.2.0" >&2; exit 1)
	@scripts/create-release-branch.sh "$(VERSION)"

test: test-backend test-worker

test-backend:
	cd backend && pytest -q

test-worker:
	cd worker && PYTHONPATH=. pytest -q

compose-up:
	docker compose up --build

compose-down:
	docker compose down
