# Reproduce the validation workflow

This project illustrates a practical AI engineering pattern: use a model for
document perception and deterministic code for checks over the extracted fields.
You can inspect that separation without calling a model or creating an account.

## Five-minute local run

```bash
git clone https://github.com/sciencenerd-des/openai-ai-deployment-portfolio.git
cd openai-ai-deployment-portfolio
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python scripts/reviewer_demo.py
USE_MOCK=1 python -m pytest -q
USE_MOCK=1 python -m evals.run_evals
```

The demonstration calls the real FastAPI routes in process. It forces mock mode
before settings load, shows clean and deliberately inconsistent synthetic
invoices, and checks that supplier follow-ups remain drafts requiring approval.
It sends no messages. Output includes anomaly codes and the mock mode label.

## What to inspect

| File | Question |
| --- | --- |
| `app/mock.py` | Which fields are synthetic fixtures rather than extracted observations? |
| `app/pipeline.py` | Where does extraction end and deterministic checking begin? |
| `app/validators.py` | Which anomaly codes can the rules actually detect? |
| `evals/dataset/cases.json` | What expected output is specified independently for each case? |
| `tests/test_pipeline_and_api.py` | Does the API preserve mode labels and review requirements? |

With Codex, try this review prompt:

> Read AGENTS.md and trace one dirty invoice from the mock fixture through the
> API to its anomaly codes. Identify one possible extraction error the current
> validator cases would miss. Propose a synthetic negative control before
> changing code. Do not call a live API or use real taxpayer data.

This is a suggested learning workflow; it does not assert historical Codex
authorship of the project.

## Interpret the results narrowly

The eval runner starts from structured fields, not invoice images. Its seven
curated cases measure agreement on anomaly-code sets. A perfect result on that
small set says nothing about live-model extraction accuracy, regional-language
recognition, or unseen invoice formats.

Mock registry status, reconciliation decisions, ITC labels, and notice triage
are prototype outputs. They do not establish current GST rules or replace
professional review. No live GSTN integration or production deployment is
verified by this walkthrough. Read [the evaluation scope](eval-report.md)
before quoting any score.

The current [license](../LICENSE) reserves reuse and redistribution rights.
Reviewing the public source does not grant an open-source license.
