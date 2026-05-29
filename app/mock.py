"""Deterministic fixtures for mock mode.

A tiny rule-based "extractor" that keys off substrings in the supplied text so
the whole pipeline behaves believably offline. It is intentionally NOT a model —
it just returns canned structured output so the UI, tests and evals are reproducible.
"""

from __future__ import annotations

from .schemas import ExtractedInvoice, LineItem, TaxBreakup

# A clean, internally-consistent intra-state tax invoice.
_CLEAN = ExtractedInvoice(
    document_type="tax_invoice",
    invoice_number="INV-2024-0042",
    invoice_date="2024-11-18",
    supplier_name="Saraswati Traders",
    supplier_gstin="27AAPFU0939F1ZV",
    buyer_name="Bharat Kirana Store",
    buyer_gstin="27AACCM1234C1Z2",
    place_of_supply="Maharashtra (27)",
    currency="INR",
    line_items=[
        LineItem(description="Basmati Rice 25kg", hsn_sac="1006", quantity=4,
                 unit_price=1450.0, amount=5800.0),
        LineItem(description="Sunflower Oil 15L", hsn_sac="1512", quantity=3,
                 unit_price=1980.0, amount=5940.0),
    ],
    subtotal=11740.0,
    total_tax=587.0,
    grand_total=12327.0,
    tax_breakup=TaxBreakup(taxable_value=11740.0, cgst=293.5, sgst=293.5, igst=0.0),
    detected_language="en",
    notes="Mock extraction (no API key configured).",
)

# A receipt whose totals do not add up and whose GSTIN checksum is wrong —
# exercises the anomaly detector.
_DIRTY = ExtractedInvoice(
    document_type="tax_invoice",
    invoice_number="9921",
    invoice_date="2024-12-02",
    supplier_name="Krishna Mobile House",
    supplier_gstin="29AAAAA0000A1Z9",  # bad checksum
    buyer_name=None,
    place_of_supply="Karnataka (29)",
    currency="INR",
    line_items=[
        LineItem(description="USB-C Cable", hsn_sac="8544", quantity=2,
                 unit_price=299.0, amount=698.0),  # 2*299=598, not 698
    ],
    subtotal=598.0,
    total_tax=107.64,
    grand_total=820.0,  # 598+107.64 != 820
    tax_breakup=TaxBreakup(taxable_value=598.0, cgst=53.82, sgst=53.82, igst=20.0),
    detected_language="en",
    notes="Mock extraction (no API key configured).",
)


def mock_extract(text: str | None) -> ExtractedInvoice:
    """Pick a fixture based on a hint in the text; default to the clean invoice."""
    hint = (text or "").lower()
    if "dirty" in hint or "anomaly" in hint or "error" in hint:
        return _DIRTY.model_copy(deep=True)
    return _CLEAN.model_copy(deep=True)
