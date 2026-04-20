"""PII masking — regression tests (checklist in doc/prompt.md §6)."""

from app.services.pii import mask_application_payload, mask_free_text, mask_pesel


def test_mask_pesel_in_string() -> None:
    assert mask_pesel("ID 91010112345 end") == "ID [PESEL] end"


def test_mask_application_payload_pesel_key() -> None:
    out = mask_application_payload({"pesel": "91010112345", "income": 5000})
    assert out["pesel"] == "[PESEL]"
    assert out["income"] == 5000


def test_mask_free_text_combined() -> None:
    t = mask_free_text("PESEL 91010112345 ul. Test 00-001 Warszawa")
    assert "[PESEL]" in t
    assert "91010112345" not in t
