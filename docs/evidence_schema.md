# Version 1 evidence contract

Registration is strict JSON with `schema_version: 1`, nonempty `scope`, two distinct `arms` and a nonempty `assertions` list. Unknown top-level registration fields and assertion fields are rejected. Each assertion has `id` (unique), `gate` (`P1`, `O`, `P2`), `kind`, `evidence` (top-level evidence key), `expected` and optional nonnegative finite `tolerance` (default 0). Arm-specific kinds also require `arm` matching one of the two registered names. All assertions are required.

Evidence is an object mapping evidence keys to observations. Missing keys and unusable records produce UNRESOLVED for their assertions. A usable observation outside its registered requirement produces FAIL. Invalid registrations issue an error rather than a scientific outcome. Extra evidence keys are ignored; duplicate JSON keys and nonstandard NaN/Infinity literals are rejected.

| Kind | Gate | Expected | Observed evidence |
|---|---|---|---|
| membership | P1 | Nonempty mapping of row IDs to label/split metadata objects | Same mapping; any difference fails |
| disjoint | P1 | `true` | `{"train": [sha256, ...], "evaluation": [sha256, ...]}`; nonempty registries with no intersection |
| weights | P1 | Nonnegative cell-weight mapping summing to 1 | Same keys and weights within absolute tolerance; observed weights must be nonnegative and sum to 1 |
| targets | O, per arm | `{"dtype": "float32", "min": 0, "max": 1}` | `{"dtype": "float32", "values": [0, 0.9, 1]}`; bounds and dtype checked |
| updates | O, per arm | `{"successful": 80, "max_skipped": 0, "max_nonfinite": 0}` | `{"successful": 80, "skipped": 0, "nonfinite": 0}`; successful count exact, others bounded |
| parameter_change | O, per arm | Positive minimum L2 delta | Finite observed L2 delta; must meet minimum |
| initialization | O, per arm | Lowercase SHA-256 | Relative path to initial-parameter artifact |
| completion | P2 | `true` | Producer boolean; false is a contradiction, absent is unresolved |
| digest | P2 | Lowercase SHA-256 | Relative path to cache or other artifact |
| reconstruction | P2, per arm | Relative saved-prediction JSON path | Relative reconstructed-prediction JSON path; finite numeric vectors, same length, absolute tolerance |
| lineage | Any gate, optional | `true` | Nonempty replicate-identity list; duplicates contradict distinct replication |
| attribution | Any gate, optional | `1` | Changed-factor string list; other lengths leave single-factor attribution unresolved |

Every required kind in each gate must be registered. `targets`, `updates`, `parameter_change`, `initialization` and `reconstruction` must each appear for both arms. Add multiple assertions for split content registries, separate caches, seed scopes and artifact digests as needed. A single digest assertion does not discover or authenticate every file automatically.

Content registries use digests supplied by the producer. Membership metadata can hold label, split, domain, manipulation type and ordering information; it is compared as registered, without guessing field meanings. This permits study-specific schemas, but registering only IDs cannot certify labels. The sample package includes labels and split membership. Register selection exposure and cohort exclusions explicitly through their membership/content records.

All artifact paths resolve relative to the evidence JSON's parent. Absolute paths, `..` escapes and escaping symlinks are rejected as unusable evidence. No network requests, imports, pickle deserialization or shell commands are executed. Restrict local file access and package size independently when handling untrusted evidence; no resource quotas or sandbox are provided.

Receipts contain schema/implementation version, scope, aggregate and gate outcomes, assertion IDs/kinds/reasons, SHA-256 of input documents and artifacts examined by digest/initialization/reconstruction assertions. Files and observations can change during verification: keep evidence immutable and use externally retained receipts. The verifier is not a transactional or adversarial filesystem attestation service.
