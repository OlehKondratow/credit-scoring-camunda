# Pola `score_bki` i `bki_request_cnt` — mapowanie techniczne

Dokument dla **zespołu wdrożeniowego**: bez opisu rynku BIG — wyłącznie zgodność nazw w kodzie z modelem i szkoleniem.

## Nazewnictwo w projekcie

Skrót **BKI** w nazwach **`score_bki`**, **`bki_request_cnt`** pochodzi z **zewnętrznego dataseta szkoleniowego** — to **nie** propozycja zmiany nazewnictwa produkcyjnego w integracjach z konkretnym dostawcą danych.

| Zmienna w procesie / modelu | Rola w szkoleniu (uproszczenie) |
|-----------------------------|----------------------------------|
| `score_bki` | Skalar skoringowy w skali zbioru treningowego |
| `bki_request_cnt` | Licznik zapytań w semantyce zbioru treningowego |

**Nie zmieniaj kluczy procesu** (`score_bki`, `bki_request_cnt`) bez **retreningu** i wdrożenia nowej wersji artefaktu `joblib`.

## Wdrożenie produkcyjne

W systemie banku wartości tych pól zwykle ustawia **backend** po pobraniu danych z właściwych źródeł (integracje umowne, katalogi, mapowanie na kontrakt zmiennych procesu). Worker ML liczy wyłącznie na już dostarczonych zmiennych — **nie** zastępuje warstwy źródłowej.

## Dane w repozytorium

- Brak prawdziwych danych z produkcyjnych systemów.
- `data/bik-synthetic-snapshot.example.json` — **fikcyjny** szkielet do mocków i dokumentacji mapowania pól.

## Zastrzeżenie

Przetwarzanie danych z biur informacji gospodarczej podlega ustawodawstwu (m.in. ustawa o BIG, RODO). Ten repozytorium to **szkielet techniczny do szkolenia**, nie analiza prawna ani projekt integracji produkcyjnej.
