# Specyfikacja: bankowy portal webowy (własny UI) + Camunda 8

**Wersja dokumentu:** 1.0  
**Status:** szablon do dopasowania w organizacji  
**Powiązane materiały:** [camunda-external-web.md](camunda-external-web.md), [ARCHITECTURE.md](../ARCHITECTURE.md)

---

## 1. Cel i zakres

### 1.1. Cel

Opracować **własny portal webowy** (frontend + backend pod przeglądarkę), który umożliwia użytkownikom końcowym banku (klientom i/lub pracownikom front office) obsługę **wniosków kredytowych i powiązanych zadań użytkownika**, orkiestrowanych przez **Camunda 8 (Zeebe)**, bez konieczności traktowania UI **Tasklist** jako głównego interfejsu.

Wygląd, branding i UX **w całości definiuje bank**.

### 1.2. Granice systemu (scope)

| W zakresie | Poza zakresem (out of scope) |
|------------|------------------------------|
| SPA (zalecane **React** lub **Vue**), responsywny layout | Zastąpienie **Operate** pełnym monitorem administracyjnym wszystkich procesów (opcjonalnie osobny epik) |
| **BFF** (Backend-for-Frontend) — jeden punkt wejścia API dla przeglądarki | Implementacja **Identity / Keycloak** od zera (wykorzystywany jest istniejący IdP) |
| Wywołania do Camunda 8 przez BFF (REST/gRPC wg uzgodnionej architektury) | Self-host **Zeebe** i wartości Helm (odpowiedzialność platformy) |
| Scenariusze: start procesu, odpytanie o stan, prezentacja i wysyłka **user task** (formularze), prezentacja wyników ML/DMN (read-only) | Trening modeli ML (osobny potok) |

---

## 2. Role i aktorzy

| Rola | Opis |
|------|------|
| **Klient banku** | Składa wniosek, wypełnia ankietę, widzi status/decyzję w ramach polityki banku |
| **Pracownik (opcjonalnie)** | Realizuje zadania z procesu w tym samym lub osobnym dziale portalu |
| **System Camunda 8** | Jedno źródło prawdy dla procesu i zadań |
| **BFF** | Agreguje wywołania do Camundy i do wewnętrznych API banku (źródła informacji kredytowej, profil klienta itd.) |

---

## 3. Architektura (logiczna)

```
[Przeglądarka] --(HTTPS + cookies/JWT)--> [BFF] --(mTLS/sieć wewn.)-->
    |                                      |--> Zeebe Gateway (gRPC) / Zeebe REST (jeśli dostępny)
    |                                      |--> Tasklist REST/GraphQL (jeśli używany)
    |                                      |--> Wewnętrzne API banku (SQL, biura/źródła informacji kredytowej, słowniki)
    +--> statyczne zasoby SPA (CDN / Ingress)
```

**Wymaganie:** przeglądarka **nie** wywołuje wprost Zeebe gRPC i **nie** przechowuje poświadczeń serwisowych Camundy. Sekrety wyłącznie po stronie BFF (Kubernetes Secret, Vault, Workload Identity).

---

## 4. Wymagania funkcjonalne

### 4.1. Uwierzytelnianie i sesja

- Logowanie użytkownika przez **firmowy IdP** banku (zalecane **OIDC**, np. Azure AD / Keycloak).
- BFF wymienia kod autoryzacji na tokeny, ustawia sesję **httpOnly, secure** albo przekazuje **krótkożyciowy JWT** w nagłówku (decyzja w projekcie bezpieczeństwa).
- Mapowanie **subject IdP** ↔ **Camunda user id** / grupy (jeśli potrzebne do przypisania user task) — konfiguracja lub serwis katalogowy.

### 4.2. Start procesu biznesowego

- Użytkownik inicjuje proces (np. „wniosek kredytowy”): `processId` / `bpmnProcessId` zgodnie z wdrożonym BPMN.
- BFF wywołuje API startu procesu z **zmiennymi procesu** zgodnymi z kontraktem (por. `c8cs_applicant_input` / zmienne w BPMN).
- W odpowiedzi UI otrzymuje **klucz procesu** / `processInstanceKey` do odpytywania o status.

### 4.3. User tasks (zadania dla człowieka)

- Lista w **otwarte zadania** bieżącego użytkownika (filtry: proces, data).
- Karta zadania: tytuł, termin, **dane formularza** (schemat z Camunda Form JSON lub uproszczony kontrakt pól, uzgodniony z bankiem).
- Akcje: **complete** z treścią zmiennych; przy błędzie walidacji — komunikat dla użytkownika bez psucia stanu procesu.

*Uwaga:* implementacja może opierać się na **Tasklist API** lub własnych wrapperach wokół Zeebe — wybór na etapie projektu wg wersji Camunda 8 i licencjonowania.

### 4.4. Prezentacja wyników

- Po krokach ML/DMN UI pokazuje pola **read-only**: prawdopodobieństwo defaultu, flagi polityki, tekst decyzji (zmienne procesu wg kontraktu).
- Źródło danych: BFF odczytuje zmienne instancji procesu lub osobny „ekran stanu” wg `processInstanceKey`.

### 4.5. Błędy i niedostępność

- Degradacja: zrozumiałe komunikaty przy timeoutach BFF/Camunda.
- Idempotentność ponownego wysłania formularza (gdzie ma zastosowanie) — do uzgodnienia.

---

## 5. Wymagania niefunkcjonalne

### 5.1. Bezpieczeństwo

- **TLS 1.2+** na zewnętrznym obwodzie; HSTS przy publicznej domenie.
- OWASP ASVS / standardy wewnętrzne banku dla XSS, CSRF (przy sesji cookie), injection.
- Logi bez danych osobowych w rozumieniu wymogów audytu i bez sekretów; maskowanie pól w UI przy audycie.
- Dostęp BFF do Camundy tylko z **zaufanej sieci** (GKE, Private Service Connect itp.).

### 5.2. Wydajność

- Docelowy czas odpowiedzi typowych ekranów (np. p95 &lt; 2 s przy nominalnym obciążeniu) — doprecyzowanie u zamawiającego.
- Cache słowników na BFF w razie potrzeby.

### 5.3. Dostępność i eksploatacja

- Endpointy health BFF dla Kubernetes **liveness/readiness**.
- Wersjonowanie API BFF (`/v1/...`).
- Zgodność z politykami retencji logów i śledzenia (OpenTelemetry — opcjonalnie).

---

## 6. Integracja z Camunda 8 (założenia techniczne)

| Zadanie | Kierunek implementacji (wybrać jeden na etapie projektu) |
|---------|------------------------------------------------------------|
| Start procesu | Klient Zeebe z BFF (gRPC) lub wspierana warstwa **REST** Camundy 8 dla deploy/start (zweryfikować względem wersji platformy) |
| User task list / complete | **Tasklist REST/GraphQL** z tokenem serwisu / użytkownika (model autoryzacji Camunda Identity) |
| Odczyt zmiennych | API Operate/Tasklist lub Zeebe — wg możliwości wersji i polityki bezpieczeństwa |

**Obowiązkowo:** ustalić wersję **Camunda 8.x** i oprzeć się na oficjalnej dokumentacji API dla tej wersji.

---

## 7. UI/UX (wysoki poziom)

- Design system banku (typografia, kolory, komponenty).
- Szerokość mobilna ≥ 360 px (docelowe breakpointy — w makietach).
- Dostępność: docelowy poziom **WCAG 2.1 AA** (doprecyzowanie u zamawiającego).
- Lokalizacja: **PL/EN** (ew. inne) — zestaw języków ustala zamawiający.

Szczegółowe makety — osobny załącznik do specyfikacji (Figma itd.).

---

## 8. Dostawa i kryteria akceptacji

### 8.1. Artefakty

- Kod źródłowy SPA i BFF w repozytorium zamawiającego.
- Obrazy **Docker**, **Helm chart** lub manifesty **Kubernetes** pod wdrożenie.
- Dokumentacja: README, opis zmiennych środowiska, schemat przepływu OAuth, kontrakty API BFF (OpenAPI).

### 8.2. Kryteria akceptacji (przykład)

1. Użytkownik przechodzi uwierzytelnianie i widzi ekran startu wniosku.
2. Poprawny start procesu Camunda z prawidłowym zestawem zmiennych; instancja widoczna w Operate (kontrola).
3. Wykonanie user task przez portal z poprawnym **complete** i aktualizacją zmiennych.
4. Wyświetlenie pól końcowych po ML/DMN zgodnie z BPMN tego repozytorium lub dołączonym kontraktem.
5. Przejście **SAST/DAST** i kontroli bezpieczeństwa wg regulaminu banku (jeśli ma zastosowanie).

---

## 9. Ryzyka i zależności

- Zmiany API między wersjami minor Camundy 8.
- Model uprawnień: spójność ról IdP i przypisań user task w BPMN.
- Obciążenie: przy wysokim równoległym obciążeniu — skalowanie BFF i limity Zeebe.

---

## 10. Załączniki (do uzupełnienia przez zamawiającego)

- Lista **processId** i środowisk (dev/stage/prod).
- Link do **OpenAPI** BFF.
- Macierz ról i dozwolonych akcji.
- Schemat przepływów danych i DPIA.
