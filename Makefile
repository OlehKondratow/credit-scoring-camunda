.PHONY: install dev lint format test cov docker-build clean

install:
	pip install .

dev:
	pip install -e ".[dev]"

lint:
	ruff check worker training tests
	ruff format --check worker training tests

format:
	ruff format worker training tests
	ruff check --fix worker training tests

test:
	pytest

cov:
	pytest --cov=worker --cov-report=term-missing

docker-build:
	docker build -t credit-score-worker .

clean:
	rm -rf build dist *.egg-info .coverage htmlcov .pytest_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

ci: lint test
