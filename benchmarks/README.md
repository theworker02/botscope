# Benchmarks

Runnable microbenchmarks for BotScope internal hot paths.

```bash
python benchmarks/microbench.py --output benchmarks/last_receipt.json
```

Receipts are machine-local measurements. **Do not copy fabricated timings into
FEATURES.md or marketing materials.** Commit receipts only when intentionally
documenting a specific environment.
