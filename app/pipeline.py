"""Orchestration: extract -> validate -> score.

This is the single entry point used by the API, tests and evals. It keeps the
``agents``/``openai`` imports lazy so mock-mode callers never need them.
"""

from __future__ import annotations

import asyncio

from .config import settings
from .compliance import get_gstin_status, verify_irn
from .mock import mock_extract
from .schemas import AnalysisReport, Anomaly, ExtractedInvoice
from .validators import score_confidence, validate_document


def _extract(image_bytes: bytes | None, text: str | None, mime: str) -> ExtractedInvoice:
    if settings.use_mock:
        return mock_extract(text)
    # Lazy import: only needed in live mode.
    from .agent import run_extraction

    return asyncio.run(
        run_extraction(image_bytes=image_bytes, text=text, mime=mime)
    )


def analyze(
    *, image_bytes: bytes | None = None, text: str | None = None,
    mime: str = "image/png",
) -> AnalysisReport:
    """Analyse a document and return a full report (extraction + anomalies)."""
    extracted = _extract(image_bytes, text, mime)
    anomalies = validate_document(extracted)
    supplier_status = get_gstin_status(extracted.supplier_gstin, extracted.supplier_name)
    buyer_status = get_gstin_status(extracted.buyer_gstin, extracted.buyer_name)
    irn_status = verify_irn(extracted)

    if supplier_status and supplier_status.well_formed:
        if supplier_status.status == "Cancelled":
            anomalies.append(Anomaly(
                code="gstin_cancelled",
                severity="error",
                message=f"Supplier GSTIN {supplier_status.gstin} is cancelled in the mock registry.",
                field="supplier_gstin",
            ))
        elif supplier_status.status == "Unverified":
            anomalies.append(Anomaly(
                code="gstin_unverified",
                severity="info",
                message=f"Supplier GSTIN {supplier_status.gstin} is well-formed but not live-verified.",
                field="supplier_gstin",
            ))
        elif supplier_status.name_match is False:
            anomalies.append(Anomaly(
                code="gstin_name_mismatch",
                severity="warning",
                message="Supplier name does not match the mock GSTIN registry legal name.",
                field="supplier_name",
            ))

    if irn_status and irn_status.irn_matches is False:
        anomalies.append(Anomaly(
            code="irn_mismatch",
            severity="warning",
            message="Printed IRN does not match the offline recomputation.",
            field="irn",
        ))

    return AnalysisReport(
        mode=settings.mode,
        extracted=extracted,
        anomalies=anomalies,
        supplier_status=supplier_status,
        buyer_status=buyer_status,
        irn_status=irn_status,
        confidence=score_confidence(anomalies),
    )
