# P1 · Population and estimand

**Which observations and weights define the claim?**

P1 binds evaluation membership and weighting to the registered comparison. A pooled score and a type-balanced score can describe different questions, even when computed from the same predictions.

## Evidence to retain

- A mapping from row identifiers to registered labels, splits and relevant domain/type metadata.
- Nonempty training and evaluation content registries after the intended exclusions. For images, use separate byte-SHA-256 and decoded-RGB-SHA-256 assertions.
- A registered map of evaluation-cell weights and the weights actually used by the producer.

Use `membership`, `disjoint` and `weights` assertions in the [evidence schema](../evidence_schema.md). Membership must match exactly. An overlap contradicts disjointness; absent or unusable registries leave that assertion unresolved. Numeric weights must match within the registered tolerance.

## Choose the estimand explicitly

`popverify.metrics.estimands` supplies three helpers: domain-balanced type averages (`A_type`), a uniform mean across all types (`A_unif`) and the mean of pooled within-domain AUCs (`A_pool`). The authentic controls are shared within each domain. Missing required domains/types are errors, not a reason to silently renormalize.

The verifier checks the supplied weight record. It does not automatically run these metric helpers, decode images, discover near-duplicate families, align rows or apply exclusions. Those are producer responsibilities. Register separate selection/exclusion cohorts where needed.

[See the complete methodology](../methodology.md) and [Python API](../api.md).
