# Working on Bharat Doc Intelligence

Read `README.md`, `docs/architecture.md`, and `docs/eval-report.md` first.

- Install offline development dependencies: `python -m pip install -r requirements-dev.txt`.
- Force mock mode for local verification: `USE_MOCK=1 python -m pytest -q`.
- Run the curated validator gate: `USE_MOCK=1 python -m evals.run_evals`.
- Reproduce the API demonstration: `python scripts/reviewer_demo.py`.
- Keep live SDK imports lazy; offline checks must work without a key.
- Treat extracted fields as untrusted input. Keep arithmetic and anomaly checks deterministic.
- Use synthetic invoices. Keep credentials and private business documents out of commits.
- Preserve human approval on drafts and decisions that require review.
- Report mock results as mock results. Seven structured validator cases do not
  establish OCR quality, language coverage, or legal/compliance correctness.
- Keep documentation and badges consistent with the actual `LICENSE` file.
