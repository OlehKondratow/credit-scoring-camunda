# Credit scoring + Camunda 8 — dokumentacja zbiorcza

Samodzielny projekt (historycznie wyodrębniony z [camunda8-tutorial](https://github.com/OlehKondratow/camunda8-tutorial)): **regresja logistyczna** (przepis cech z [0leh-kondratov/credit-scoring](https://github.com/0leh-kondratov/credit-scoring)), **job workery Zeebe** (`pyzeebe`), **BPMN**, **DMN**, **formularze** Modeler, notatnik EDA/ML (PL), materiały o skali (**KEDA**, GKE, Kafka, Keycloak) i **portalu bankowym** (Ingress, BFF).

**W skrócie:** kontur szkoleniowy scoringu kredytowego dla Camundy 8: trening → `joblib` → workery → przykłady BPMN/DMN/formularzy; osobne pliki MD — architektura, skala, warstwa web, specyfikacja portalu bankowego.

---

## Spis treści

1. [Cel i zakres](#1-cel-i-zakres)  
2. [Szybki start](#2-szybki-start)  
3. [Architektura logiczna](#3-architektura-logiczna)  
4. [Potok ML (trening → artefakt → inference)](#4-potok-ml-trening--artefakt--inference)  
5. [Kontrakt zmiennych procesu](#5-kontrakt-zmiennych-procesu)  
6. [Job workery (typy zadań)](#6-job-workery-typy-zadań)  
7. [Procesy BPMN](#7-procesy-bpmn)  
8. [DMN](#8-dmn)  
9. [Formularze Camunda 8](#9-formularze-camunda-8)  
10. [Notatnik Jupyter i katalog `data/`](#10-notatnik-jupyter-i-katalog-data)  
11. [Kontrakt modelu: score_bki, bki_request_cnt](#11-kontrakt-modelu-score_bki-bki_request_cnt)  
12. [Wdrożenie: lokalnie, Docker, GKE](#12-wdrożenie-lokalnie-docker-gke)  
13. [Indeks dokumentacji szczegółowej](#13-indeks-dokumentacji-szczegółowej)  
14. [Struktura katalogów (skrót)](#14-struktura-katalogów-skrót)  
15. [Repozytorium nadrzędne](#15-repozytorium-nadrzędne)

---

## 1. Cel i zakres

**Cel:** pokazać end-to-end **scoring kredytowy** z perspektywy Camunda 8: dane wejściowe → walidacja (opcjonalnie) → **model ML** (wyłącznie inference w runtime) → reguły **DMN** lub **worker routingu** → wynik w zmiennych procesu / formularzu.

**Poza zakresem:** produkcyjna integracja z zewnętrznymi źródłami informacji kredytowej, produkcyjny Keycloak/Helm pod pełną platformę Camunda (wskazówki w dokumentacji dodatkowej), workery Go z katalogu nadrzędnego (ten folder używa wyłącznie Pythona z `requirements.txt`).

---

## 2. Szybki start

```bash
cd /data/projects/credit-scoring-camunda   # lub ścieżka po klonowaniu tego katalogu
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Artefakt modelu (syntetyczne dane — bez train.csv)
python training/train.py --demo

# Alternatywa: skopiować train.csv z repozytorium credit-scoring → data/train.csv
# python training/train.py --data data/train.csv

export ZEEBE_ADDRESS=127.0.0.1:26500
python worker/run_worker.py
```

- Domyślnie **`WORKERS`** obejmuje **wszystkie trzy** typy: `c8jw-credit-validate`, `c8jw-credit-score`, `c8jw-credit-route`.  
- Sam scoring (jeden BPMN): `WORKERS=c8jw-credit-score python worker/run_worker.py`  
- Pełny Modeler (forma + DMN, **bez** route workera): `WORKERS=c8jw-credit-validate,c8jw-credit-score python worker/run_worker.py`

Wdrożenie zasobów Camundy: BPMN (+ ewentualnie formularze JSON, DMN) — Modeler lub CI; **kolejność** przy `bindingType latest` dla DMN opisano w [MODELER.md](MODELER.md).

---

## 3. Architektura logiczna

- **Orchestracja:** silnik **Zeebe** (BPMN 2.0); **Operate / Tasklist** — UI operacyjne (self-managed lub SaaS).  
- **Obciążenie ML:** proces **Zeebe Job** → worker **gRPC** (`ZEEBE_ADDRESS`).  
- **Reguły biznesowe:** **DMN** (Business Rule Task) *lub* worker `c8jw-credit-route` (progi środowiskowe).  
- **Uczenie modelu:** poza ścieżką pojedynczej wnioski (batch / notebook → plik `joblib`).

Diagramy, GKE, Kafka, KEDA: **[ARCHITECTURE.md](ARCHITECTURE.md)** oraz **[docs/operations-scale-identity-data.md](docs/operations-scale-identity-data.md)**.

**Łańcuch runtime (jedna wniosek):**

1. Formularz / API banku ustawia zmienne procesu (zgodnie z kontraktem).  
2. **Service task** → worker `c8jw-credit-score` ładuje **wersjonowany** `credit_model.joblib`, zwraca m.in. `defaultProbability`, `predictedDefault`.  
3. **DMN** (lub worker route) stosuje politykę na wyjściu ML.  
4. **User task** z formularzem wyjściowym lub dalsze kroki BPMN.

Retrening: `training/train.py` + nowa wersja pliku modelu / `MODEL_PATH` — **nie** wykonywane wewnątrz instancji procesu obsługującej klienta.

---

## 4. Potok ML (trening → artefakt → inference)

| Etap | Komponent | Opis |
|------|-----------|------|
| EDA / prototyp | `notebooks/credit-scoring-eda-ml.ipynb` | Analiza, logistyczna regresja (PL); źródło danych: `../data/train.csv` |
| Trening produkcyjny (skrypt) | `training/train.py` | Parametry: `--demo`, `--data`, `--out`, `--seed`, `--test-size`, `--tuned` |
| Artefakt | `models/credit_model.joblib` (gitignored poza demo) | Słownik: `version`, `model` (sklearn), `state` (mediany, kolejność kolumn one-hot itd.) |
| Inference | `worker/scoring.py` — klasa `CreditScorer` | Identyczny preprocessing jak w treningu; dopasowanie kolumn do `state["column_order"]` |

**Logika cech (skrót):** imputacja `education`, typy adresów, `ln(x+1)` dla wybranych liczb, `month` z `app_date` (format `01FEB2014`), cechy pośrednie `mean_income_*`, `mean_bki_*` z median treningowych, `pd.get_dummies` na kategoriach z `CAT_COLS` (zgodność: `training/train.py` ↔ `worker/scoring.py`).

Model: **LogisticRegression** z `class_weight='balanced'` (wariant `--tuned` z parametrem C jak w notatniku).

---

## 5. Kontrakt zmiennych procesu

### 5.1. Wejście (wymagane przed scoringiem)

Zmienne muszą mieć **dokładnie te klucze** (snake_case), zgodne z `REQUIRED_INPUT_KEYS` w `worker/scoring.py`:

| Klucz | Opis (skrót) |
|-------|----------------|
| `app_date` | Np. `01FEB2014` (`%d%b%Y`) |
| `education` | SCH, GRD, UGR, PGR, ACD |
| `sex` | M / F |
| `age` | Liczba (lata) |
| `car`, `car_type` | Y / N |
| `decline_app_cnt` | Liczba odrzuconych wniosków |
| `good_work` | 0 / 1 |
| `score_bki` | Scoring „z biura” w skali dataseta |
| `bki_request_cnt` | Liczba zapytań |
| `region_rating` | Rating regionu |
| `home_address`, `work_address` | Kategorie (w formularzu liczby jak w przykładzie) |
| `income` | Dochód |
| `sna` | Zmienna SNA z dataseta |
| `first_time` | 0 / 1 |
| `foreign_passport` | Y / N |

Opcjonalnie: `client_id` (ignorowane przy macierzy cech, jeśli obecne).

### 5.2. Wyjście — worker walidacji

| Zmienna | Typ / sens |
|---------|------------|
| `creditInputValid` | Boolean |
| `creditValidationErrors` | Tekst (np. brakujące klucze) |

### 5.3. Wyjście — worker ML (`c8jw-credit-score`)

| Zmienna | Opis |
|---------|------|
| `defaultProbability` | P(default), float |
| `predictedDefault` | 0 / 1 (próg 0.5 na prawdopodobieństwie) |
| `creditMlModelVersion` | Wersja bundle z `joblib` |

### 5.4. Wyjście — worker routingu (`c8jw-credit-route`) lub DMN

**Worker:** `creditRiskBand` (LOW / MEDIUM / HIGH), `routingHint`, `reviewRequired` — progi `CREDIT_THRESHOLD_HIGH` (domyślnie `0.5`), `CREDIT_THRESHOLD_MID` (`0.25`).

**DMN** `c8cs_credit_policy` → `creditPolicyDecision` (łańcuchy: m.in. `AUTO_APPROVE`, `STANDARD_REVIEW`, `MANUAL_UNDERWRITING`, `DECLINE_REVIEW`) — szczegół w `dmn/c8cs-post-ml-policy.dmn`.

---

## 6. Job workery (typy zadań)

Jeden proces OS: **`worker/run_worker.py`**. Rejestracja typów przez **`WORKERS`** (lista po przecinku).

| Job type | Moduł | Funkcja |
|----------|--------|---------|
| `c8jw-credit-validate` | `worker/validate.py` | Sprawdza komplet `REQUIRED_INPUT_KEYS` |
| `c8jw-credit-score` | `worker/scoring.py` | Ładuje `MODEL_PATH`, zwraca wyniki ML |
| `c8jw-credit-route` | `worker/route.py` | Progi na `defaultProbability`; **wyłączone** w procesie z samym DMN |

**Zmienne środowiskowe workera:** `ZEEBE_ADDRESS`, `MODEL_PATH`, `WORKERS`, `CREDIT_THRESHOLD_*`, `LOG_LEVEL`.

Pełna tabela i przykłady poleceń: **[WORKERS.md](WORKERS.md)**.

---

## 7. Procesy BPMN

| Plik | `id` procesu | Przepływ | Wymagane job types |
|------|----------------|-----------|---------------------|
| `bpmn/credit-score-process.bpmn` | `c8jw_credit_score_process` | Start → **jeden** service task ML → Koniec | `c8jw-credit-score` |
| `bpmn/credit-score-pipeline.bpmn` | `c8jw_credit_score_pipeline` | Walidacja → brama `creditInputValid` → ML → route worker → Koniec (lub ścieżka odrzucenia) | `c8jw-credit-validate`, `c8jw-credit-score`, `c8jw-credit-route` |
| `bpmn/c8cs-full-modeler.bpmn` | `c8cs_full_orchestration` | User task (forma wejścia) → walidacja → brama → ML → **DMN** → user task (forma wyjścia) / gałąź błędu | `c8jw-credit-validate`, `c8jw-credit-score` (bez route) |

W dokumentacji XML każdego pliku znajduje się opis zmiennych dla Modeler / Operate.

---

## 8. DMN

| Plik | `decisionId` | Wynik (resultVariable w BPMN) |
|------|----------------|--------------------------------|
| `dmn/c8cs-post-ml-policy.dmn` | `c8cs_credit_policy` | `creditPolicyDecision` |

Wejścia FEEL: `defaultProbability`, `predictedDefault` (z workera ML). Dostosowanie progów — edycja literału FEEL w DMN.

---

## 9. Formularze Camunda 8

| `id` (formId) | Plik | Przeznaczenie |
|----------------|------|----------------|
| `c8cs_applicant_input` | `forms/c8cs_applicant_input.form` | Pola = kontrakt wejścia (klucze jak w §5.1); dopiski o score_bki / bki_request_cnt bez wskazywania dostawcy danych |
| `c8cs_decision_output` | `forms/c8cs_decision_output.form` | Pola read-only: walidacja, ML, `creditPolicyDecision` |

**Execution platform:** Camunda Cloud 8.6 (metadane w JSON); self-managed Tasklist zwykle akceptuje te same formularze przy zgodnej wersji.

Instrukcja wdrożenia pod Modeler: **[MODELER.md](MODELER.md)**.

---

## 10. Notatnik Jupyter i katalog `data/`

- **`notebooks/credit-scoring-eda-ml.ipynb`** — przetłumaczony (PL) notatnik z repozytorium źródłowego; ścieżka CSV: `../data/train.csv`.  
- **`data/train.csv`** — nie commitowany (`.gitignore`); źródło: [credit-scoring/train.csv](https://github.com/0leh-kondratov/credit-scoring).  
- **`data/bik-synthetic-snapshot.example.json`** — fikcyjny przykład mapowania pól ze źródła informacji kredytowej (zob. `data/README.md`).  
- **`data/README.md`** — opis katalogu.

---

## 11. Kontrakt modelu: score_bki, bki_request_cnt

Nazwy **`score_bki`** i **`bki_request_cnt`** są **kontraktem** wobec zbioru treningowego i workera; zmiana kluczy w procesie bez retreningu lub warstwy mapującej psuje spójność inference.

Mapowanie na źródła w runtime, nazewnictwo dataseta vs produkcja, krótkie zastrzeżenie prawne: **[docs/bik-kontekst.md](docs/bik-kontekst.md)**.

---

## 12. Wdrożenie: lokalnie, Docker, GKE

**Lokalnie:** Zeebe (np. Docker Compose z repozytorium nadrzędnego) + worker jak w §2.

**Docker (worker):**

```bash
# Z katalogu głównego tego projektu; wymaga models/credit_model.joblib (np. po training/train.py --demo)
docker build -t credit-score-worker -f Dockerfile .
docker run -e ZEEBE_ADDRESS=host.docker.internal:26500 credit-score-worker
```

Obraz kopiuje `worker/*.py` i model — przy aktualizacji modelu przebuduj obraz lub montuj wolumen / użyj initContainer w K8s.

**GKE:** `Deployment` workera, `ZEEBE_ADDRESS` wskazujący na Service bramki Zeebe w klastrze; Workload Identity; modele z GCS/PVC — **[ARCHITECTURE.md](ARCHITECTURE.md)**, **[ściąga GKE](https://github.com/OlehKondratow/camunda8-tutorial/blob/main/docs/gke-camunda-cheatsheet.md)**.

---

## 13. Indeks dokumentacji szczegółowej

| Dokument | Treść |
|----------|--------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Diagram warstw, ML vs runtime, Camunda, workerzy, GKE, Kafka, link do KEDA |
| [WORKERS.md](WORKERS.md) | Tabela job types, BPMN ↔ worker, env, przykłady `WORKERS=…` |
| [MODELER.md](MODELER.md) | Kolejność deploy form + DMN + BPMN pełnego procesu |
| [docs/bik-kontekst.md](docs/bik-kontekst.md) | Pola `score_bki` / `bki_request_cnt`, dataset vs runtime, zastrzeżenia |
| [docs/camunda-external-web.md](docs/camunda-external-web.md) | Tasklist, Operate, Ingress, API Gateway, Zeebe gRPC |
| [docs/tz-bank-portal-camunda.md](docs/tz-bank-portal-camunda.md) | Specyfikacja portalu bankowego: SPA + BFF + Camunda 8 |
| [docs/operations-scale-identity-data.md](docs/operations-scale-identity-data.md) | Skala użytkowników i procesów, Keycloak/Azure, SQL, MLOps, data lake, **KEDA** |

---

## 14. Struktura katalogów (skrót)

```
credit-scoring-camunda/
├── ARCHITECTURE.md
├── MODELER.md
├── WORKERS.md
├── README.md                 ← ten plik
├── requirements.txt
├── Dockerfile
├── training/
│   └── train.py
├── worker/
│   ├── run_worker.py
│   ├── scoring.py
│   ├── validate.py
│   └── route.py
├── models/
│   └── credit_model.joblib   # po treningu (gitignored)
├── bpmn/
│   ├── credit-score-process.bpmn
│   ├── credit-score-pipeline.bpmn
│   └── c8cs-full-modeler.bpmn
├── dmn/
│   └── c8cs-post-ml-policy.dmn
├── forms/
│   ├── c8cs_applicant_input.form
│   └── c8cs_decision_output.form
├── notebooks/
│   └── credit-scoring-eda-ml.ipynb
├── data/
│   ├── README.md
│   └── bik-synthetic-snapshot.example.json
└── docs/
    ├── bik-kontekst.md
    ├── camunda-external-web.md
    ├── tz-bank-portal-camunda.md
    └── operations-scale-identity-data.md
```

---

## 15. Repozytorium nadrzędne i Git

Folder **nie** zależy od workerów **Go** w `zeebe-tutorial/`. Zależności wyłącznie z **`requirements.txt`** (Python).

Szerszy kontekst szkoleniowy (Helm, GKE, inne BPMN): repozytorium [camunda8-tutorial](https://github.com/OlehKondratow/camunda8-tutorial).

Po przeniesieniu katalogu poza klona **camunda8-tutorial** nie ma tu automatycznie własnego `.git` — jeśli potrzebujesz osobnego repozytorium: `git init`, dodaj `remote`, utwórz `python3 -m venv .venv` na nowo (stary `.venv` usunięto ze względu na bezwzględne ścieżki w skryptach).
