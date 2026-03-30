# Camunda 8 — aplikacje web, dostęp zewnętrzny (Ingress, API Gateway)

Ściąga GKE (port-forward, serwisy) w repozytorium szkoleniowym: **[gke-camunda-cheatsheet.md](https://github.com/OlehKondratow/camunda8-tutorial/blob/main/docs/gke-camunda-cheatsheet.md)**.

---

## 1. Jakie są „web appy” Camundy 8?

W **self-managed** (Helm **Camunda Platform**) typowo uruchamiane są **osobne** aplikacje SPA / backend (nie jeden monolitowy „Camunda Console” jak w C7):

| Komponent | Rola dla użytkownika | Typowy port (wewn. klastra / lokalnie) |
|-----------|----------------------|----------------------------------------|
| **Tasklist** | Lista zadań użytkownika, **formularze** powiązane z user taskami | np. 8082 (port-forward w ściądze) |
| **Operate** | Monitoring **instancji procesów**, incydenty, anulowanie | np. 8081 |
| **Identity** | Logowanie SSO, użytkownicy — często przekierowania do **Keycloak** | osobny serwis |
| **Optimize** | (Opcja) analityka procesów | osobny serwis |
| **Camunda Modeler** | **Aplikacja desktop** (Electron) — **nie** jest serwowana z klastra jako główny UI produkcyjny | — |

**Zeebe Gateway** (`:26500`) to **gRPC** dla workerów i klientów — **nie** jest to przeglądarkowy „portal”; do przeglądarki trafiają **Tasklist / Operate** przez HTTP(S).

---

## 2. Dostęp zewnętrzny — Ingress (GKE)

**Cel:** użytkownik z Internetu lub VPN ładuje `https://tasklist.bank.example`, `https://operate.bank.example`.

1. **Ingress controller** w klastrze (np. **GKE Ingress** = Google Cloud Load Balancer, lub **nginx-ingress**, **Traefik**).
2. Zasób **`Ingress`** (lub **Gateway API**) mapuje **host + ścieżkę** → **Service** `ClusterIP` Camundy, np.:
   - `tasklist.bank.internal` → `camunda-platform-tasklist:8080` (nazwa zależy od wersji chartu Helm),
   - `operate.bank.internal` → `camunda-platform-operate:8080`.
3. **TLS:** **ManagedCertificate** (GKE) lub cert z **cert-manager** (Let’s Encrypt); Ingress wymusza HTTPS.
4. **DNS:** rekordy A/AAAA lub CNAME na adres **Load Balancera** z Ingress.

**Bezpieczeństwo:** Tasklist/Operate **nie** wystawiaj publicznie bez **Keycloak (OIDC)** i polityk sieciowych; często dostęp tylko z **corp VPN** lub **Identity-Aware Proxy (IAP)** w GCP.

Szczegóły nazw `Service` sprawdź: `kubectl get svc -n <namespace>` po `helm install`.

---

## 3. API Gateway a Camunda

Pojęcia rozdzielamy:

| Warstwa | Protokół / przeznaczenie |
|---------|---------------------------|
| **Zeebe Gateway** | **gRPC** (`ZEEBE_ADDRESS=host:26500`) — workery, Deploy diagramów z Modelera, część operacji programistycznych |
| **Tasklist REST API / GraphQL** | HTTP — **własna aplikacja** (bankowy portal) może tworzyć zadania / kompletować user task zamiast Tasklist UI; adres = zwykle ten sam backend Tasklist za Ingress lub dedykowany routing |
| **Operate API** | HTTP — automatyzacja podglądu (ograniczenia wg wersji/licencji) |
| **„API Gateway” (Kong, Apigee, Envoy)** | **Przed** Ingress: uwierzytelnianie klienta zewnętrznego (API key, JWT), rate limit, routing do mikrousług banku; do Camundy często tylko **wewnętrzny** ruch lub **BFF** banku woła Tasklist/Zeebe z sieci klastra |

**Schemat:**  
`Internet → (opcjonalnie) Cloud Load Balancer / API Gateway → Ingress → Tasklist|Operate|Keycloak`  
Workery w GKE łączą się **wewnętrznie**: `camunda-platform-zeebe-gateway.camunda.svc:26500` — **bez** wystawiania gRPC na świat (lub z **mTLS** jeśli architektura wymaga).

---

## 4. Zewnętrzni użytkownicy (nie tylko IT)

1. **Użytkownik końcowy banku** — zwykle **aplikacja banku** (web/mobile) → backend banku → **Start process** / **Complete task** (REST Zeebe, Connectors, lub Tasklist API) — **bez** bezpośredniego logowania do Operate.
2. **Analityk / operator procesu** — **Operate** + SSO (Keycloak + Azure AD).
3. **Pracownik back-office** — **Tasklist** + formularze Camundy 8.

Konfiguracja **Identity** + **Keycloak**: realms, clienty, redirect URI **dokładnie** jak w dokumentacji wersji Camundy (localhost vs publiczny URL Ingress).

---

## 5. Jak „to wygląda” w praktyce

- **Tasklist / Operate:** nowoczesny interfejs (lista filtrów, widok BPMN w Operate, formularze w Tasklist); wygląd zależy od wersji **8.x** i motywu — nie jest to „stary” Cockpit z C7.
- **Własny portal:** budujesz osobno (React/Vue) i wołasz API — **wygląd w 100% pod bank**.

Ten folder **credit-scoring-camunda** nie zawiera Szablonu Ingress ani Helm values — użyj oficjalnych **values** Camunda Platform i dodaj Ingress u operatora platformy lub osobnym manifeście.

**Własny portal (SPA + BFF)** — szablon TZ (RU): **[tz-bank-portal-camunda.md](tz-bank-portal-camunda.md)**.
