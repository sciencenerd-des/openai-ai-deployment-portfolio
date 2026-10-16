"""Demonstrate the real API with synthetic mock inputs and no credentials.

Install requirements-dev.txt, then run: python scripts/reviewer_demo.py
This is an integration demonstration, not an OCR or live-model benchmark.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Override before importing settings even if the caller has a real API key.
os.environ["USE_MOCK"] = "1"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


def main() -> int:
    with TestClient(app) as client:
        observations = []
        for text, expected_clean in [("normal invoice", True), ("dirty invoice", False)]:
            response = client.post("/api/analyze", data={"text": text})
            response.raise_for_status()
            report = response.json()
            codes = sorted({item["code"] for item in report["anomalies"]})
            if report["mode"] != "mock" or (not codes) != expected_clean:
                raise RuntimeError("Mock fixture did not produce the expected validation result")
            if not expected_clean and "gstin_invalid" not in codes:
                raise RuntimeError("Dirty fixture must expose the invalid GSTIN")
            observations.append({
                "input": text, "mode": report["mode"],
                "anomaly_codes": codes, "confidence": report["confidence"],
            })

        reconciliation = client.get("/api/reconcile/sample")
        reconciliation.raise_for_status()
        drafts = client.post("/api/followups", json=reconciliation.json())
        drafts.raise_for_status()
        messages = drafts.json()
        if not messages or not all(message["requires_approval"] for message in messages):
            raise RuntimeError("Follow-up drafts must require human approval")

    print(json.dumps({
        "observations": observations,
        "followup_drafts": len(messages),
        "all_drafts_require_approval": True,
        "scope": "Synthetic mock extraction + real validators and in-process API; no sending.",
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
