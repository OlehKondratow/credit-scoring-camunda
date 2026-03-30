# Build from project root: docker build -t credit-score-worker ./credit-scoring-camunda
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY worker/scoring.py worker/run_worker.py ./worker/
COPY models/credit_model.joblib ./models/credit_model.joblib

ENV MODEL_PATH=/app/models/credit_model.joblib

WORKDIR /app/worker
CMD ["python", "run_worker.py"]
