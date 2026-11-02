# SICA project source adaptation record

The maintainer explicitly authorized publishing their original POP audit/utility scripts and adaptations under the POP-Forensics MIT license on 2026-11-02. This permission excludes third-party SICA/ForensicHub implementation, datasets, weights and private exports.

Sources were read over SSH from the main SICA/OpenMMSec project on `pro6000`. The project container is not itself a Git repository, so source-file SHA-256 values identify the inspected bytes. Source paths below are relative to that project. Remote originals were not edited. Downloads for inspection were kept outside this repository. No historical predictions or raw research data were copied into Git.

| Original source | Adaptation in this repository |
|---|---|
| `paper_submission_audit_20261019/execution/phase1_cpu.py` | `producers/population.py`: strict image reads, byte hashes, dimension-prefixed decoded-RGB hashes, content-excluded cohorts. Removed fixed splits/counts, lab paths, permissive retries, pHash and statistics dependencies. |
| `paper_submission_audit_20261019/execution/add_numeric_counters.py` | `producers/optimization.py`: live optimizer post-step hook and numeric diagnostics as a reusable context manager instead of patching an external trainer's source strings. |
| `paper_submission_audit_20261019/execution/fingerprint_cached_inputs.py` | `producers/provenance.py`: stable streamed fingerprints; generalized publication and committed-byte validation. Atomic publication is new corrective implementation, not recovered historical behavior. |
| `paper_submission_audit_20261019/execution/score_cohorts.py` | `producers/scoring.py`: fixed-cohort identity alignment, explicit population coverage and paired contrasts under the three estimands. Removed model/checkpoint loading and silent cross-model intersections. |
| `paper_submission_audit_20261019/execution/verify_training_stagnation.py` | `producers/logs.py`: retained DE3 JSONL optimizer counters with explicit epoch coverage. Missing records remain missing; no checkpoint pickle load or inferred scaler cause. |
| `paper_submission_audit_20261019/scripts/analyze_existing.py` | Inspected for the scoring and population conventions; no broad analysis/report builder imported. |
| `Strarting_case_for_ForensicHub_by_SICA/scripts/aggregate_sica_metrics.py` | Inspected for native CSV column and label conventions. `producers/sica.py` exports stable split-scoped IDs and drops private paths; original aggregation script remains unchanged. |

Exact source hashes and byte sizes are in [source_adaptation.json](source_adaptation.json). These are adaptation provenance, not claims that the historical experiment is reproducible or that all recovered files match earlier execution bytes. The original historical POP validator, 58-scope matrix and archive catalog remain unavailable. None was fabricated or reconstructed.

New glue includes the producer CLI, native SICA converters, safe output helpers, cache publication, fault tests and a CPU image/training/reconstruction integration example. The old verifier CLI and decision semantics are preserved. These producer tools collect/compare evidence; they do not automatically establish complete training coverage or scientific validity.

## Additional paper-specific entry points

The original controlled conformance benchmark and historical prediction/optimizer-log verification scripts from the local paper collection are included under `scripts/historical/`. They were formatted and changed to require explicit input/output locations; hard-coded lab path substitution is now an opt-in pair of prefix arguments. They retain original research computations and read only user-supplied historical exports. Their original SHA-256 hashes are recorded in `historical_analysis_sources` in [source_adaptation.json](source_adaptation.json). See [historical analysis](historical_analysis.md).
