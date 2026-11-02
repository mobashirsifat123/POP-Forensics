# CPU evidence pipeline

This example connects the newly adapted tools to the original POP verifier:

1. Generate 36 tiny synthetic RGB images and a manifest.
2. Compute strict byte/RGB hashes and training-content exclusions.
3. Register a two-arm comparison before fitting.
4. Atomically publish the intended evaluation input cache.
5. Fit two CPU logistic heads for 40 SGD updates each while collecting live optimizer evidence.
6. Record initial/final trainable tensors and their actual L2 change.
7. Reconstruct predictions through fresh PyTorch models using JSON parameters.
8. Align scores, compute all three estimands and produce a PASS receipt.

Requirements: Python 3.10+, Pillow (`pip install -e '.[images]'`) and a CPU-capable PyTorch environment with optimizer post-step hooks. The tested remote environment uses PyTorch 2.7.1; choose the official PyTorch install suitable for your platform. No SICA, ForensicHub, datasets or weights are imported.

```sh
python examples/evidence_pipeline/run.py output/image-pipeline
popverify verify output/image-pipeline/registration.json output/image-pipeline/evidence.json
```

Use a new destination. All generated data are synthetic. Files under `output/` are ignored by Git. The example is for software integration, not a scientific finding or recovery of historical POP decisions. See [producer guide](../../docs/evidence_producers.md) and [source provenance](../../docs/source_adaptation.md).
