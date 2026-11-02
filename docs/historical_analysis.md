# Paper-specific historical analysis scripts

These scripts are author-owned analysis code retained from the paper collection and made available alongside the general POP verifier. They reproduce specific analyses from **existing saved evidence**; they are separate from the missing historical POP validator. [Source hashes](source_adaptation.json) identify the inspected originals. The adaptations require explicit input/output paths and remove fixed laboratory path rewriting.

Install optional analysis dependencies in a separate environment:

```sh
python -m pip install -e '.[historical]'
```

## Original synthetic conformance experiment

```sh
python scripts/historical/controlled_benchmark.py --output output/original-conformance
```

This is the original author-designed NumPy experiment from the paper package: five synthetic training seeds, one clean package and 15 mutations. It regenerates synthetic data and the combined/partial-rule reports. The destination must not exist; the script refuses overwrites. It is distinct from the newer `examples/evidence_pipeline` fixture and is not independent forensic validation. No GPU or actual image dataset is needed.

## Historical prediction rescoring

```sh
python scripts/historical/rescore_historical.py --root HISTORICAL_EVIDENCE_ROOT > rescore.json
```

This executes the original CPU analysis of the 238,872-row content-excluded cohort, PatchMoE same-forward contrast, three-seed DE3 comparisons, source-prior diagnostic and retained census summaries. It requires the original census and exclusion Parquet files, saved per-image prediction CSVs for all listed arms, and archived PatchMoE predictions arranged in the same directories as the research package. Those files are not distributed in this public repository; use them only if you have authorized access.

For paths exported with different prefixes, pass both `--path-prefix-from OLD_PREFIX --path-prefix-to NEW_PREFIX`. This affects prediction identity strings only; verify the resulting identities correspond to the census. The original analysis uses assertions and must be run without Python's `-O` option. Script output includes input paths; inspect and redact sensitive paths before sharing reports.

The script trusts the retained census hashes/flags rather than newly decoding images; its paired scores are fresh calculations from saved model predictions, not fresh model training or independent POP scope decisions. Missing or incompatible data raise errors.

## Original optimizer-log check

```sh
python scripts/historical/verify_historical_updates.py --root HISTORICAL_EVIDENCE_ROOT > updates.json
```

Requires retained logs, initialization receipts and frozen-base receipts for all nine DE3 arms (three seeds × three settings) under `paper_submission_audit_20261019/execution/checkpoints/`. It reports per-epoch optimizer calls, nonfinite losses and matched initialization/data signatures. Missing records raise errors. Output contains source paths and potentially sensitive metadata: review it before distribution. This check does not recover missing scaler traces or prove why the 4-call gaps occurred.

For portable studies that do not have this exact historical layout, use the [general evidence producer tools](evidence_producers.md). The original 58-scope matrix, original POP validator and archive catalog remain unavailable; these scripts cannot recreate them.
