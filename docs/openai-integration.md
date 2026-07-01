# OpenAI Integration

This document explains where and how Bharat Doc Intelligence uses OpenAI APIs.

## Flow

1. A user uploads a GST invoice or receipt.
2. The extraction pipeline prepares the document for model input.
3. OpenAI vision-capable models extract structured invoice data.
4. The app validates the output with deterministic GST and tax rules.
5. The API returns extracted fields, confidence metadata, and audit flags.

## Design principles

- Use the model for perception and extraction.
- Use deterministic Python code for compliance and math checks.
- Keep API responses structured, inspectable, and testable.
- Support mock mode so developers can run the app without secrets.
- Run evals so prompt/model changes do not silently regress.

## OpenAI developer concepts demonstrated

- multimodal input handling through image and text content
- structured response design with Pydantic schemas
- model output validation after generation
- function-tool style GSTIN validation
- safe mock-mode fallback behavior
- eval regression testing
- API-key based local configuration
- separation of model extraction from deterministic business rules

## Key files

- `app/agent.py` — OpenAI-facing extraction logic using the Agents SDK, Responses API-style multimodal inputs, schema-constrained output, and a GSTIN validation tool.
- `app/pipeline.py` — orchestration layer and live/mock boundary.
- `app/schemas.py` — structured response models.
- `app/validators.py` — GSTIN and tax validation.
- `evals/run_evals.py` — regression eval runner.
