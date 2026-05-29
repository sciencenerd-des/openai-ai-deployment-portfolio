"""Deterministic validation of extracted documents.

This is the "audit brain" of the system and is intentionally **pure Python** —
no model calls — so it is fast, free, and exhaustively unit-tested. The agent
also exposes ``validate_gstin`` as a tool so it can self-check during extraction.

References:
* GSTIN format: 2-digit state code + 10-char PAN + entity digit + 'Z' + checksum.
* The checksum is a modulo-36 algorithm published by GSTN.
"""

from __future__ import annotations

import re

from .schemas import Anomaly, ExtractedInvoice

GSTIN_CHARSET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
GSTIN_RE = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$")

# Valid GST state codes (UTs and states); 97 is used for "Other Territory".
VALID_STATE_CODES = {f"{i:02d}" for i in range(1, 39)} | {"97"}

# Absolute rupee tolerance for arithmetic checks (rounding on printed invoices).
MONEY_TOLERANCE = 1.0


def gstin_checksum(first14: str) -> str:
    """Return the expected 15th checksum character for a 14-char GSTIN prefix."""
    if len(first14) != 14:
        raise ValueError("GSTIN prefix must be exactly 14 characters")
    factor = 2
    total = 0
    base = len(GSTIN_CHARSET)  # 36
    for ch in reversed(first14.upper()):
        code = GSTIN_CHARSET.index(ch)
        addend = factor * code
        factor = 1 if factor == 2 else 2
        addend = (addend // base) + (addend % base)
        total += addend
    checksum_index = (base - (total % base)) % base
    return GSTIN_CHARSET[checksum_index]


def validate_gstin(gstin: str) -> tuple[bool, str]:
    """Validate a GSTIN. Returns (is_valid, human-readable reason)."""
    if not gstin:
        return False, "empty GSTIN"
    g = gstin.strip().upper()
    if len(g) != 15:
        return False, f"length {len(g)} != 15"
    if not GSTIN_RE.match(g):
        return False, "does not match GSTIN format"
    if g[:2] not in VALID_STATE_CODES:
        return False, f"invalid state code '{g[:2]}'"
    try:
        expected = gstin_checksum(g[:14])
    except ValueError as exc:  # pragma: no cover - guarded by regex above
        return False, str(exc)
    if g[14] != expected:
        return False, f"checksum mismatch (expected '{expected}')"
    return True, "valid"


def _approx(a: float, b: float, tol: float = MONEY_TOLERANCE) -> bool:
    return abs(a - b) <= tol


def validate_document(doc: ExtractedInvoice) -> list[Anomaly]:
    """Run all deterministic checks and return a list of anomalies."""
    anomalies: list[Anomaly] = []

    # --- GSTIN checks ---------------------------------------------------
    for field, value in (("supplier_gstin", doc.supplier_gstin),
                          ("buyer_gstin", doc.buyer_gstin)):
        if value:
            ok, reason = validate_gstin(value)
            if not ok:
                anomalies.append(Anomaly(
                    code="gstin_invalid",
                    severity="error",
                    message=f"{field} '{value}' is invalid: {reason}.",
                    field=field,
                ))

    if doc.document_type == "tax_invoice" and not doc.supplier_gstin:
        anomalies.append(Anomaly(
            code="missing_supplier_gstin",
            severity="error",
            message="Tax invoice has no supplier GSTIN.",
            field="supplier_gstin",
        ))

    # --- line-item arithmetic ------------------------------------------
    for i, item in enumerate(doc.line_items):
        expected = round(item.quantity * item.unit_price, 2)
        if item.amount and not _approx(expected, item.amount):
            anomalies.append(Anomaly(
                code="line_amount_mismatch",
                severity="warning",
                message=(f"Line {i + 1} '{item.description}': "
                         f"{item.quantity} x {item.unit_price} = {expected}, "
                         f"but amount is {item.amount}."),
                field=f"line_items[{i}]",
            ))

    # --- subtotal vs line items ----------------------------------------
    if doc.subtotal is not None and doc.line_items:
        line_sum = round(sum(it.amount for it in doc.line_items), 2)
        if not _approx(line_sum, doc.subtotal):
            anomalies.append(Anomaly(
                code="subtotal_mismatch",
                severity="warning",
                message=f"Line items sum to {line_sum} but subtotal is {doc.subtotal}.",
                field="subtotal",
            ))

    # --- grand total = subtotal + tax ----------------------------------
    if (doc.subtotal is not None and doc.total_tax is not None
            and doc.grand_total is not None):
        expected_total = round(doc.subtotal + doc.total_tax, 2)
        if not _approx(expected_total, doc.grand_total):
            anomalies.append(Anomaly(
                code="grand_total_mismatch",
                severity="error",
                message=(f"subtotal {doc.subtotal} + tax {doc.total_tax} = "
                         f"{expected_total}, but grand total is {doc.grand_total}."),
                field="grand_total",
            ))

    # --- CGST/SGST symmetry for intra-state supply ----------------------
    tb = doc.tax_breakup
    if tb is not None:
        if (tb.cgst or tb.sgst) and tb.igst:
            anomalies.append(Anomaly(
                code="mixed_tax_heads",
                severity="error",
                message="Both IGST and CGST/SGST present; a supply is either inter- or intra-state.",
                field="tax_breakup",
            ))
        if (tb.cgst or tb.sgst) and not _approx(tb.cgst, tb.sgst):
            anomalies.append(Anomaly(
                code="cgst_sgst_asymmetry",
                severity="warning",
                message=f"CGST {tb.cgst} != SGST {tb.sgst} (they must be equal).",
                field="tax_breakup",
            ))

    return anomalies


def score_confidence(anomalies: list[Anomaly]) -> float:
    """Map anomalies to a 0..1 confidence score."""
    penalty = 0.0
    weights = {"error": 0.34, "warning": 0.12, "info": 0.02}
    for a in anomalies:
        penalty += weights.get(a.severity, 0.1)
    return max(0.0, round(1.0 - penalty, 3))
