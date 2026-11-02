# Python API

## Verify a registered comparison

```python
from popverify import verify

receipt = verify(
    "examples/synthetic/package/registration.json",
    "examples/synthetic/package/evidence.json",
)
assert receipt["outcome"] == "PASS"
print(receipt["gates"])
```

`verify(registration, evidence)` accepts filesystem paths and returns a JSON-serializable dictionary. It evaluates all assertions, then reduces their outcomes with contradiction-first priority. Invalid registrations raise `ValueError` (including `RegistrationError`); inaccessible registration paths can raise `OSError`. Missing/malformed evidence produces UNRESOLVED assertions. The [evidence schema](evidence_schema.md) describes receipt fields.

## Rank AUC

```python
from popverify.metrics import auc

assert auc([0, 1], [0.2, 0.8]) == 1.0
assert auc([0, 1], [0.5, 0.5]) == 0.5
```

Labels must be binary integers, scores finite, and both classes present. Ties receive average ranks.

## Explicit estimands

```python
from popverify.metrics import estimands

rows = [
    {"domain": "document", "type": "real", "label": 0, "score": 0.2},
    {"domain": "document", "type": "edited", "label": 1, "score": 0.8},
]
scores = estimands(rows, {"document": ["edited"]})
assert scores["A_type"] == scores["A_unif"] == scores["A_pool"] == 1.0
```

`estimands(rows, expected_types)` requires every registered domain and fake type, sharing authentic controls per domain. It returns `A_type`, `A_unif`, `A_pool` and `per_type`. These are independent helpers: running `verify` does not automatically score predictions, validate their identity order or calculate confidence intervals.
