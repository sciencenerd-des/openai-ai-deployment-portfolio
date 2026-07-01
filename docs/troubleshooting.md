# Troubleshooting

## Missing API key

Use mock mode for zero-key local development:

```bash
export USE_MOCK=1
```

## OpenAI API error

Check that:

- `OPENAI_API_KEY` is set.
- the configured model name is valid.
- the uploaded image is not too large.
- network access is available.

## Bad extraction

Try:

- a clearer image
- a cropped invoice
- a higher-resolution capture
- the mock fixture to isolate API behavior from validation behavior

## Tests fail locally

```bash
pip install -r requirements-dev.txt
pytest -q
python -m evals.run_evals --write
```
