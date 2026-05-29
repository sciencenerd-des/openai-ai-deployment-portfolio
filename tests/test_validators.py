from app.schemas import ExtractedInvoice, LineItem, TaxBreakup
from app.validators import (
    gstin_checksum,
    score_confidence,
    validate_document,
    validate_gstin,
)


def _valid_gstin(prefix14: str) -> str:
    """Build a checksum-valid GSTIN from a 14-char prefix (self-consistent)."""
    return prefix14 + gstin_checksum(prefix14)


def test_gstin_roundtrip_is_valid():
    g = _valid_gstin("27AAPFU0939F1Z")
    assert g == "27AAPFU0939F1ZV"
    ok, reason = validate_gstin(g)
    assert ok, reason


def test_gstin_bad_checksum_rejected():
    g = "27AAPFU0939F1Z" + "A"  # wrong final char
    ok, _ = validate_gstin(g)
    assert not ok


def test_gstin_bad_length_and_state():
    assert not validate_gstin("123")[0]
    assert not validate_gstin("99AAPFU0939F1ZV")[0]  # state code 99 invalid


def test_clean_invoice_has_no_anomalies():
    doc = ExtractedInvoice(
        document_type="tax_invoice",
        supplier_gstin=_valid_gstin("27AAPFU0939F1Z"),
        line_items=[LineItem(description="X", quantity=2, unit_price=50.0, amount=100.0)],
        subtotal=100.0, total_tax=10.0, grand_total=110.0,
        tax_breakup=TaxBreakup(taxable_value=100.0, cgst=5.0, sgst=5.0),
    )
    assert validate_document(doc) == []


def test_line_and_subtotal_mismatch_detected():
    doc = ExtractedInvoice(
        document_type="receipt",
        line_items=[LineItem(description="X", quantity=2, unit_price=299.0, amount=698.0)],
        subtotal=598.0, total_tax=0.0, grand_total=598.0,
    )
    codes = {a.code for a in validate_document(doc)}
    assert "line_amount_mismatch" in codes
    assert "subtotal_mismatch" in codes


def test_grand_total_mismatch_is_error():
    doc = ExtractedInvoice(
        document_type="tax_invoice",
        supplier_gstin=_valid_gstin("29AABCT1332L1Z"),
        line_items=[LineItem(description="S", quantity=1, unit_price=1000.0, amount=1000.0)],
        subtotal=1000.0, total_tax=180.0, grand_total=1200.0,
        tax_breakup=TaxBreakup(taxable_value=1000.0, igst=180.0),
    )
    errs = [a for a in validate_document(doc) if a.code == "grand_total_mismatch"]
    assert errs and errs[0].severity == "error"


def test_mixed_tax_heads_detected():
    doc = ExtractedInvoice(
        document_type="tax_invoice",
        supplier_gstin=_valid_gstin("07AAACG2115R1Z"),
        line_items=[LineItem(description="G", quantity=1, unit_price=1000.0, amount=1000.0)],
        subtotal=1000.0, total_tax=180.0, grand_total=1180.0,
        tax_breakup=TaxBreakup(taxable_value=1000.0, cgst=90.0, sgst=90.0, igst=180.0),
    )
    assert "mixed_tax_heads" in {a.code for a in validate_document(doc)}


def test_confidence_decreases_with_severity():
    clean = score_confidence([])
    assert clean == 1.0
    from app.schemas import Anomaly
    noisy = score_confidence([Anomaly(code="x", severity="error", message="m")])
    assert noisy < clean
