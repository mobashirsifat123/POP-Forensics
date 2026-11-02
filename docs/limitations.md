# Limitations

- New reference implementation, not the missing historical validator. Scope-level historical counts remain independently unverified.
- Synthetic cases and tests are authored alongside the implementation; they do not estimate real-world sensitivity, independent effectiveness, cost or superiority over configured existing safeguards.
- No detector, benchmark dataset, pretrained weights, GPU inference/training, image decoder or turnkey ForensicHub/SICA adapter is included.
- Target checks implement a BCE-style probability contract. Other objectives require documented extensions and tests.
- Producer logs, target samples, parameter deltas, content digests and completion records are trusted observations. The software does not measure training itself, prove log completeness, establish preregistration or guarantee historical cache state.
- Reconstruction compares vectors generated externally. It cannot prove that a producer recomputed them independently or used the intended model. Register input/output identities, order, checkpoints and additional digests explicitly.
- Metrics do not implement cluster bootstrap, seed confidence intervals, source-family dependence or automatic identity joins. Constant/tie-aware AUC is supported; missing classes/cells are errors.
- Registrations can be poorly chosen. PASS certifies supplied registered assertions, not scientific truth, generalizability or architectural attribution beyond those assertions.
- JSON vectors and manifests are loaded into memory. Very large studies should export bounded per-cohort scopes or develop a tested streaming adapter. Resource quotas and hostile-filesystem race protection are outside this release.
