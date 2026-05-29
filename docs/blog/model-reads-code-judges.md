# Model Reads, Code Judges: A Multimodal Agent You Can Actually Trust

How I built a GST-invoice agent using the OpenAI Agents SDK where the model
handles messy real-world perception, but deterministic code keeps the final
veto.

Large language models are excellent at reading chaotic documents. They can
handle a crumpled thermal receipt, a blurry phone photo, or a bill printed partly
in Hindi and partly in English.

But they are not the right authority for compliance judgment. You do not want a
model certifying that `2 * 299 = 598`, deciding whether an Indian GSTIN is valid,
or silently approving an input tax credit claim. If that decision is wrong, "the
model hallucinated" is not a serious answer in an audit.

Bharat Doc Intelligence uses one boundary throughout the app:

> The model reads unstructured reality into a typed schema. Deterministic Python
> judges whether that data is correct.

That split lets the app use the model for what it is good at, while keeping the
business-critical verdicts testable, repeatable, and explainable.

## 1. Start with typed schemas

Before calling a model, define what a valid extraction looks like. The app uses
Pydantic models such as `ExtractedInvoice`, `LineItem`, and `TaxBreakup`.

```python
class LineItem(BaseModel):
    description: str
    hsn_sac: str | None = None
    quantity: float = 1.0
    unit_price: float = 0.0
    amount: float = 0.0


class ExtractedInvoice(BaseModel):
    document_type: Literal["tax_invoice", "receipt", "bill_of_supply", "unknown"]
    supplier_gstin: str | None = None
    line_items: list[LineItem] = []
    subtotal: float | None = None
    total_tax: float | None = None
    grand_total: float | None = None
    detected_language: str | None = None
```

Passing this schema into the Agents SDK as `output_type` removes a large amount
of fragile glue code. The model is not asked to return "some JSON that probably
looks right"; it is constrained to return the application contract.

## 2. Let the agent inspect, not decide

The live extraction agent can call a GSTIN validation tool while reading a
document:

```python
@function_tool
def validate_gstin(gstin: str) -> str:
    ok, reason = _validate_gstin(gstin)
    return f"{'VALID' if ok else 'INVALID'}: {reason}"
```

That tool helps the model notice a bad GSTIN during extraction, but it does not
give the model authority over the final report. The downstream validation layer
runs the same deterministic checks independently.

The model is also instructed to transcribe rather than fix. If an invoice prints
the wrong line amount, the app wants that wrong amount captured exactly. An audit
tool must preserve the defect so the deterministic validator can catch it.

## 3. Feed the model messy pixels

The multimodal path sends mixed text and image content through the Agents SDK:

```python
content = [
    {"type": "input_text", "text": "Extract all fields from this document."},
    {"type": "input_image", "image_url": data_url, "detail": "high"},
]
result = await Runner.run(agent, [{"role": "user", "content": content}])
invoice = result.final_output_as(ExtractedInvoice)
```

At this point, the model's job is done. It has converted messy input into a
structured object. The verdict now belongs to code.

## 4. Put judgment in deterministic Python

Every compliance claim lives in pure Python:

```python
def validate_document(doc: ExtractedInvoice) -> list[Anomaly]:
    anomalies = []

    if doc.supplier_gstin:
        ok, reason = validate_gstin(doc.supplier_gstin)
        if not ok:
            anomalies.append(Anomaly(
                code="gstin_invalid",
                severity="error",
                message=reason,
                field="supplier_gstin",
            ))

    for i, item in enumerate(doc.line_items):
        expected = round(item.quantity * item.unit_price, 2)
        if item.amount and abs(expected - item.amount) > 1:
            anomalies.append(Anomaly(
                code="line_amount_mismatch",
                severity="warning",
                message="quantity * unit_price does not equal printed amount",
                field=f"line_items[{i}]",
            ))

    return anomalies
```

This matters because GSTIN validation is mathematical. A model can only guess
whether a GSTIN looks plausible. Python can prove whether the checksum is valid.

## 5. Make the project runnable without a key

The app falls back to deterministic mock fixtures when `OPENAI_API_KEY` is not
present:

```python
def _extract(image_bytes, text, mime):
    if settings.use_mock:
        return mock_extract(text)

    from .agent import run_extraction
    return asyncio.run(run_extraction(image_bytes=image_bytes, text=text, mime=mime))
```

That makes the repo easy to review. A developer can run the UI, tests, and evals
without spending tokens or configuring secrets.

## Why the pattern generalizes

The same perception-vs-judgment split applies beyond GST invoices:

- Contract analysis: let the model extract dates and clauses; let code enforce
  policy rules.
- System log triage: let the model summarize messy logs; let code decide whether
  thresholds page an engineer.
- Catalog ingestion: let the model read dimensions; let code validate units and
  shipping constraints.

Whenever AI output drives an operational action, the action should be a
deterministic function of validated data. Models read. Code judges.

