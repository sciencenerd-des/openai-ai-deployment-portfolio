# Build a multimodal document agent with the OpenAI Agents SDK

A step-by-step walkthrough of how Bharat Doc Intelligence works, so you can build
your own structured-extraction agent. ~15 minutes. The finished code is this repo.

> **The core idea:** let the model *read* the document into a typed schema, then
> let plain Python *judge* it. Models are great at perception and terrible at
> arithmetic you actually want to trust — so don't ask them to do both.

## 1. Define the shape of the answer first

Before touching the model, describe exactly what a "read" document is, as a
Pydantic model. The Agents SDK will hold the model to this shape.

```python
# app/schemas.py
class ExtractedInvoice(BaseModel):
    document_type: Literal["tax_invoice", "receipt", "bill_of_supply", "unknown"]
    supplier_gstin: str | None = None
    line_items: list[LineItem] = []
    subtotal: float | None = None
    total_tax: float | None = None
    grand_total: float | None = None
    detected_language: str | None = None
    # ...
```

## 2. Create the agent with a tool and an `output_type`

```python
# app/agent.py
from agents import Agent, Runner, function_tool

@function_tool
def validate_gstin(gstin: str) -> str:
    ok, reason = _validate_gstin(gstin)
    return f"{'VALID' if ok else 'INVALID'}: {reason}"

agent = Agent(
    name="Bharat Doc Intelligence",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    tools=[validate_gstin],
    output_type=ExtractedInvoice,   # <- the model is constrained to this schema
)
```

Two things matter here: `output_type` removes all JSON-parsing glue, and
`tools=[validate_gstin]` lets the model self-check GST numbers while it reads.

## 3. Pass the image (vision) via the Responses API

The Agents SDK accepts Responses-API input items. To send an image, build a
`user` message whose content mixes `input_text` and `input_image`:

```python
content = [
    {"type": "input_text", "text": "Extract all fields from this document."},
    {"type": "input_image", "image_url": f"data:image/png;base64,{b64}", "detail": "high"},
]
result = await Runner.run(agent, [{"role": "user", "content": content}])
invoice = result.final_output_as(ExtractedInvoice)
```

## 4. Judge the result in deterministic code

Now that you have structure, never trust the model for correctness — compute it:

```python
# app/validators.py — pure functions, fully unit-tested
anomalies = validate_document(invoice)   # GSTIN checksum, line maths, CGST==SGST...
confidence = score_confidence(anomalies)
```

The GSTIN checksum is the GSTN modulo-36 algorithm — a nice example of a check
the model *cannot* fake.

## 5. Make it runnable without a key

Wrap the model call so the app falls back to deterministic fixtures when there's
no `OPENAI_API_KEY`. This is the single highest-leverage thing you can do for a
demo: reviewers, tests, and CI all run instantly and for free.

```python
def _extract(image_bytes, text, mime):
    if settings.use_mock:
        return mock_extract(text)
    from .agent import run_extraction      # lazy import: SDK only needed live
    return asyncio.run(run_extraction(image_bytes=image_bytes, text=text, mime=mime))
```

## 6. Gate the logic with evals

Treat anomaly detection as a labelled multi-label task and score precision /
recall / F1. Wire it into CI so a regression fails the build:

```bash
python -m evals.run_evals    # exits non-zero if exact-match accuracy drops
```

## Where to take it next

- Swap `gpt-4o-mini` for a frontier model and compare eval scores.
- Add a handoff to a second agent that drafts a GST-compliant corrected invoice.
- Stream partial extraction to the UI with the Agents SDK streaming events.
