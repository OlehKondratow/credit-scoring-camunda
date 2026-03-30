# BIK a pola w tym projekcie

## Czym jest BIK w Polsce?

**BIK** (*Biuro Informacji Kredytowej*) to działające w Polsce **biuro informacji gospodarczej**, które przetwarza m.in. dane o zobowiązaniach i historii kredytowej (w uproszczeniu: „raport kredytowy” / zapytania do bazy informacji kredytowej).

To **nie jest** to samo co skrót **BKI** użyty w nazwach pól importowanych z zestawu szkoleniowego (`score_bki`, `bki_request_cnt`) — tam chodzi o nazewnictwo z **zewnętrznego dataseta**, a nie o oficjalną skrótową formę „BIK”.

## Mapowanie pól modelu → sens „jak z biura”

W procesie i w modelu ML używane są zmienne odczytywane **z wniosku / systemów banku**, które w realnym wdrożeniu mogłyby pochodzić z **integracji z raportem lub scoringiem od BIK** (po stronie backendu), a nie od ręcznego wpisania przez klienta w całości.

| Zmienna w projekcie | Sens biznesowy (uproszczony) | Uwaga |
|---------------------|------------------------------|--------|
| `score_bki` | Jednowymiarowy scoring „z biura” z dataseta | W produkcji zastąpiłby go np. konkretny wskaźnik z dostawcy danych (format zależy od umowy i API). |
| `bki_request_cnt` | Liczba zapytań / wpisów w oś czasu zapytań (w dataset: liczba) | Semantyka zbliżona do „ile razy w historii pojawiały się zapytania” — tylko w tym projekcie to **kolumna treningowa**, nie live BIK. |

**Pola `score_bki` i `bki_request_cnt` muszą pozostać pod tymi nazwami** w kodzie i formularzu powiązanym z BPMN, żeby nie re-trenować modelu po samej zmianie etykiet.

## Dane w repozytorium

- **Nie udostępniamy** prawdziwych danych z BIK ani nie symulujemy **oficjalnego** API BIK.
- Plik `data/bik-synthetic-snapshot.example.json` to **fikcyjny przykład** struktury, jaką *mógłby* zwrócić wewnętrzny serwis po pobraniu informacji z biura (do dokumentacji i mocków).
- Trening modelu nadal opiera się na `train.csv` / `--demo` zgodnie z `README.md`.

## Aplikacja wewnątrz banku

Jeśli proces działa **w infrastrukturze banku** (własna aplikacja kredytowa, istniejące umowy z BIK lub innym BIG, procedury zgód, DPIA, kontrolki dostępu), **przekazanie do Camundy zmiennych pochodzących z biura** — normalny wzorzec: backend pobiera raport / scoring, mapuje je na zmienne procesu (`score_bki`, `bki_request_cnt` lub przyszłe pola po retreningu), worker tylko liczy model na już „bankowych” danych.

Ten projekt szkoleniowy **nie zastępuje** integracji ani compliance po stronie banku; chodzi wyłącznie o to, że **sam fakt orkiestracji wewnątrz banku** nie jest przeszkodą — o ile respektowane są umowy i polityki instytucji.

## Zgodność prawna (skrót)

Przetwarzanie danych z biur informacji gospodarczej (w tym BIK) podlega **ustawie o biurach informacji gospodarczej** oraz RODO. Wdrożenie produkcyjne wymaga podstawy prawnej, umów z BIK jako dostawcą danych i polityk bezpieczeństwa. Repozytorium to nie porada prawna — opisuje jedynie **szkoleniowy** szkielet techniczny.
