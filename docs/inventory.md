# Source and reuse inventory

Inspected against the current manuscript and local research package, plus the external reproduction repository. No historical code or data was imported into this release. The new implementation uses protocol concepts and independently written logic rather than relicensing the assembled archive.

| Material | Reusable role | Decision / modifications needed |
|---|---|---|
| `code/controlled_benchmark.py` | Synthetic logistic example, fault taxonomy, contradiction-first reduction | Tight coupling to NumPy arrays and local receipt format; incomplete malformed-input handling and registration independence. Used as a behavioral design reference; newly implemented package and fixtures supplied instead. |
| `code/historical_contract_tests.py` | BCE target, optimizer budget and cache-reconstruction fault ideas | Existing script writes to research root and is not a reusable package. Concepts covered by new tests; original not copied. |
| `code/rescore_historical.py` | Tie-aware rank AUC and population-aligned historical scoring | Depends on pandas/SciPy and private dataset-derived exports; not included. New stdlib metric helpers implement documented estimands. No historical rerun performed. |
| `code/verify_historical_updates.py` | Retained optimizer-log verification | Archive-specific paths/log formats; reference only. New contract accepts explicitly exported counters. |
| `code/framework_comparison/` | Existing configured tracker integration feasibility examples | Dependency/host constraints and uncertain assembled-code licensing. Not included or advertised as installed adapters. |
| Manuscript Methods and limitations | POP gates, estimands, decision priority, scientific boundary | Newly written documentation; no paper PDF or figures distributed. |
| Evidence guide / implementation / release notes | Provenance and missing-artifact distinctions | Inspected and summarized in new inventory/reproducibility docs. Stale page/release status not copied. |
| Prior `evidence/controlled/` | Internal five-seed and 16-case records | Not copied. New standard-library example and 16-case tests clearly distinguished. |
| Historical census, predictions, logs and receipts | Existing study evidence | Excluded: ownership/data-access and private path review remain separate work. |
| ForensicHub source snapshot | Research pipeline context | Excluded entirely; external dependency for researchers who need it. |
| Historical validator, per-scope matrix, archive catalog | Original scope validation | Unavailable. Never fabricated or reconstructed. |

## Existing SICA reproduction utilities

Inspected at the recorded external commit; that repository was only read and remains unchanged.

| External path | Useful role | POP relationship / action |
|---|---|---|
| `scripts/dump_sica_predictions.py` | Export image scores with labels and metadata; preserve explicit corrupt-image exclusions | Potential producer for external reconstruction work, not a POP verifier. Requires its original model environment and rights; link only. |
| `scripts/aggregate_sica_metrics.py` | ACC/AUC/AP/F1 and domain/type summaries | Useful reference for label/metric conventions; not a substitute for registered POP weights, content exclusion or identity alignment. Not copied. |
| `scripts/verify_checkpoint.py` | SHA-256 and checkpoint/config inspection | Potential initialization/lineage evidence producer; does not establish realized updates. Uses PyTorch/model dependencies; not copied. |
| `scripts/run_full_eval.sh` | Existing inference orchestration | External workflow only; no GPU evaluation invoked. |
| `configs/sica_train_1gpu.yaml`, `configs/sica_4gpu_smoke.yaml` | SICA training setups | Not POP configurations; retained externally. |
| Evaluation/baseline/corrupt-image protocol documents | Split roles, label conventions, skipped-item reporting | Referenced for integration design; private paths and original text not imported. |

## Licensing boundary

Only newly developed reference code, new prose and newly generated synthetic values are MIT licensed here. No permission to relicense any existing research source, manuscript assets, dataset exports or upstream implementation is inferred. See [reference review](reference_review.md) for observed upstream license signals and commits. Components with uncertain redistribution rights are excluded, so publication does not depend on resolving those components' ownership.

## Author-authorized source adaptations (2026-11-02)

The original release inventory above describes v0.1.1. On the separate evidence-producers branch, the maintainer authorized MIT publication of their original audit utilities/adaptations. The new [source record](source_adaptation.md) supersedes the earlier no-import decision only for those explicitly listed author scripts. Third-party models, original SICA inference code, raw data and private exports remain excluded.
