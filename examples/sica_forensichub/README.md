# Applying POP around SICA / ForensicHub

This is an integration contract, not a runnable detector adapter. No external code, models or data are bundled. Obtain permissions and install the original project in a separate environment:

- [ForensicHub](https://github.com/scu-zjz/ForensicHub)
- [SICA/OpenMMSec](https://github.com/venus-guangjian/SICA_OpenMMSec)
- [Existing reproduction repository](https://github.com/mobashirsifat123/Strarting_case_for_ForensicHub_by_SICA)

Before fitting, register baseline/candidate arms, selected epoch policy and the intended row/label/domain/type population. Export byte and decoded-RGB content registries for training, selection and evaluation; apply exclusions before scoring. Register the desired domain/type weight map.

Instrument each arm's post-scaler optimizer calls, skipped/nonfinite losses, target dtype and values, initialization bytes and actual trainable-parameter delta. Summarizing a declared epoch budget is insufficient. Save and authenticate raw logs with additional digest assertions.

Produce caches under a temporary name and atomically replace the final file only after writing completes. Record completion and final digest. Evaluate saved and independently rerun predictions from completed inputs in exactly the same registered row order. Export finite score vectors as JSON for this version's reconstruction check. Keep raw restricted images and private filesystem paths outside public evidence.

Translate those observations into [version-1 records](https://github.com/mobashirsifat123/POP-Forensics/blob/main/docs/evidence_schema.md) and run:

```sh
popverify verify your-registration.json your-evidence/evidence.json --json
```

The command works once you supply records in that schema. It does not discover SICA exports, infer ForensicHub configuration semantics, invoke a model or reproduce the historical archive. Unrecorded historical events remain UNRESOLVED; newly instrumented runs are new evidence.
