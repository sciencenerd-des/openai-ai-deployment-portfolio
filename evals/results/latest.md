# Eval results — validation layer

- cases: **7**
- exact-match accuracy: **100%**
- precision: **1.00** · recall: **1.00** · F1: **1.00**

| case | expected | detected | ✓ |
|------|----------|----------|---|
| clean_intrastate_invoice | — | — | ✅ |
| bad_gstin_checksum | gstin_invalid | gstin_invalid | ✅ |
| missing_supplier_gstin | missing_supplier_gstin | missing_supplier_gstin | ✅ |
| line_amount_mismatch | line_amount_mismatch, subtotal_mismatch | line_amount_mismatch, subtotal_mismatch | ✅ |
| grand_total_mismatch | grand_total_mismatch | grand_total_mismatch | ✅ |
| mixed_tax_heads | mixed_tax_heads | mixed_tax_heads | ✅ |
| cgst_sgst_asymmetry | cgst_sgst_asymmetry | cgst_sgst_asymmetry | ✅ |
