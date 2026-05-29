"""FastAPI surface for Bharat Doc Intelligence.

Endpoints
---------
GET  /              -> static single-page UI
GET  /api/health    -> {status, mode}
POST /api/analyze   -> multipart (file) and/or form field `text` -> AnalysisReport
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import FileResponse, JSONResponse

from .config import settings
from .pipeline import analyze
from .schemas import AnalysisReport

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


@app.get("/", response_model=None)
def index() -> FileResponse | JSONResponse:
    index_html = WEB_DIR / "index.html"
    if index_html.exists():
        return FileResponse(index_html)
    return JSONResponse({"detail": "UI not found", "try": "/api/health"})
