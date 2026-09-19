# Labeled evaluation fixtures

Small, hand-labeled event corpora for `botscope.eval` and calibration experiments.
Labels are researcher annotations for evaluation — not ground truth from vendors.

## Files

| File | Purpose |
|------|---------|
| `labeled_mini.jsonl` | Mini labeled set (classification field = label) |
| `asn_sample.json` | Tiny offline ASN table for `botscope.asn` tests |

Do not invent benchmark scores from these fixtures in marketing copy; run the eval harness.
