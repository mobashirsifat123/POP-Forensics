# Registration schema

A registration declares one comparison before fitting or selection. Preserve an external timestamp or version-control commit: the JSON file alone does not establish preregistration.

Version 1 requires exactly four top-level fields:

```json
{
  "schema_version": 1,
  "scope": "synthetic feature-count comparison",
  "arms": ["baseline", "candidate"],
  "assertions": []
}
```

This block shows the **shape only**; an empty assertion list is invalid. Use the complete, runnable [synthetic registration](https://github.com/mobashirsifat123/POP-Forensics/blob/main/examples/synthetic/package/registration.json) as a concrete example, then register your own requirements.

Each assertion has a unique `id`, `gate`, `kind`, evidence-record key and expected value. Optional `tolerance` is finite and nonnegative. Arm-specific checks must identify a registered `arm`.

All assertions are required. A valid contract covers all three gates and the required optimization/reconstruction checks for both arms. Unknown fields, duplicate IDs, unsupported versions, invalid expectations and incomplete coverage are rejected before a scientific decision is issued.

```sh
popverify validate examples/synthetic/package/registration.json
```

The [canonical version-1 contract](evidence_schema.md) defines the field semantics and required kinds. It is the shared source for registration and evidence expectations.
