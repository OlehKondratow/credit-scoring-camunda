# Contributing

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Quality checks

```bash
make lint    # ruff check + format --check
make format  # auto-fix and format
make test
make ci      # lint + test
```

Training and worker code must stay aligned: feature lists and preprocessing in `training/train.py` and `worker/scoring.py` must match.

## Running the worker locally

From the repository root (after `pip install -e .`):

```bash
export ZEEBE_ADDRESS=127.0.0.1:26500
python -m worker.run_worker
```

## Pull requests

- Keep changes scoped and documented in the PR description.
- Ensure `make ci` passes (Ruff + pytest).
