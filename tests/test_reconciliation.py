from app.reconciliation import normalize_invoice_number, reconcile, sample_reconciliation_report
from app.schemas import Gstr2bLine, PurchaseLine


def test_normalize_invoice_number_handles_common_format_drift():
    assert normalize_invoice_number("INV/2026/0042") == normalize_invoice_number("inv-2026-0042")
    assert normalize_invoice_number("0007") == "7"


def test_reconcile_classifies_core_match_buckets_and_itc_totals():
    report = sample_reconciliation_report()
    statuses = {match.status for match in report.matches}

    assert statuses == {
        "matched",
        "value_mismatch_rounding",
        "value_mismatch_material",
        "in_register_not_2b",
        "in_2b_not_register",
    }
    assert report.summary["claimable_itc"] == 1487.0
    assert report.summary["deferred_itc"] == 180.0
    assert report.summary["blocked_itc"] == 2610.0


def test_in_register_not_2b_defers_itc_and_sets_pending_ims_action():
    report = reconcile(
        period="2026-04",
        purchase_register=[
            PurchaseLine(
                supplier_gstin="27AAPFU0939F1ZV",
                invoice_number="MISSING-2B",
                invoice_date="2026-04-18",
                taxable_value=1000.0,
                cgst=90.0,
                sgst=90.0,
            )
        ],
        gstr2b=[],
    )

    match = report.matches[0]
    assert match.status == "in_register_not_2b"
    assert match.ims_action == "pending"
    assert match.itc is not None
    assert match.itc.verdict == "defer"
    assert report.summary["deferred_itc"] == 180.0


def test_material_mismatch_blocks_itc_and_rejects_ims_action():
    report = reconcile(
        period="2026-04",
        purchase_register=[
            PurchaseLine(
                supplier_gstin="27AAPFU0939F1ZV",
                invoice_number="INV-1",
                invoice_date="2026-04-18",
                taxable_value=1000.0,
                cgst=90.0,
                sgst=90.0,
            )
        ],
        gstr2b=[
            Gstr2bLine(
                ctin="27AAPFU0939F1ZV",
                invoice_number="INV/1",
                invoice_date="2026-04-18",
                taxable_value=900.0,
                cgst=81.0,
                sgst=81.0,
            )
        ],
    )

    match = report.matches[0]
    assert match.status == "value_mismatch_material"
    assert match.ims_action == "reject"
    assert match.itc is not None
    assert match.itc.verdict == "block"
