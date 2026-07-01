# Eval Report

The eval suite checks that the pipeline returns stable structured outputs for representative GST invoice cases.

| Case | Checks | Status |
|---|---|---|
| Sample invoice OCR | vendor fields, GSTIN, totals | Passing in mock mode |
| Tax math | CGST/SGST symmetry, line totals | Passing in mock mode |
| Compliance flags | invalid/missing fields surfaced | Passing in mock mode |

## How to run

```bash
USE_MOCK=1 python -m evals.run_evals --write
```

## Future evals

- scanned images in regional languages
- noisy mobile captures
- multi-page invoices
- handwritten corrections
- adversarial GSTIN values
