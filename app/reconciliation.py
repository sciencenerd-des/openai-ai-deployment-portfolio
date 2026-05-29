"""Deterministic GSTR-2B ↔ purchase-register reconciliation.

This module is intentionally model-free: GST compliance decisions should be
auditable and replayable. LLM/OCR output can feed these models, but matching,
IMS action selection, and ITC verdicts are owned by deterministic code.
"""

from __future__ import annotations

import re
from datetime import date

from .schemas import (
    Gstr2bLine,
    ImsAction,
    ItcAssessment,
    MatchStatus,
    PurchaseLine,
    ReconMatch,
    ReconReport,
)

MONEY_TOLERANCE = 1.0
BLOCKED_ITC_CATEGORIES = {
    "food",
    "canteen",
    "motor_vehicle",
    "personal_use",
    "club_membership",
    "health_insurance",
}


def normalize_invoice_number(value: str) -> str:
    """Normalize invoice numbers enough for exact GST reconciliation keys."""
    normalized = re.sub(r"[^A-Z0-9]", "", value.upper())
    return normalized.lstrip("0") or "0"


def invoice_period(invoice_date: str) -> str:
    """Return YYYY-MM from an ISO date string."""
    return date.fromisoformat(invoice_date).strftime("%Y-%m")


def total_tax(line: PurchaseLine | Gstr2bLine) -> float:
    return round(line.igst + line.cgst + line.sgst + line.cess, 2)


def total_itc(line: PurchaseLine | Gstr2bLine | None) -> float:
    return total_tax(line) if line is not None else 0.0


def _money_delta(register_line: PurchaseLine, gstr2b_line: Gstr2bLine) -> dict[str, float]:
    return {
        "taxable_value": round(register_line.taxable_value - gstr2b_line.taxable_value, 2),
        "igst": round(register_line.igst - gstr2b_line.igst, 2),
        "cgst": round(register_line.cgst - gstr2b_line.cgst, 2),
        "sgst": round(register_line.sgst - gstr2b_line.sgst, 2),
        "cess": round(register_line.cess - gstr2b_line.cess, 2),
        "total_itc": round(total_itc(register_line) - total_itc(gstr2b_line), 2),
    }


def _max_abs_delta(deltas: dict[str, float]) -> float:
    return max((abs(v) for v in deltas.values()), default=0.0)


def _recon_key(line: PurchaseLine | Gstr2bLine) -> tuple[str, str, str]:
    gstin = line.supplier_gstin if isinstance(line, PurchaseLine) else line.ctin
    return (
        gstin.strip().upper(),
        normalize_invoice_number(line.invoice_number),
        invoice_period(line.invoice_date),
    )


def ims_action_for(status: MatchStatus) -> ImsAction:
    if status in {"matched", "value_mismatch_rounding"}:
        return "accept"
    if status == "in_register_not_2b":
        return "pending"
    if status in {"value_mismatch_material", "in_2b_not_register"}:
        return "reject"
    return "none"


def assess_itc(
    status: MatchStatus,
    register_line: PurchaseLine | None,
    gstr2b_line: Gstr2bLine | None,
    deltas: dict[str, float],
) -> ItcAssessment:
    reasons: list[str] = []
    tax_line = gstr2b_line or register_line

    if register_line and register_line.category:
        category = register_line.category.strip().lower()
        if category in BLOCKED_ITC_CATEGORIES:
            return ItcAssessment(
                eligible=False,
                verdict="block",
                risk=1.0,
                reasons=[f"Section 17(5) blocked category: {category}."],
            )

    if total_itc(tax_line) <= 0:
        return ItcAssessment(
            eligible=False,
            verdict="block",
            risk=1.0,
            reasons=["No GST credit amount is available on this line."],
        )

    if status == "in_register_not_2b":
        return ItcAssessment(
            eligible=False,
            verdict="defer",
            risk=0.75,
            reasons=["Purchase exists in register but is absent from static GSTR-2B."],
        )

    if status == "in_2b_not_register":
        return ItcAssessment(
            eligible=False,
            verdict="block",
            risk=0.65,
            reasons=["Invoice appears in GSTR-2B but is missing from the purchase register."],
        )

    if status == "value_mismatch_material":
        return ItcAssessment(
            eligible=False,
            verdict="block",
            risk=0.9,
            reasons=["Material value mismatch exceeds the rupee tolerance."],
        )

    if status == "value_mismatch_rounding":
        reasons.append("Only rounding-level value deltas are present.")

    if gstr2b_line and gstr2b_line.supplier_filing_date:
        filing_month = invoice_period(gstr2b_line.supplier_filing_date)
        invoice_month = invoice_period(gstr2b_line.invoice_date)
        if filing_month > invoice_month:
            reasons.append("Supplier filed after the invoice month.")
            return ItcAssessment(
                eligible=False,
                verdict="defer",
                risk=0.45,
                reasons=reasons,
            )

    if not reasons:
        reasons.append("Matched in GSTR-2B within tolerance.")
    return ItcAssessment(
        eligible=True,
        verdict="claim",
        risk=min(_max_abs_delta(deltas) / 100.0, 0.2),
        reasons=reasons,
    )


def reconcile(
    *,
    period: str,
    purchase_register: list[PurchaseLine],
    gstr2b: list[Gstr2bLine],
) -> ReconReport:
    """Match purchase-register lines against GSTR-2B lines and score ITC."""
    register_by_key = {_recon_key(line): line for line in purchase_register}
    gstr2b_by_key = {_recon_key(line): line for line in gstr2b}
    all_keys = sorted(set(register_by_key) | set(gstr2b_by_key))

    matches: list[ReconMatch] = []
    for key in all_keys:
        reg = register_by_key.get(key)
        two_b = gstr2b_by_key.get(key)
        deltas: dict[str, float] = {}

        if reg and two_b:
            deltas = _money_delta(reg, two_b)
            max_delta = _max_abs_delta(deltas)
            if max_delta == 0:
                status: MatchStatus = "matched"
            elif max_delta <= MONEY_TOLERANCE:
                status = "value_mismatch_rounding"
            else:
                status = "value_mismatch_material"
        elif reg:
            status = "in_register_not_2b"
        else:
            status = "in_2b_not_register"

        matches.append(
            ReconMatch(
                status=status,
                ims_action=ims_action_for(status),
                register_line=reg,
                gstr2b_line=two_b,
                deltas=deltas,
                itc=assess_itc(status, reg, two_b, deltas),
            )
        )

    summary = _summarize(matches)
    return ReconReport(period=period, matches=matches, summary=summary)


def _summarize(matches: list[ReconMatch]) -> dict[str, float]:
    summary: dict[str, float] = {
        "total": float(len(matches)),
        "claimable_itc": 0.0,
        "deferred_itc": 0.0,
        "blocked_itc": 0.0,
    }
    for match in matches:
        summary[match.status] = summary.get(match.status, 0.0) + 1.0
        amount = total_itc(match.gstr2b_line or match.register_line)
        if match.itc is None:
            continue
        if match.itc.verdict == "claim":
            summary["claimable_itc"] += amount
        elif match.itc.verdict == "defer":
            summary["deferred_itc"] += amount
        else:
            summary["blocked_itc"] += amount

    for key in ("claimable_itc", "deferred_itc", "blocked_itc"):
        summary[key] = round(summary[key], 2)
    return summary


def sample_reconciliation_report() -> ReconReport:
    """Mock-first demo fixture that exercises the main market-research buckets."""
    purchase_register = [
        PurchaseLine(
            supplier_gstin="27AAPFU0939F1ZV",
            invoice_number="INV-2026-0042",
            invoice_date="2026-04-18",
            taxable_value=11740.0,
            cgst=293.5,
            sgst=293.5,
        ),
        PurchaseLine(
            supplier_gstin="29AABCT1332L1ZA",
            invoice_number="KA/88",
            invoice_date="2026-04-20",
            taxable_value=5000.0,
            igst=900.0,
        ),
        PurchaseLine(
            supplier_gstin="07AAACG2115R1ZJ",
            invoice_number="DEL-12",
            invoice_date="2026-04-22",
            taxable_value=10000.0,
            igst=1800.0,
        ),
        PurchaseLine(
            supplier_gstin="33AAAAA0000A1Z9",
            invoice_number="FOOD-7",
            invoice_date="2026-04-24",
            taxable_value=3000.0,
            cgst=270.0,
            sgst=270.0,
            category="food",
        ),
        PurchaseLine(
            supplier_gstin="08AAACH7409R1Z6",
            invoice_number="RJ-19",
            invoice_date="2026-04-26",
            taxable_value=1000.0,
            cgst=90.0,
            sgst=90.0,
        ),
    ]
    gstr2b = [
        Gstr2bLine(
            ctin="27AAPFU0939F1ZV",
            invoice_number="INV/2026/0042",
            invoice_date="2026-04-18",
            taxable_value=11740.0,
            cgst=293.5,
            sgst=293.5,
            supplier_filing_date="2026-04-30",
        ),
        Gstr2bLine(
            ctin="29AABCT1332L1ZA",
            invoice_number="KA-88",
            invoice_date="2026-04-20",
            taxable_value=5000.8,
            igst=900.0,
            supplier_filing_date="2026-04-30",
        ),
        Gstr2bLine(
            ctin="07AAACG2115R1ZJ",
            invoice_number="DEL-12",
            invoice_date="2026-04-22",
            taxable_value=9300.0,
            igst=1674.0,
            supplier_filing_date="2026-05-14",
        ),
        Gstr2bLine(
            ctin="33AAAAA0000A1Z9",
            invoice_number="FOOD-7",
            invoice_date="2026-04-24",
            taxable_value=3000.0,
            cgst=270.0,
            sgst=270.0,
            supplier_filing_date="2026-04-30",
        ),
        Gstr2bLine(
            ctin="24AAACC1206D1ZM",
            invoice_number="GJ-204",
            invoice_date="2026-04-25",
            taxable_value=2200.0,
            igst=396.0,
            supplier_filing_date="2026-04-30",
        ),
    ]
    return reconcile(period="2026-04", purchase_register=purchase_register, gstr2b=gstr2b)
