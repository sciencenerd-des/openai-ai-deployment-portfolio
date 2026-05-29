# Bharat Doc Intelligence

**Multimodal GST-document understanding for Indian SMBs — built on the OpenAI Agents SDK + Responses API.**

[![CI](https://github.com/sciencenerd-des/openai-ai-deployment-portfolio/actions/workflows/ci.yml/badge.svg)](https://github.com/sciencenerd-des/openai-ai-deployment-portfolio/actions/workflows/ci.yml)
![python](https://img.shields.io/badge/python-3.12-blue)
![license](https://img.shields.io/badge/license-MIT-green)

Upload a photo of an Indian GST invoice or receipt — including ones printed in
regional languages — and get back **structured, validated data** with the dodgy
bits flagged: invalid GSTINs, line-item maths that doesn't add up, CGST/SGST
that isn't symmetric, IGST mixed with CGST/SGST, and more.

> **Design in one line:** the model *reads* the document into a typed schema;
> deterministic Python *judges* its correctness. You never trust an LLM with
> arithmetic you actually need to be right.

```
┌── photo / OCR text ──┐   ┌─ OpenAI Agents SDK ─┐   ┌──── pure-Python audit ────┐
│  GST invoice image   │ → │ vision + output_type │ → │ GSTIN checksum, line maths │ → report + confidence
│  (en / hi / ta / …)  │   │ + validate_gstin tool│   │ CGST=SGST, totals reconcile│
└──────────────────────┘   └──────────────────────┘   └────────────────────────────┘
```

See [`docs/architecture.md`](docs/architecture.md) for the full diagram and rationale.

> 📸 _Add a screenshot/GIF of the running UI here (`web/index.html`) — see TODO in the Roadmap._

## Quickstart (zero API key, ~30 seconds)

The app ships with a deterministic **mock mode**, so the whole pipeline, UI,
tests, and evals run with no key and no network.

```bash
pip install -r requirements-dev.txt
make test        # 13 tests, all offline
make eval        # anomaly-detection eval: 100% exact-match on the curated set
make run         # open http://localhost:8000  (type "dirty" in the box to see flags)
```

## Live mode (real model)

```bash
cp .env.example .env      # add your OPENAI_API_KEY
pip install -r requirements.txt
make run
```

In live mode the agent reads an uploaded image with `gpt-4o-mini` (vision),
constrained to the `ExtractedInvoice` schema, and may call the `validate_gstin`
function tool to self-check GST numbers. One-click deploy via [`render.yaml`](render.yaml)
or the included [`Dockerfile`](Dockerfile).

## What it checks (the "audit brain")

| Check | Severity | Example |
|-------|----------|---------|
| GSTIN format + modulo-36 checksum | error | `29AAAAA0000A1Z9` → checksum mismatch |
| Tax invoice missing supplier GSTIN | error | — |
| `quantity × unit_price ≠ line amount` | warning | `2 × 299 = 598`, printed `698` |
| Line items don't sum to subtotal | warning | — |
| `subtotal + tax ≠ grand total` | error | — |
| IGST mixed with CGST/SGST | error | a supply is inter- *or* intra-state |
| CGST ≠ SGST | warning | the two halves must be equal |

## Eval results

Anomaly detection is scored as a labelled multi-label task; CI fails if
exact-match accuracy regresses. Latest run ([`evals/results/latest.md`](evals/results/latest.md)):

- cases: **7** · exact-match: **100%** · precision **1.00** · recall **1.00** · F1 **1.00**

```bash
python -m evals.run_evals
```

## Project structure

```
app/
  main.py        FastAPI: /, /api/health, /api/analyze
  pipeline.py    extract → validate → score (keeps SDK imports lazy)
  agent.py       OpenAI Agents SDK: vision input, output_type, function tool
  schemas.py     Pydantic models (ExtractedInvoice, Anomaly, AnalysisReport)
  validators.py  GSTIN checksum + arithmetic/anomaly checks (pure, tested)
  mock.py        deterministic fixtures for offline mode
web/index.html   single-page UI (Tailwind CDN, no build step)
evals/           labelled dataset + scoring harness (CI regression gate)
tests/           pytest, runs fully offline
docs/            architecture + a build-it-yourself tutorial
```

## Tech stack

OpenAI **Agents SDK** · **Responses API** (multimodal/vision) · FastAPI · Pydantic v2 · pytest · GitHub Actions · Docker.

## Roadmap

- [ ] Add a UI screenshot + GIF to this README.
- [ ] Second agent (handoff) that drafts a corrected, GST-compliant invoice.
- [ ] Stream partial extraction to the UI via Agents SDK streaming events.
- [ ] Expand the eval set with real regional-language document scans.

## Tutorial

A full walkthrough of how this is built — and how to build your own structured
multimodal agent — is in [`docs/TUTORIAL.md`](docs/TUTORIAL.md).

## License

MIT — see [LICENSE](LICENSE).
