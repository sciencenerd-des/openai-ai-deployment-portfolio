"""Pydantic schemas for extracted documents and the analysis report.

The ``ExtractedInvoice`` schema is used directly as the Agents SDK ``output_type``
so the model is constrained to emit valid structured data.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

DocumentType = Literal["tax_invoice", "receipt", "bill_of_supply", "unknown"]
Severity = Literal["info", "warning", "error"]


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
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Heuristic confidence (1.0 minus weighted anomaly penalty).",
    )

    @property
    def is_clean(self) -> bool:
        return not any(a.severity == "error" for a in self.anomalies)
