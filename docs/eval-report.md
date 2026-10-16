# Evaluation scope and reproducible results

Verified locally on 16 October 2026 with Python 3.12 against source revision
`04123ef3c25b4f8255d4f37895d7bd8880bf9d39` before the reviewer documentation changes.

| Check | Observed result | What it measures |
| --- | --- | --- |
| `USE_MOCK=1 python -m pytest -q` | 30 tests passed | Covered validators, mock pipeline/API, reconciliation and prototype workflows |
| `USE_MOCK=1 python -m evals.run_evals` | 7/7 exact matches; precision, recall, F1 = 1.00 | Expected anomaly-code sets on seven curated structured inputs |

## Reproduce

```bash
python -m pip install -r requirements-dev.txt
USE_MOCK=1 python -m pytest -q
USE_MOCK=1 python -m evals.run_evals
```

Use `--write` on the eval runner to save its per-case Markdown results.
The case source is `evals/dataset/cases.json`; scoring lives in
`evals/run_evals.py`. Exact match requires the detected and expected anomaly-code
sets to be identical, and the current CI threshold is 1.0.

## What these scores do not establish

The eval begins with `ExtractedInvoice` data. It does not run image extraction,
the OpenAI Agents SDK, or the Responses API. The seven cases are curated
regressions, not a held-out, representative benchmark. No model comparison,
multilingual OCR accuracy, statistical generalisation, live GSTN verification,
or legal correctness follows from the score.

Mock Hindi and Tamil examples select synthetic fixtures based on text hints;
they are not measurements of regional-language understanding. The confidence
field is a rule-based score and is not a calibrated probability of correctness.

## Useful next evaluation work

- Create a consented or synthetic image corpus with independently labelled fields.
- Separate clean scans, mobile captures, noisy images, and language subsets.
- Measure field-level extraction accuracy separately from validation accuracy.
- Add unseen adversarial cases and report false positives and false negatives.
- Record model identifier, prompt, dataset revision, cost, and latency for live runs.
