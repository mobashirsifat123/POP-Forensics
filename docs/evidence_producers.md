# Evidence producers from the SICA audit workflow

This branch adds working evidence-generation tools adapted from the maintainer's project on `pro6000`. See the [source record](source_adaptation.md). They complement `popverify verify`: producer commands emit measurements or diagnostics, not aggregate PASS/FAIL/UNRESOLVED decisions.

The original `popverify` CLI is unchanged. Invoke these tools with:

```sh
python -m popverify.producers.cli --help
```

Install `python -m pip install -e '.[images]'` for the optional Pillow image census. Everything except image decoding and the optional PyTorch example uses the standard library. PyTorch is supplied by your training environment; it is not a mandatory package dependency.

## P1: native manifests, content census and exclusions

Native SICA JSON lists use `path`, binary integer `label`, `domain` and `mani_type` for fake images. Convert them explicitly; no automatic private-path prefix rewriting is performed:

```sh
python -m popverify.producers.cli sica-manifests DATASET_ROOT \
  --split train=TRAIN_JSON --split evaluation=EVALUATION_JSON \
  --output portable-manifest.json
python -m popverify.producers.cli census portable-manifest.json DATASET_ROOT \
  --output census.json
python -m popverify.producers.cli cohort census.json \
  --train-split train --evaluation-split evaluation --output cohort.json
```

Uppercase arguments are your local inputs; they are not bundled datasets. New output files and their parents must be available. Commands refuse overwrite. For portable direct manifests the format is a nonempty JSON list:

```json
[{"id":"sample-1","path":"images/one.png","label":1,"split":"evaluation","domain":"Doc","type":"AIGC"}]
```

Native conversion assigns stable split-scoped IDs using SHA-256 of relative path text. These identify observations; they are distinct from content hashes. Repeated paths in different splits remain separate observations so the census can detect leakage. Paths are relative to the declared image root and cannot escape via traversal or symlinks. Treat relative paths as potentially identifying data when publishing manifests.

Census performs strict Pillow decoding, stores byte and decoded-RGB SHA-256, dimensions, decode status and error/warning categories. The decoded convention matches the audit: `SHA256(b"RGB:<width>:<height>:" + RGB bytes)`, no EXIF transpose. Permissive `LOAD_TRUNCATED_IMAGES` settings are refused. Census outputs omit image paths. Corrupt/missing evaluation files remain explicit excluded records; incomplete training registries abort exclusion instead of implying disjointness.

`cohort` returns exact row/label/split/domain/type membership, excluded IDs/reasons, train/evaluation byte and RGB registries and a cohort identity hash. It excludes undecodable evaluation rows and training byte/RGB matches. Perceptual families, near duplicates and source dependence are not inferred. Repeat `--train-split` to include selection exposure as a separately declared sensitivity cohort.

## Identity-aligned paired rescoring

Convert each native prediction export using the same root and split name as the manifest:

```sh
python -m popverify.producers.cli sica-predictions NATIVE_BASELINE_CSV DATASET_ROOT \
  --split evaluation --output baseline.csv
python -m popverify.producers.cli sica-predictions NATIVE_CANDIDATE_CSV DATASET_ROOT \
  --split evaluation --output candidate.csv
python -m popverify.producers.cli score cohort.json baseline.csv candidate.csv \
  expected-types.json --output score.json
```

The type contract is `{"Doc": ["AIGC", "edited"]}` (replace with your registered domains/types). A prediction CSV has `id,probability` and optional binary `label`; path identity is also accepted for direct comparisons. Both arms must cover the entire explicit cohort. Extra predictions are counted but unused; missing rows, duplicate IDs, mismatched labels and invalid probabilities abort. No intersection silently changes the population. Shared authentic controls per domain define `A_type`, `A_unif` and `A_pool`; reports include paired percentage-point differences, coverage and input digests. No seed/cluster uncertainty or model superiority is inferred.

`cell_weights(expected_types, membership, estimand)` exports the numeric map used by each aggregation. Keys encode `[domain,type]` as JSON strings to avoid separator collisions. Bind this observed map to independently registered expectations, not expectations chosen after inspecting outcomes.

## O: live optimization records

Use an actual optimizer post-step hook rather than a configured epoch budget:

```python
from popverify.producers.optimization import UpdateTracker

with UpdateTracker(optimizer) as tracker:
    # Inside your real training loop:
    tracker.targets(target_tensor, "float32")
    tracker.loss(loss)
    loss.backward()
    tracker.attempt()  # immediately before optimizer.step or scaler.step
    optimizer.step()
    observed = tracker.evidence()
```

For AMP call `tracker.attempt()` before `scaler.step(optimizer)`, then `scaler.update()` as usual. The post-step hook records actual optimizer calls; an attempted scaler step which never calls the optimizer contributes to the skipped count. Microbatch loss observations and optimizer attempts are distinct counts. Nonfinite-loss branches that never reach an update boundary must still be observed with `loss()`. The tracker does not decide when to skip or alter training. Test coverage includes an actual CPU GradScaler skip.

For tensor targets the supplied dtype must match the observed tensor dtype. Finite values outside [0,1] remain in evidence and can contradict the verifier's contract. Nonfinite values cannot be valid JSON numbers: the target record is omitted and explicit diagnostics retained, leaving that assertion unresolved rather than pretending it passed. Interpret diagnostic contradictions through scientific review or separately registered checks.

`parameter_snapshot(model)` copies finite trainable tensors to CPU JSON records; `parameter_delta(initial, final)` computes L2 change with matching identities/shapes. Save initial bytes before fitting and bind their digest independently. The tracker retains target observations in memory and snapshots copy trainable parameters; overhead depends on model scale. One tracker is per optimizer/rank; distributed reduction, trainer selection and coverage integrity are external responsibilities.

## Read retained training logs

```sh
python -m popverify.producers.cli training-log log.txt \
  --epoch 2 --epoch 3 --output training-observations.json
```

This understands the original `epoch`, `train_actual_optimizer_steps`, `train_nonfinite_steps` and `train_nominal_accumulation_boundaries` fields. Requested epochs/counters must be present for totals. It reports an unexplained boundary gap, not a fabricated GradScaler cause. It does not recover unrecorded initialization or lost checkpoints.

## P2: committed caches and reconstruction

```sh
python -m popverify.producers.cli publish-cache new-cache FEATURES_FILE \
  --output publication.json
python -m popverify.producers.cli inspect-cache new-cache --output inspection.json
python -m popverify.producers.cli reconstruction saved.csv rerun.csv \
  --tolerance 0.00001 --output reconstruction.json
```

Publication stages file bytes, fsyncs them, records fingerprints in `COMMIT.json` and renames the complete directory into place. It refuses existing destinations and serializes cooperating publishers with a sibling lock. Inspection verifies listed bytes, missing files and unexpected files. Missing completion is `null`; contradicted content is `false`. Bind a separately retained commit digest in the registration: a self-consistent edited commit cannot authenticate itself.

A stale cooperative lock after process death requires manual inspection/removal. Publication is local filesystem evidence management, not a transaction across network services or protection against a hostile concurrent filesystem. Stable-stat fingerprints detect observed changes; mutations preserving all metadata cannot be ruled out. File existence and shape alone are never called proof of completion.

Reconstruction compares identity-aligned saved and independently produced CSV scores with an explicit absolute tolerance. It exports vectors in a shared order for the existing verifier and measures residuals. It never invokes the model. Add `--alternative ZERO_PATCH_OR_OTHER_CSV` to classify each row as complete-only, alternative-only, both or neither. These are numerical signatures, not proof of a historical race or per-row cache-read timestamp.

## Run all gates together on CPU

With a CPU-capable PyTorch installed in your environment:

```sh
python -m pip install -e '.[images]'
python examples/evidence_pipeline/run.py output/image-pipeline
popverify verify output/image-pipeline/registration.json \
  output/image-pipeline/evidence.json
```

The example generates 36 original tiny images, derives a clean 12-row evaluation cohort, freezes registration before fitting, performs 40 actual SGD updates per arm, publishes the intended input cache, reconstructs predictions using fresh models loaded from non-executable JSON tensors, scores both arms and verifies the resulting evidence. It is a new synthetic integration fixture, not a detector, independent validation or repetition of the historical research. Output directories must be new. No GPU or external weights/data are used.
