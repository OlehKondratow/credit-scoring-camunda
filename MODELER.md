# Camunda Modeler — pakiet C8CS

## Pliki do otwarcia / wdrożenia

| Kolejność | Plik | Opis |
|-----------|------|------|
| 1 | `forms/c8cs_applicant_input.form` | Formularz startowy — pola zgodne ze zmiennymi ML |
| 2 | `forms/c8cs_decision_output.form` | Formularz wyniku (read-only) |
| 3 | `dmn/c8cs-post-ml-policy.dmn` | Decyzja `c8cs_credit_policy` → zmienna `creditPolicyDecision` |
| 4 | `bpmn/c8cs-full-modeler.bpmn` | Proces `c8cs_full_orchestration` |

W **Operate** można wdrażać w tej kolejności (lub zaznaczyć wszystkie cztery typy zasobów jednym deployem, jeśli narzędzie to obsługuje). Przy DMN w procesie użyto **`bindingType="latest"`** — wtedy DMN może być opublikowany przed BPMN.

## Proces `c8cs_full_orchestration`

1. **User task** — formularz `c8cs_applicant_input`
2. **Service task** — `c8jw-credit-validate`
3. **Brama** — `creditInputValid`; gałąź „nie” → user task z wynikiem (tylko błąd walidacji) → koniec
4. **Service task** — `c8jw-credit-score`
5. **Business rule task** — DMN `c8cs_credit_policy`
6. **User task** — formularz `c8cs_decision_output` → koniec

## Worker przed testem

Uruchom workery ML (bez `c8jw-credit-route`, bo routing jest w DMN):

```bash
export WORKERS=c8jw-credit-validate,c8jw-credit-score
export ZEEBE_ADDRESS=127.0.0.1:26500
python -m worker.run_worker
```

Wymagany plik modelu: `models/credit_model.joblib` (`python training/train.py --demo`).

Pełna lista typów jobów: **`WORKERS.md`**.
