# Multi-stage: train a demo model in CI-friendly builds (no pre-existing joblib required).
# Build: docker build -t credit-score-worker .

FROM python:3.12-slim AS trainer
WORKDIR /app
ENV PIP_NO_CACHE_DIR=1
COPY pyproject.toml README.md ./
COPY worker ./worker/
COPY training ./training/
RUN pip install --no-cache-dir .
RUN python training/train.py --demo --out /tmp/credit_model.joblib --seed 42

FROM python:3.12-slim AS runtime
WORKDIR /app
ENV PIP_NO_CACHE_DIR=1 \
    MODEL_PATH=/app/models/credit_model.joblib
COPY pyproject.toml README.md ./
COPY worker ./worker/
COPY --from=trainer /tmp/credit_model.joblib ./models/credit_model.joblib
RUN pip install --no-cache-dir . \
    && useradd --system --uid 10001 --home /app appuser \
    && chown -R appuser:appuser /app
USER appuser
CMD ["credit-score-worker"]
