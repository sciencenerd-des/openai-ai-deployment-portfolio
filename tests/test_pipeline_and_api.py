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


def test_reconcile_sample_endpoint():
    r = client.get("/api/reconcile/sample")
    assert r.status_code == 200
    body = r.json()
    assert body["period"] == "2026-04"
    assert body["summary"]["total"] == 6.0
    assert {m["status"] for m in body["matches"]} >= {"matched", "in_register_not_2b"}


def test_reconcile_endpoint_accepts_structured_payload():
    r = client.post(
        "/api/reconcile",
        json={
            "period": "2026-04",
            "purchase_register": [
                {
                    "supplier_gstin": "27AAPFU0939F1ZV",
                    "invoice_number": "INV-1",
                    "invoice_date": "2026-04-18",
                    "taxable_value": 1000.0,
                    "cgst": 90.0,
                    "sgst": 90.0,
                }
            ],
            "gstr2b": [
                {
                    "ctin": "27AAPFU0939F1ZV",
                    "invoice_number": "INV/1",
                    "invoice_date": "2026-04-18",
                    "taxable_value": 1000.0,
                    "cgst": 90.0,
                    "sgst": 90.0,
                }
            ],
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["matches"][0]["status"] == "matched"
    assert body["matches"][0]["ims_action"] == "accept"
    assert body["matches"][0]["itc"]["verdict"] == "claim"


def test_followups_endpoint_drafts_missing_2b_email():
    report = client.get("/api/reconcile/sample").json()
    r = client.post("/api/followups", json=report)

    assert r.status_code == 200
    body = r.json()
    assert len(body) == 1
    assert body[0]["requires_approval"] is True
    assert body[0]["invoice_numbers"] == ["RJ-19"]


def test_notice_triage_endpoint():
    r = client.post(
        "/api/notices/triage",
        json={"text": "ASMT-10 scrutiny notice for mismatch", "period": "2026-04"},
    )

    assert r.status_code == 200
    assert r.json()["notice_type"] == "asmt_10"


def test_prefile_check_endpoint():
    r = client.post(
        "/api/prefile-check",
        json={
            "period": "2026-04",
            "gstr1_taxable_value": 1000.0,
            "gstr1_tax": 180.0,
            "gstr3b_taxable_value": 1000.0,
            "gstr3b_tax": 180.0,
        },
    )

    assert r.status_code == 200
    assert r.json()["rule_88c_risk"] is False


def test_batch_analyze_endpoint():
    r = client.post("/api/analyze/batch", json={"texts": ["normal invoice", "dirty", "hindi invoice"]})

    assert r.status_code == 200
    body = r.json()
    assert len(body) == 3
    assert body[0]["anomalies"] == []
    assert any(item["severity"] == "error" for item in body[1]["anomalies"])
    assert body[2]["extracted"]["detected_language"] == "hi"


def test_batch_analyze_files_endpoint_uses_mock_mode_without_network():
    r = client.post(
        "/api/analyze/batch-files",
        files=[
            ("files", ("invoice-a.png", b"fake-image-a", "image/png")),
            ("files", ("invoice-b.png", b"fake-image-b", "image/png")),
        ],
    )

    assert r.status_code == 200
    body = r.json()
    assert len(body) == 2
    assert body[0]["mode"] == "mock"


def test_index_served():
    r = client.get("/")
    assert r.status_code == 200
    assert "Bharat Doc Intelligence" in r.text
