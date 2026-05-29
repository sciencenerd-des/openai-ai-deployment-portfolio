"""Pydantic schemas for extracted documents and the analysis report.

The ``ExtractedInvoice`` schema is used directly as the Agents SDK ``output_type``
so the model is constrained to emit valid structured data.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

DocumentType = Literal["tax_invoice", "receipt", "bill_of_supply", "unknown"]
Severity = Literal["info", "warning", "error"]
SourceMode = Literal["mock", "live", "offline"]
MatchStatus = Literal[
    "matched",
    "in_2b_not_register",
    "in_register_not_2b",
    "value_mismatch_rounding",
    "value_mismatch_material",
]
ImsAction = Literal["accept", "reject", "pending", "none"]
ItcVerdict = Literal["claim", "defer", "block"]
NoticeType = Literal["drc_01c", "asmt_10", "rule_88c", "unknown"]


class LineItem(BaseModel):
    description: str = Field(description="Item or service description, as printed.")
    hsn_sac: Optional[str] = Field(
        default=None, description="HSN (goods) or SAC (services) code if present."
    )
    quantity: float = 1.0
    unit_price: float = 0.0
    amount: float = Field(
        default=0.0, description="Pre-tax line amount (quantity * unit_price)."
    )


class TaxBreakup(BaseModel):
    taxable_value: float = 0.0
    cgst: float = 0.0
    sgst: float = 0.0
    igst: float = 0.0


class ExtractedInvoice(BaseModel):
    """Structured representation the model is asked to return."""

    document_type: DocumentType = "unknown"
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = Field(
        default=None, description="ISO 8601 date (YYYY-MM-DD) if determinable."
    )
    irn: Optional[str] = Field(default=None, description="Printed e-invoice IRN if present.")
    document_subtype: Optional[str] = Field(
        default=None, description="Invoice document subtype such as INV, CRN, or DBN."
    )
    supplier_name: Optional[str] = None
    supplier_gstin: Optional[str] = None
    buyer_name: Optional[str] = None
    buyer_gstin: Optional[str] = None
    place_of_supply: Optional[str] = None
    currency: str = "INR"
    line_items: list[LineItem] = Field(default_factory=list)
    subtotal: Optional[float] = None
    total_tax: Optional[float] = None
    grand_total: Optional[float] = None
    tax_breakup: Optional[TaxBreakup] = None
    detected_language: Optional[str] = Field(
        default=None, description="Primary language of the document, e.g. 'en', 'hi', 'ta'."
    )
    notes: Optional[str] = None


class Anomaly(BaseModel):
    code: str
    severity: Severity
    message: str
    field: Optional[str] = None


class AnalysisReport(BaseModel):
    mode: str = Field(description="'live' or 'mock'.")
    extracted: ExtractedInvoice
    anomalies: list[Anomaly] = Field(default_factory=list)
    supplier_status: Optional["GstinStatus"] = None
    buyer_status: Optional["GstinStatus"] = None
    irn_status: Optional["IrnStatus"] = None
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Heuristic confidence (1.0 minus weighted anomaly penalty).",
    )

    @property
    def is_clean(self) -> bool:
        return not any(a.severity == "error" for a in self.anomalies)


class PurchaseLine(BaseModel):
    supplier_gstin: str
    invoice_number: str
    invoice_date: str = Field(description="ISO 8601 date (YYYY-MM-DD).")
    taxable_value: float
    igst: float = 0.0
    cgst: float = 0.0
    sgst: float = 0.0
    cess: float = 0.0
    category: Optional[str] = Field(
        default=None,
        description="Optional purchase category used for deterministic ITC blocking rules.",
    )


class Gstr2bLine(BaseModel):
    ctin: str = Field(description="Counterparty/supplier GSTIN.")
    invoice_number: str
    invoice_date: str = Field(description="ISO 8601 date (YYYY-MM-DD).")
    taxable_value: float
    igst: float = 0.0
    cgst: float = 0.0
    sgst: float = 0.0
    cess: float = 0.0
    supplier_filing_date: Optional[str] = Field(default=None, description="GSTR-2B supfildt.")
    section: str = "b2b"


class ItcAssessment(BaseModel):
    eligible: bool
    verdict: ItcVerdict
    risk: float = Field(ge=0.0, le=1.0)
    reasons: list[str] = Field(default_factory=list)


class ReconMatch(BaseModel):
    status: MatchStatus
    ims_action: ImsAction
    register_line: Optional[PurchaseLine] = None
    gstr2b_line: Optional[Gstr2bLine] = None
    deltas: dict[str, float] = Field(default_factory=dict)
    itc: Optional[ItcAssessment] = None


class ReconReport(BaseModel):
    period: str = Field(description="Return period, e.g. 2026-04.")
    matches: list[ReconMatch]
    summary: dict[str, float] = Field(default_factory=dict)


class ReconcileRequest(BaseModel):
    period: str = Field(description="Return period, e.g. 2026-04.")
    purchase_register: list[PurchaseLine]
    gstr2b: list[Gstr2bLine]


class GstinStatus(BaseModel):
    gstin: str
    well_formed: bool
    registered: bool
    status: Optional[str] = None
    legal_name: Optional[str] = None
    trade_name: Optional[str] = None
    registration_date: Optional[str] = None
    cancellation_date: Optional[str] = None
    name_match: Optional[bool] = None
    source: SourceMode = "mock"


class IrnStatus(BaseModel):
    irn: Optional[str] = None
    recomputed_irn: Optional[str] = None
    irn_matches: Optional[bool] = None
    qr_signature_valid: Optional[bool] = None
    irp_status: Optional[Literal["ACT", "CNL", "REJ"]] = None
    source: SourceMode = "offline"


class DraftEmail(BaseModel):
    supplier_gstin: str
    subject: str
    body: str
    severity: Literal["reminder", "escalation", "itc_at_risk"]
    invoice_numbers: list[str] = Field(default_factory=list)
    requires_approval: bool = True


class NoticeTriageRequest(BaseModel):
    text: str
    period: Optional[str] = None


class NoticeTriageResult(BaseModel):
    notice_type: NoticeType
    risk: Literal["low", "medium", "high"]
    deadline_days: Optional[int] = None
    issues: list[str] = Field(default_factory=list)
    draft_reply: str
    citations: list[str] = Field(default_factory=list)
    requires_human_review: bool = True


class PrefileCheckRequest(BaseModel):
    period: str
    gstr1_taxable_value: float
    gstr1_tax: float
    gstr3b_taxable_value: float
    gstr3b_tax: float


class PrefileCheckResult(BaseModel):
    period: str
    rule_88c_risk: bool
    taxable_delta: float
    tax_delta: float
    severity: Severity
    message: str


class BatchAnalyzeRequest(BaseModel):
    texts: list[str] = Field(min_length=1, max_length=25)
