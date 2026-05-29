"""FastAPI surface for Bharat Doc Intelligence.

Endpoints
---------
GET  /              -> static single-page UI
GET  /api/health    -> {status, mode}
POST /api/analyze   -> multipart (file) and/or form field `text` -> AnalysisReport
GET  /api/reconcile/sample -> deterministic sample ReconReport
POST /api/reconcile -> JSON purchase register + GSTR-2B lines -> ReconReport
POST /api/followups -> draft supplier follow-up emails from a ReconReport
POST /api/notices/triage -> classify a notice and draft a reviewed reply
POST /api/prefile-check -> compare GSTR-1 and GSTR-3B values
POST /api/analyze/batch -> analyze up to 25 text snippets
POST /api/analyze/batch-files -> analyze up to 10 uploaded files
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import FileResponse, JSONResponse

from .config import settings
from .compliance import check_prefile_mismatch, draft_vendor_followups, triage_notice
from .pipeline import analyze
from .reconciliation import reconcile, sample_reconciliation_report
from .schemas import (
    AnalysisReport,
    BatchAnalyzeRequest,
    DraftEmail,
    NoticeTriageRequest,
    NoticeTriageResult,
    PrefileCheckRequest,
    PrefileCheckResult,
    ReconcileRequest,
    ReconReport,
)

WEB_DIR = Path(__file__).resolve().parent.parent / "web"

app = FastAPI(
    title="Bharat Doc Intelligence",
    version="0.1.0",
    description="Multimodal GST-document understanding for Indian SMBs, "
                "built on the OpenAI Agents SDK + Responses API.",
)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "mode": settings.mode, "model": settings.model}


@app.post("/api/analyze", response_model=AnalysisReport)
async def analyze_endpoint(
    file: UploadFile | None = File(default=None),
    text: str | None = Form(default=None),
) -> AnalysisReport:
    image_bytes = await file.read() if file is not None else None
    mime = (file.content_type if file else None) or "image/png"
    return analyze(image_bytes=image_bytes, text=text, mime=mime)


@app.get("/api/reconcile/sample", response_model=ReconReport)
def reconcile_sample_endpoint() -> ReconReport:
    return sample_reconciliation_report()


@app.post("/api/reconcile", response_model=ReconReport)
def reconcile_endpoint(payload: ReconcileRequest) -> ReconReport:
    return reconcile(
        period=payload.period,
        purchase_register=payload.purchase_register,
        gstr2b=payload.gstr2b,
    )


@app.post("/api/followups", response_model=list[DraftEmail])
def followups_endpoint(report: ReconReport) -> list[DraftEmail]:
    return draft_vendor_followups(report)


@app.post("/api/notices/triage", response_model=NoticeTriageResult)
def notice_triage_endpoint(payload: NoticeTriageRequest) -> NoticeTriageResult:
    return triage_notice(payload.text, payload.period)


@app.post("/api/prefile-check", response_model=PrefileCheckResult)
def prefile_check_endpoint(payload: PrefileCheckRequest) -> PrefileCheckResult:
    return check_prefile_mismatch(
        period=payload.period,
        gstr1_taxable_value=payload.gstr1_taxable_value,
        gstr1_tax=payload.gstr1_tax,
        gstr3b_taxable_value=payload.gstr3b_taxable_value,
        gstr3b_tax=payload.gstr3b_tax,
    )


@app.post("/api/analyze/batch", response_model=list[AnalysisReport])
def batch_analyze_endpoint(payload: BatchAnalyzeRequest) -> list[AnalysisReport]:
    return [analyze(text=text) for text in payload.texts]


@app.post("/api/analyze/batch-files", response_model=list[AnalysisReport])
async def batch_analyze_files_endpoint(
    files: list[UploadFile] = File(...),
) -> list[AnalysisReport]:
    reports: list[AnalysisReport] = []
    for file in files[:10]:
        image_bytes = await file.read()
        reports.append(analyze(image_bytes=image_bytes, mime=file.content_type or "image/png"))
    return reports


@app.get("/", response_model=None)
def index() -> FileResponse | JSONResponse:
    index_html = WEB_DIR / "index.html"
    if index_html.exists():
        return FileResponse(index_html)
    return JSONResponse({"detail": "UI not found", "try": "/api/health"})
