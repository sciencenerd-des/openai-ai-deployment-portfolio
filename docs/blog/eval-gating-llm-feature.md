# Eval-Gating an LLM Feature: From "Seems to Work" to a Hard CI Check

LLM demos can rot silently. A prompt change, model upgrade, or parser refactor
may still return `200 OK` while making the feature worse. Bharat Doc
Intelligence avoids that failure mode by turning its deterministic audit layer
into a hard CI gate.

## 1. Separate perception from judgment

The app has two different quality problems:

1. Perception: did the model read the invoice correctly?
2. Judgment: given extracted data, did the app flag the right violations?

The first problem is expensive and probabilistic. It needs real documents,
vision-model calls, and fuzzy scoring.

The second problem is deterministic. It can run locally, for free, on every
commit. That is the layer we gate most aggressively.

## 2. Use a labeled multi-label dataset

Each eval case provides an extracted invoice payload and the exact anomaly codes
that should be raised.

```json
[
  {
    "name": "bad_gstin_checksum",
    "expected_codes": ["gstin_invalid"],
    "doc": {
      "document_type": "tax_invoice",
      "supplier_gstin": "29AAAAA0000A1Z9"
    }
  }
]
```

The harness loads each fixture into the same Pydantic model used by the app,
runs the validator, and compares detected anomaly codes against the labels.

```python
for case in cases:
    doc = ExtractedInvoice.model_validate(case["doc"])
    detected = {a.code for a in validate_document(doc)}
    expected = set(case["expected_codes"])

    tp += len(detected & expected)
    fp += len(detected - expected)
    fn += len(expected - detected)
    exact += int(detected == expected)
```

## 3. Prefer exact-match for compliance logic

Precision and recall are useful, but the repo also tracks exact-match accuracy.
In a compliance product, false alarms and missed errors both matter. If a clean
invoice is flagged incorrectly, users stop trusting the tool. If a bad invoice is
missed, the tool creates real financial risk.

For the curated regression set, the threshold is intentionally strict:

```python
THRESHOLD = 1.0

if result["exact_match"] < THRESHOLD:
    return 1
```

One broken fixture should fail CI.

## 4. Run the gate without secrets

The GitHub Actions workflow forces mock mode:

```yaml
env:
  USE_MOCK: "1"

steps:
  - uses: actions/checkout@v4
  - uses: actions/setup-python@v5
    with:
      python-version: "3.12"
  - run: pip install -r requirements-dev.txt
  - run: pytest -q
  - run: python -m evals.run_evals --write
```

No OpenAI key is needed. No GSTN credentials are needed. The quality gate is
cheap enough to run on every push and strict enough to block regressions.

## 5. Evaluate perception separately

The vision/extraction layer still needs evaluation, but it should not run on
every tiny commit. A practical setup is:

- run perception evals on a schedule or release-candidate branch;
- score text fields with edit distance or token similarity;
- compare model versions against the same labeled image set;
- use the results to decide whether a model upgrade is worth shipping.

The important engineering move is not to mix this noisy evaluation with the
deterministic audit gate.

## The takeaway

Production AI systems need tests that fail loudly. For Bharat Doc Intelligence,
the model is allowed to be probabilistic at the perception boundary, but the
judgment layer is deterministic, labeled, and CI-gated.

That is the difference between "it seems to work" and a system you can keep
shipping with confidence.

