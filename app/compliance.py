"""Mock-first compliance services from the market research backlog."""

from __future__ import annotations

import hashlib
import re
from difflib import SequenceMatcher
from typing import Protocol

from .schemas import (
    DraftEmail,
    ExtractedInvoice,
    GstinStatus,
    IrnStatus,
    NoticeTriageResult,
    PrefileCheckResult,
    ReconReport,
)
from .validators import validate_gstin

MOCK_GSTIN_REGISTRY = {
    "27AAPFU0939F1ZV": {
        "status": "Active",
        "legal_name": "Saraswati Traders",
        "trade_name": "Saraswati Traders",
        "registration_date": "2017-07-01",
    },
    "29AABCT1332L1ZA": {
        "status": "Active",
        "legal_name": "Krishna Mobile House",
        "trade_name": "Krishna Mobile",
        "registration_date": "2018-04-12",
    },
    "07AAACG2115R1ZJ": {
        "status": "Active",
        "legal_name": "Delhi Industrial Supply Co",
        "trade_name": "DIS Co",
        "registration_date": "2017-08-03",
    },
    "33AAAAA0000A1Z9": {
        "status": "Cancelled",
        "legal_name": "South Canteen Services",
        "trade_name": "South Canteen",
        "registration_date": "2019-01-10",
        "cancellation_date": "2025-11-30",
    },
}


class GstnClient(Protocol):
    """Small provider boundary for future GSP/GSTN adapters."""

    def get_gstin(self, gstin: str) -> dict[str, str] | None:
        ...


class MockGstnClient:
    def get_gstin(self, gstin: str) -> dict[str, str] | None:
        return MOCK_GSTIN_REGISTRY.get(gstin.strip().upper())


def _token_ratio(left: str | None, right: str | None) -> float:
    if not left or not right:
        return 0.0
    normalize = lambda s: " ".join(sorted(re.findall(r"[a-z0-9]+", s.lower())))
    return SequenceMatcher(None, normalize(left), normalize(right)).ratio()


def get_gstin_status(
    gstin: str | None,
    printed_legal_name: str | None = None,
    client: GstnClient | None = None,
) -> GstinStatus | None:
    if not gstin:
        return None
    normalized = gstin.strip().upper()
    well_formed, _ = validate_gstin(normalized)
    if not well_formed:
        return GstinStatus(
            gstin=normalized,
            well_formed=False,
            registered=False,
            status=None,
            source="mock",
        )

    record = (client or MockGstnClient()).get_gstin(normalized)
    if record is None:
        return GstinStatus(
            gstin=normalized,
            well_formed=True,
            registered=False,
            status="Unverified",
            name_match=None,
            source="mock",
        )

    legal_name = record.get("legal_name")
    return GstinStatus(
        gstin=normalized,
        well_formed=True,
        registered=record["status"] == "Active",
        status=record["status"],
        legal_name=legal_name,
        trade_name=record.get("trade_name"),
        registration_date=record.get("registration_date"),
        cancellation_date=record.get("cancellation_date"),
        name_match=_token_ratio(printed_legal_name, legal_name) >= 0.8 if printed_legal_name else None,
        source="mock",
    )


def expected_irn(gstin: str, doc_no: str, doc_type: str, financial_year: str) -> str:
    payload = f"{gstin.strip().upper()}{doc_no.strip().upper()}{doc_type.strip().upper()}{financial_year}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def financial_year_from_iso(invoice_date: str | None) -> str | None:
    if not invoice_date:
        return None
    year = int(invoice_date[:4])
    month = int(invoice_date[5:7])
    start = year if month >= 4 else year - 1
    return f"{start}-{str(start + 1)[-2:]}"


def verify_irn(doc: ExtractedInvoice) -> IrnStatus | None:
    if not (doc.supplier_gstin and doc.invoice_number and doc.invoice_date):
        return None
    doc_type = (doc.document_subtype or "INV").upper()
    financial_year = financial_year_from_iso(doc.invoice_date)
    if not financial_year:
        return None
    recomputed = expected_irn(doc.supplier_gstin, doc.invoice_number, doc_type, financial_year)
    return IrnStatus(
        irn=doc.irn,
        recomputed_irn=recomputed,
        irn_matches=(doc.irn.lower() == recomputed) if doc.irn else None,
        qr_signature_valid=None,
        irp_status=None,
        source="offline",
    )


def draft_vendor_followups(report: ReconReport) -> list[DraftEmail]:
    drafts: list[DraftEmail] = []
    for match in report.matches:
        if match.status != "in_register_not_2b" or match.register_line is None:
            continue
        line = match.register_line
        drafts.append(
            DraftEmail(
                supplier_gstin=line.supplier_gstin,
                subject=f"Action required: invoice {line.invoice_number} missing from GSTR-2B",
                body=(
                    "Please upload or amend this invoice in your GSTR-1/IMS records so our "
                    f"ITC can reflect in GSTR-2B for {report.period}. Invoice "
                    f"{line.invoice_number} dated {line.invoice_date} is currently present "
                    "in our purchase register but absent from GSTR-2B."
                ),
                severity="itc_at_risk",
                invoice_numbers=[line.invoice_number],
            )
        )
    return drafts


def triage_notice(text: str, period: str | None = None) -> NoticeTriageResult:
    lowered = text.lower()
    issues: list[str] = []
    notice_type = "unknown"
    risk = "medium"
    deadline_days = None

    if "drc-01c" in lowered or "drc 01c" in lowered or "88d" in lowered:
        notice_type = "drc_01c"
        risk = "high"
        deadline_days = 7
        issues.append("ITC claimed appears higher than GSTR-2B credit.")
    elif "asmt-10" in lowered or "asmt 10" in lowered:
        notice_type = "asmt_10"
        risk = "medium"
        deadline_days = 30
        issues.append("Scrutiny notice requires document-backed explanation.")
    elif "88c" in lowered or "gstr-1" in lowered and "gstr-3b" in lowered:
        notice_type = "rule_88c"
        risk = "high"
        deadline_days = 7
        issues.append("GSTR-1 liability may not reconcile with GSTR-3B payment.")
    else:
        issues.append("Notice type could not be classified from the supplied text.")

    period_text = f" for {period}" if period else ""
    draft = (
        f"Draft reply{period_text}: We acknowledge the notice and are reconciling the "
        "underlying GST returns, purchase register, and supporting invoices. We request "
        "that the officer consider the attached reconciliation statement and allow us to "
        "submit corrected particulars where required."
    )
    return NoticeTriageResult(
        notice_type=notice_type,
        risk=risk,
        deadline_days=deadline_days,
        issues=issues,
        draft_reply=draft,
        citations=["CGST Rule 88C/88D guidance requires source verification before filing a reply."],
    )


def check_prefile_mismatch(
    *,
    period: str,
    gstr1_taxable_value: float,
    gstr1_tax: float,
    gstr3b_taxable_value: float,
    gstr3b_tax: float,
) -> PrefileCheckResult:
    taxable_delta = round(gstr1_taxable_value - gstr3b_taxable_value, 2)
    tax_delta = round(gstr1_tax - gstr3b_tax, 2)
    risk = abs(tax_delta) > 0
    severity = "error" if abs(tax_delta) >= 100000 else "warning" if risk else "info"
    if not risk:
        message = "GSTR-1 and GSTR-3B tax values reconcile for this pre-file check."
    elif severity == "error":
        message = "Material tax mismatch may trigger a Rule 88C-style notice workflow."
    else:
        message = "Tax mismatch should be reconciled before filing."
    return PrefileCheckResult(
        period=period,
        rule_88c_risk=risk,
        taxable_delta=taxable_delta,
        tax_delta=tax_delta,
        severity=severity,
        message=message,
    )
