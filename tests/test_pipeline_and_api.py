"""Pipeline + API tests run entirely in mock mode (no key, no network)."""

import os

os.environ["USE_MOCK"] = "1"  # force mock before importing app modules

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.pipeline import analyze  # noqa: E402

client = TestClient(app)


def test_pipeline_clean_document():
    report = analyze(text="a normal invoice")
    assert report.mode == "mock"
    assert report.extracted.document_type == "tax_invoice"
    assert report.is_clean
    assert report.confidence == 1.0


def test_pipeline_dirty_document_flags_anomalies():
    report = analyze(text="show me a dirty receipt with an anomaly")
    codes = {a.code for a in report.anomalies}
    # bad GSTIN checksum + arithmetic problems should surface
    assert "gstin_invalid" in codes
    assert report.confidence < 1.0
    assert not report.is_clean


def test_health_endpoint():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["mode"] == "mock"


def test_analyze_endpoint_with_text():
    r = client.post("/api/analyze", data={"text": "normal invoice"})
    assert r.status_code == 200
    body = r.json()
    assert body["extracted"]["supplier_gstin"] == "27AAPFU0939F1ZV"
    assert body["mode"] == "mock"


def test_index_served():
    r = client.get("/")
    assert r.status_code == 200
    assert "Bharat Doc Intelligence" in r.text
