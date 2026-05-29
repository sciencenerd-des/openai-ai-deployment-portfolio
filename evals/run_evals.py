"""Offline eval harness for the validation layer.

Each labelled case lists the anomaly *codes* a correct validator should raise.
We score detection as a multi-label problem and report precision / recall / F1
over codes, plus exact-match accuracy per case. Runs with no API key.

Usage:
    python -m evals.run_evals            # print report
    python -m evals.run_evals --write    # also write evals/results/latest.md

Exit code is non-zero if exact-match accuracy drops below THRESHOLD, so this
doubles as a regression gate in CI.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.schemas import ExtractedInvoice  # noqa: E402
from app.validators import validate_document  # noqa: E402

THRESHOLD = 1.0  # require perfect exact-match on the curated set
HERE = Path(__file__).resolve().parent
CASES = HERE / "dataset" / "cases.json"


def evaluate() -> dict:
    cases = json.loads(CASES.read_text())
    tp = fp = fn = 0
    exact = 0
    rows = []
    for case in cases:
        doc = ExtractedInvoice.model_validate(case["doc"])
        detected = {a.code for a in validate_document(doc)}
        expected = set(case["expected_codes"])
        tp += len(detected & expected)
        fp += len(detected - expected)
        fn += len(expected - detected)
        is_exact = detected == expected
        exact += int(is_exact)
        rows.append((case["name"], sorted(expected), sorted(detected), is_exact))

    precision = tp / (tp + fp) if (tp + fp) else 1.0
    recall = tp / (tp + fn) if (tp + fn) else 1.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    return {
        "n": len(cases),
        "exact_match": exact / len(cases),
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "rows": rows,
    }


def to_markdown(r: dict) -> str:
    lines = [
        "# Eval results — validation layer",
        "",
        f"- cases: **{r['n']}**",
        f"- exact-match accuracy: **{r['exact_match']:.0%}**",
        f"- precision: **{r['precision']:.2f}** · recall: **{r['recall']:.2f}** · F1: **{r['f1']:.2f}**",
        "",
        "| case | expected | detected | ✓ |",
        "|------|----------|----------|---|",
    ]
    for name, exp, det, ok in r["rows"]:
        lines.append(f"| {name} | {', '.join(exp) or '—'} | {', '.join(det) or '—'} | {'✅' if ok else '❌'} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    r = evaluate()
    md = to_markdown(r)
    print(md)
    if "--write" in sys.argv:
        out = HERE / "results" / "latest.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(md)
        print(f"wrote {out}")
    if r["exact_match"] < THRESHOLD:
        print(f"FAIL: exact-match {r['exact_match']:.0%} < {THRESHOLD:.0%}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
