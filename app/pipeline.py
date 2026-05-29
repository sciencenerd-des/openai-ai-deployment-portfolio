"""Orchestration: extract -> validate -> score.

This is the single entry point used by the API, tests and evals. It keeps the
``agents``/``openai`` imports lazy so mock-mode callers never need them.
"""

from __future__ import annotations

import asyncio

from .config import settings
from .mock import mock_extract
from .schemas import AnalysisReport, ExtractedInvoice
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
    return AnalysisReport(
        mode=settings.mode,
        extracted=extracted,
        anomalies=anomalies,
        confidence=score_confidence(anomalies),
    )
