# API Reference

Run locally in mock mode:

```bash
USE_MOCK=1 uvicorn app.main:app --reload
```

Interactive docs are available at:

- http://localhost:8000/docs

## `GET /api/health`

Returns service status and current mode.

```bash
curl http://localhost:8000/api/health
```

Example response:

```json
{
  "status": "ok",
  "mode": "mock",
  "model": "gpt-4.1-mini"
}
```

## `POST /api/analyze`

Analyzes one uploaded document image and/or text snippet.

### Multipart form fields

| Field | Type | Required | Description |
|---|---|---:|---|
| `file` | file | no | Invoice/receipt image |
| `text` | string | no | OCR text or instruction |

Example with text:

```bash
curl -X POST http://localhost:8000/api/analyze \
  -F "text=GST invoice from Example Traders, total INR 1180 including CGST 90 and SGST 90"
```

Example with file:

```bash
curl -X POST http://localhost:8000/api/analyze \
  -F "file=@samples/example-invoice.png"
```

## `POST /api/analyze/batch`

Analyzes up to 25 text snippets.

```bash
curl -X POST http://localhost:8000/api/analyze/batch \
  -H "Content-Type: application/json" \
  -d '{"texts":["GST invoice total 1180", "Receipt with missing GSTIN"]}'
```

## `POST /api/analyze/batch-files`

Analyzes up to 10 uploaded files.

```bash
curl -X POST http://localhost:8000/api/analyze/batch-files \
  -F "files=@invoice-1.png" \
  -F "files=@invoice-2.png"
```

## `GET /api/reconcile/sample`

Returns a deterministic reconciliation sample.

```bash
curl http://localhost:8000/api/reconcile/sample
```

## `POST /api/reconcile`

Compares purchase-register lines with GSTR-2B lines and returns reconciliation status.

See the OpenAPI schema at `/docs` for the exact request model.

## `POST /api/followups`

Creates vendor follow-up email drafts from a reconciliation report.

## `POST /api/notices/triage`

Classifies a GST notice and drafts a reviewed response.

## `POST /api/prefile-check`

Compares GSTR-1 and GSTR-3B values before filing.

## Error handling

The API is designed to make failure modes inspectable:

- missing app UI returns a JSON hint
- validation issues are surfaced as audit flags
- mock mode can isolate app behavior from OpenAI/provider behavior
