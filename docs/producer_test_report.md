# Evidence-producer verification report

Date: 2026-11-02. Branch: `evidence-producers`. These are code/integration checks, not a new detector experiment, model ranking or independent POP-effectiveness study.

| Environment/check | Result | Scope |
|---|---|---|
| Local macOS, Python 3.14.3, Pillow image extra | PASS | 29 test methods: 27 passed, 2 optional PyTorch tests skipped because PyTorch is not installed locally |
| pro6000 isolated temporary directory, Python 3.10, PyTorch 2.7.1+cu128, Pillow 12.2.0 | PASS | All 29 test methods, including actual optimizer hooks and an actual CPU GradScaler skip; CUDA devices disabled |
| CPU image/training/reconstruction pipeline | PASS | 36 generated images, 12 evaluation rows, 40 SGD updates per arm, all three POP gates accepted |
| Existing verifier tests | PASS | All 12 original test methods retained without changes, including 16 conformance subcases |
| Image/population fault cases | PASS | Re-encoded RGB duplicate, byte duplicate, corrupt image, strict/permissive setting, escaping paths and incomplete training registry |
| Paired scoring | PASS | Reordered rows aligned by ID; missing rows rejected; type-balanced and pooled effects have opposite signs in a synthetic fixture |
| Optimization | PASS | Actual steps versus attempts, missing attempts, nonfinite losses/targets, parameter identity/shape validation and hook removal |
| Cache/reconstruction | PASS | Interrupted publication cleanup, overwrite refusal, missing/changed cache bytes, stable fingerprint checks, identity mismatch and four mixed reconstruction classes |
| Lint and formatting | PASS | Ruff across repository Python code and documented Python snippets |
| Distribution | PASS | Package build includes producer modules and example in the source archive; no new public release created |

The first remote run exposed a test-fixture issue: a same-size rewrite can preserve observed metadata at filesystem timestamp resolution. The fixture now changes size deterministically. Fingerprinting only claims detection when the observed stat signature changes; it is not an adversarial filesystem attestation. The second attempted fixture edit did not match the formatted source; that was corrected before the successful full rerun. No unresolved test failure remains.

All remote code execution used a new temporary directory, the existing Python environment and CPU-only synthetic inputs. The main SICA/OpenMMSec source, reproduction repository, research outputs, model checkpoints and GPU jobs were not modified. Source scripts were copied out for inspection and adaptation with author permission; no third-party implementation, data or weights were published.

A dedicated GitHub Actions job installs CPU PyTorch and the image extra, runs the full suite and complete integration example. The original Python matrix still exercises minimal-runtime compatibility; optional integration tests are explicitly skipped there when those extras are absent. Consult the branch/PR checks for the latest hosted status.
