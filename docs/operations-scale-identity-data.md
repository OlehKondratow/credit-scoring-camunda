# Skala (100 / 1000 użytkowników), Keycloak/LDAP/Azure, SQL, wersje modeli, data lake

Uzupełnienie **[ARCHITECTURE.md](../ARCHITECTURE.md)** — wskazówki wdrożeniowe, nie instrukcja krok po kroku.

---

## 1. „100 vs 1000 userów” — o co chodzi?

Trzeba rozróżnić:

| Pojęcie | Co skalować |
|---------|-------------|
| **Użytkownicy Tasklist / Operate** (ludzie w banku) | Keycloak (realm), sesje, licencje Camunda; przy SSO — obciążenie IdP (Azure AD). Setki–tysiące kont to standard dla Keycloak przy sensownej JVM/DB. |
| **Równoległe instancje procesów BPMN** | **Partycje Zeebe**, liczba brokerów, **repliki workerów** (`Deployment` w GKE: `replicas: N`). Worker jest bezstanowy względem Zeebe (poza cache modelem w pamięci — każdy pod może załadować ten sam `MODEL_PATH`). |
| **Job completion rate** | Więcej replik `c8jw-credit-*` → wyższy throughput jobów; wąskie gardło może być po stronie **jednej** bramki Zeebe lub **Elasticsearch** (Operate), a nie Pythona. |

**100 aktywnych użytkowników** Tasklist: zazwyczaj mały klaster. **1000+**: monitoruj Zeebe metrics, ES heap, Keycloak DB connection pool; rozważ Camunda 8 **SaaS** lub referencyjną topologię self-managed (oddzielne role: gateway, broker, operate).

---

## 2. Keycloak + LDAP / Microsoft Entra (Azure AD)

Typowe warianty:

1. **Entra ID (Azure AD) jako zewnętrzny IdP dla Keycloak** — w Keycloak *Identity Provider* → OIDC (Microsoft). Użytkownicy logują się kontem firmowym; Keycloak mapuje grupy/role do ról Camundy (claimy lub mappery).
2. **LDAP** — jeśli katalog jest klasycznym LDAP (np. **Azure AD Domain Services** eksponuje LDAP): Keycloak *User Federation* → LDAP. Alternatywa: synchronizacja lub brokering zamiast pełnego LDAP, jeśli strategia firmy to wyłącznie OIDC.
3. **Camunda 8 (self-managed)** — dokumentacja Camundy opisuje podłączenie **Operate/Tasklist/Orchestrate** do Keycloak (URLs, clienty, redirecty). W GKE: Ingress TLS + stabilny DNS.

**LDAP „Azure”** w praktyce często znaczy: **Entra ID przez OIDC**, a nie surowy LDAP — prostsze w utrzymaniu.

Ten repozytorium **nie** zawiera Helm chartów Keycloak; użyj oficjalnych chartów / operatora lub managed IdP.

---

## 3. Zewnętrzne bazy SQL (PostgreSQL, itd.)

| Warstwa | Gdzie jest SQL? |
|---------|-----------------|
| **Silnik Zeebe 8** | Stan runtime procesu jest w **logu strumieniowym/partycjach** brokerów — **nie** w „zewnętrznym Postgres dla silnika” w sensie Camundy 7. |
| **Operate / Tasklist / Identity (self-managed)** | Często **Elasticsearch** do indeksów + komponenty mogą używać Postgres dla swojej konfiguracji/użytkowników (zależy od wersji i szablonu Helm). Sprawdź **oficjalny Helm Camunda 8** dla swojej wersji. |
| **Aplikacja banku** | **Tak** — własny Postgres/Azure SQL: dane kredytowe, snapshoty z BIK po stronie backendu, powiązanie `businessKey` ↔ PK wniosku. Worker może wołać HTTP do serwisu, który czyta SQL — albo proces ustawia zmienne przed jobem. |
| **Keycloak** | Własna baza (Postgres) dla realmów i sesji. |

**Wątek „zewnętrzny SQL”** = **domena banku + tożsamość**, a nie zamiennik storage Zeebe.

---

## 4. Gdzie przechowywać wersje modeli ML

| Opcja | Zastosowanie |
|-------|----------------|
| **Object storage wersjonowany** | GCS / S3 z prefiksami `models/credit/v20250330/credit_model.joblib` + metadata (łatwy rollback). |
| **Artifact Registry + obraz Dockera** | Warstwa z `COPY models/…` — wersja = tag obrazu (`credit-worker:1.4.2`). |
| **MLflow Model Registry** | Śledzenie runów, stage „Production”; worker pobiera URI artefaktu przy starcie lub przez initContainer. |
| **Feature Store** (Feast, Vertex, wewnętrzny) | Wersjonowanie **cech**, nie tylko `.joblib`; ważne przy driftcie. |
| **ConfigMap / Secret** | Tylko dla małych metadanych (np. nazwa wersji); cały model raczej nie w Secret. |

W GKE: **initContainer** `gcp storage cp` albo **CSI driver** dla GCS; albo wbudowany model w obrazie dla prostoty (mniej elastycznie).

---

## 5. Data lake i „big data”

| Rola | Typowa technologia |
|------|-------------------|
| **Surowe dane** | Data lake (GCS, ADLS, S3) + format **Delta / Iceberg / Parquet** |
| **Trening ML** | Batch (Spark, BigQuery, Dataflow) → zapisuje zbiory do lake → `training/train.py` lub pipeline CI |
| **Feedback loop** | Wyniki procesów (faktyczny default) trafiają do lake (ETL z systemów banku lub eksport z Camundy przez **Kafka / Zeebe exporter / REST**) — **nie** surowy runtime Zeebe jako „lake”. |
| **Operacyjny insight** | Operate + ES; długoterminowe analityka często **replikuje zdarzenia** do BigQuery/Snowflake |

Architektura: **lake = źródło prawdy do uczenia i raportów**; **Zeebe = orkiestracja runtime**; mostek często **Kafka + kontrakty zdarzeń**.

---

## 6. KEDA (Kubernetes Event-driven Autoscaling)

**KEDA** skaluje `Deployment` / `ScaledObject` w oparciu o **metryki zewnętrzne** (kolejki, lag, Prometheus, HTTP), a nie tylko CPU/RAM jak zwykły HPA.

| Kontekst | Jak się ma do Camundy / workerów |
|----------|-----------------------------------|
| **Workery Zeebe (Python, job polling)** | Sensowne, gdy masz **metrykę „ile pracy czeka”**. Oficjalnego scalera *„Zeebe pending jobs per task type”* w KEDA nie ma z półki — typowo: **Prometheus** (eksport metryk Zeebe / własny sidecar liczący backlog) + **Prometheus scaler** w KEDA, albo **własny external scaler**. |
| **Kafka** | **Bardzo dobry fit**: `kafka` scaler w KEDA — `lagThreshold` na topic, skalujesz konsumentów, którzy potem startują procesy / wołają API. |
| **CPU/RAM** | KEDA może użyć `cpu` / `memory` (jak HPA), ale dla workerów **kolejkowych** lepiej sterować **głębokością kolejki**, nie średnim obciążeniem CPU. |
| **Broker Zeebe / Gateway** | Zazwyczaj **nie** skalujesz agresywnie przez KEDA w locie jak zwykłych podów usługowych — to stateful / klaster; skalowanie wg dokumentacji Camunda (partycje, liczba brokerów). |

**Praktyka:** `ScaledObject` na **Deployment** `credit-score-worker`: źródło = metryka backlogu (np. z Prometheus po Zeebe albo własna heurystyka). **Min replicas** > 0, jeśli potrzebujesz niskiej latencji pierwszego joba; **max replicas** ogranicza koszt GKE.

**GKE:** KEDA instaluje się jako operator w klastrze (Helm); nie zastępuje to **Cluster Autoscaler** na węzłach — KEDA skaluje **pody**, CA — **węzły**, gdy brakuje zasobów.

---

## 7. Krótkie podsumowanie

- **100–1000 użytkowników UI**: Keycloak + Azure — standard; skaluj realm i infrastrukturę IdP.
- **100–1000 równoległych procesów**: partycje Zeebe + **N replik workerów** + monitoring ES/gateway; opcjonalnie **KEDA** na workerach wg metryki kolejki / Kafka lag.
- **SQL zewnętrzny**: dla aplikacji banku i Keycloak; nie jako zamiennik magazynu stanu Zeebe.
- **Wersje modeli**: bucket z wersjonowaniem lub registry ML + spójny `MODEL_PATH` / init w K8s.
- **Data lake**: trening i raporty; integracja z procesem przez batch i zdarzenia, nie przez bezpośredni dostęp workerów do lake w ścieżce real-time scoringu (opcjonalnie wyjątki architektoniczne — rzadko dla scoringu synchronicznego).
