# O · Objective and realized optimization

**Was the intended training actually realized?**

A configured epoch count is not evidence that optimizer updates occurred. O connects the registered optimization requirements to observations from both comparison arms.

## Checks required for each arm

| Check | What the producer supplies |
|---|---|
| `targets` | Observed probability targets and dtype for the supported BCE-style contract |
| `updates` | Successful post-scaler optimizer calls, skipped calls and nonfinite-loss counts |
| `parameter_change` | Observed trainable-parameter L2 delta |
| `initialization` | Path to initial parameters, checked against the registered SHA-256 |

Use additional `digest` assertions to bind retained logs and checkpoints. Optional `lineage` assertions detect duplicate replicate identities. An optional `attribution` assertion leaves single-factor attribution unresolved when the recorded list contains more or fewer than one changed factor.

## Interpret the evidence

A finite probability target outside registered bounds, an incorrect successful-update count or an insufficient parameter delta is a contradiction. Missing counters or unusable records leave an assertion unresolved. See [decision rules](../decision_rules.md).

The software does not instrument a trainer, run a gradient scaler, calculate the observed parameter delta or establish the truthfulness/completeness of training logs. The supported objective contract is BCE-oriented; other loss semantics require a documented extension.
