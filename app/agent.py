"""OpenAI Agents SDK integration (live mode only).

Everything in this module is imported lazily by ``pipeline.py`` so that mock-mode
runs, unit tests, and CI do not require the ``openai-agents`` package or a key.

The extraction agent:
* reads an invoice **image** (vision, via the Responses API ``input_image`` item),
* is constrained to the ``ExtractedInvoice`` Pydantic schema (``output_type``),
* can call the ``validate_gstin`` **function tool** to self-check GST numbers.
"""

from __future__ import annotations

import base64

from agents import Agent, Runner, function_tool

from .config import settings
from .schemas import ExtractedInvoice
from .validators import validate_gstin as _validate_gstin

INSTRUCTIONS = """\
You are Bharat Doc Intelligence, an expert at reading Indian business documents
(GST tax invoices, receipts, bills of supply), including documents printed in
regional languages such as Hindi, Tamil, Telugu, Bengali, and Marathi.

Extract every field of the ExtractedInvoice schema as faithfully as possible:
- Transcribe numbers exactly as printed; do not "fix" arithmetic.
- Normalise the invoice date to ISO 8601 (YYYY-MM-DD) when you can read it.
- Set detected_language to the primary language of the document.
- Use the validate_gstin tool to check any GSTIN you read; if it is invalid,
  still report the number exactly as printed and note the issue in `notes`.
- If a field is absent, leave it null rather than guessing.
"""


@function_tool
def validate_gstin(gstin: str) -> str:
    """Validate an Indian GSTIN and explain why it is or isn't valid."""
    ok, reason = _validate_gstin(gstin)
    return f"{'VALID' if ok else 'INVALID'}: {reason}"


def build_agent() -> "Agent":
    return Agent(
        name="Bharat Doc Intelligence",
        instructions=INSTRUCTIONS,
        model=settings.model,
        tools=[validate_gstin],
        output_type=ExtractedInvoice,
    )


def _data_url(image_bytes: bytes, mime: str = "image/png") -> str:
    b64 = base64.b64encode(image_bytes).decode("ascii")
    return f"data:{mime};base64,{b64}"


async def run_extraction(
    *, image_bytes: bytes | None = None, text: str | None = None,
    mime: str = "image/png",
) -> ExtractedInvoice:
    """Run the agent on an image and/or text and return structured output."""
    agent = build_agent()

    content: list[dict] = []
    prompt = text or "Extract all fields from this document."
    content.append({"type": "input_text", "text": prompt})
    if image_bytes:
        content.append({
            "type": "input_image",
            "image_url": _data_url(image_bytes, mime),
            "detail": "high",
        })

    result = await Runner.run(agent, [{"role": "user", "content": content}])
    return result.final_output_as(ExtractedInvoice)
