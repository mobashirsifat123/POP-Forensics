# P2 · Prediction provenance

**Were predictions made from the intended inputs?**

P2 connects input publication and artifact integrity to saved predictions. A feature file's existence is insufficient evidence that the producer finished writing it.

## Publish, record, reconstruct

1. Write a cache to a temporary file and atomically publish the completed artifact.
2. Retain the completion record and register the expected digest.
3. Independently rerun the model from the intended complete inputs.
4. Export saved and reconstructed finite prediction vectors in the same registered row order.
5. Check the vectors with an explicit absolute tolerance.

The implementation supports `completion`, `digest` and per-arm `reconstruction` assertions. An explicit false completion record is FAIL; an absent record is UNRESOLVED. A measured digest mismatch or prediction residual outside tolerance is FAIL.

## What POP reads

Artifacts are local paths relative to the evidence JSON. Escaping paths and symlinks are rejected. Reconstruction vectors are numeric JSON lists with equal lengths; no model is loaded or executed. Additional artifacts are authenticated only when explicitly registered.

A producer boolean does not prove historical cache state, and a matching vector does not establish an independent rerun. Retain trustworthy producer records and checkpoint/input identities. See [evidence schema](../evidence_schema.md), [integration guide](../integration.md) and [limitations](../limitations.md).
