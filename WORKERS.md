# Lista workerów (job types) — `credit-scoring-camunda`

Wszystkie handlery są w jednym procesie Python: **`python -m worker.run_worker`** (`pyzeebe`), z katalogu głównego repozytorium.  
Wybór aktywnych typów: zmienna środowiskowa **`WORKERS`** (lista po przecinku). Domyślnie: wszystkie trzy.

| Job type | Plik | Rola |
|----------|------|------|
| **`c8jw-credit-validate`** | `worker/validate.py` | Sprawdza obecność wymaganych zmiennych procesu (`REQUIRED_INPUT_KEYS` w `worker/scoring.py`). Zwraca m.in. `creditInputValid`, `creditValidationErrors`. |
| **`c8jw-credit-score`** | `worker/scoring.py` | Wczytuje `MODEL_PATH` / `models/credit_model.joblib`, liczy `defaultProbability`, `predictedDefault`, `creditMlModelVersion`. |
| **`c8jw-credit-route`** | `worker/route.py` | Progi `CREDIT_THRESHOLD_HIGH` / `CREDIT_THRESHOLD_MID` → `creditRiskBand`, `routingHint`, `reviewRequired`. **Nie** jest używany w procesie `c8cs_full_orchestration` (tam routing jest w DMN). |

## BPMN a workery

| Proces (plik BPMN) | Używane job types |
|--------------------|-------------------|
| `credit-score-process.bpmn` (`c8jw_credit_score_process`) | `c8jw-credit-score` |
| `credit-score-pipeline.bpmn` (`c8jw_credit_score_pipeline`) | `c8jw-credit-validate`, `c8jw-credit-score`, `c8jw-credit-route` |
| `c8cs-full-modeler.bpmn` (`c8cs_full_orchestration`) | `c8jw-credit-validate`, `c8jw-credit-score` |

## Zmienne środowiskowe

| Zmienna | Domyślnie | Znaczenie |
|---------|-----------|-----------|
| `ZEEBE_ADDRESS` | `127.0.0.1:26500` | Adres bramki gRPC Zeebe |
| `MODEL_PATH` | `<root>/models/credit_model.joblib` | Paczka `joblib` z modelem |
| `WORKERS` | wszystkie trzy typy | Ograniczenie zarejestrowanych handlerów |
| `CREDIT_THRESHOLD_HIGH` | `0.5` | Tylko dla `c8jw-credit-route` |
| `CREDIT_THRESHOLD_MID` | `0.25` | Tylko dla `c8jw-credit-route` |
| `LOG_LEVEL` | `INFO` | Poziom logów |

## Przykłady uruchomienia

```bash
# Pipeline techniczny (walidacja + ML + routing w workerze)
python -m worker.run_worker

# Tylko scoring (np. przy starcie BPMN `credit-score-process`)
WORKERS=c8jw-credit-score python -m worker.run_worker

# Modeler: formularz + walidacja + ML + DMN (bez job type route)
WORKERS=c8jw-credit-validate,c8jw-credit-score python -m worker.run_worker
```
