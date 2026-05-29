from app.compliance import (
    check_prefile_mismatch,
    draft_vendor_followups,
    expected_irn,
    get_gstin_status,
    triage_notice,
    verify_irn,
)
from app.reconciliation import sample_reconciliation_report
from app.schemas import ExtractedInvoice


def test_mock_gstin_status_detects_cancelled_supplier():
    status = get_gstin_status("33AAAAA0000A1Z9", "South Canteen Services")

    assert status is not None
    assert status.well_formed
    assert status.status == "Cancelled"
    assert status.registered is False
    assert status.name_match is True


def test_mock_gstin_status_detects_name_mismatch():
    status = get_gstin_status("27AAPFU0939F1ZV", "Totally Different Vendor")

    assert status is not None
    assert status.status == "Active"
    assert status.name_match is False


def test_irn_recompute_matches_known_input():
    irn = expected_irn("27AAPFU0939F1ZV", "INV-1", "INV", "2026-27")
    doc = ExtractedInvoice(
        document_type="tax_invoice",
        supplier_gstin="27AAPFU0939F1ZV",
        invoice_number="INV-1",
        invoice_date="2026-04-18",
        irn=irn,
    )

    status = verify_irn(doc)
    assert status is not None
    assert status.irn_matches is True


def test_vendor_followups_are_approval_gated():
    drafts = draft_vendor_followups(sample_reconciliation_report())

    assert len(drafts) == 1
    assert drafts[0].requires_approval is True
    assert drafts[0].severity == "itc_at_risk"
    assert drafts[0].invoice_numbers == ["RJ-19"]


def test_notice_triage_classifies_drc_01c():
    result = triage_notice("DRC-01C issued under Rule 88D for excess ITC", "2026-04")

    assert result.notice_type == "drc_01c"
    assert result.risk == "high"
    assert result.requires_human_review is True
    assert result.citations


def test_prefile_check_flags_rule_88c_risk():
    result = check_prefile_mismatch(
        period="2026-04",
        gstr1_taxable_value=1000000.0,
        gstr1_tax=180000.0,
        gstr3b_taxable_value=900000.0,
        gstr3b_tax=70000.0,
    )

    assert result.rule_88c_risk is True
    assert result.severity == "error"
    assert result.tax_delta == 110000.0
