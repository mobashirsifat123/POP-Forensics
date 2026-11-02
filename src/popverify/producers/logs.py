"""Read retained DE3/ForensicHub JSONL counters without loading checkpoints.

Adapted from verify_training_stagnation.py. A nominal boundary minus a recorded
call is an unexplained gap, not independently proven GradScaler backoff.
"""

import json

from ..evidence import sha256


def summarize_training_log(path, epochs):
    if (
        not epochs
        or any(type(e) is not int or e < 0 for e in epochs)
        or len(set(epochs)) != len(epochs)
    ):
        raise ValueError("explicit distinct nonnegative epochs required")
    rows = {}
    with open(path, encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            row = json.loads(line)
            epoch = row.get("epoch")
            if type(epoch) is not int or epoch < 0 or epoch in rows:
                raise ValueError("missing, invalid or duplicated epoch")
            rows[epoch] = row
    required = {
        "successful": "train_actual_optimizer_steps",
        "nonfinite_microbatches": "train_nonfinite_steps",
        "nominal_boundaries": "train_nominal_accumulation_boundaries",
    }
    missing = []
    observed = {}
    for epoch in epochs:
        if epoch not in rows:
            missing.append(f"epoch:{epoch}")
            continue
        summary = {}
        for key, field in required.items():
            value = rows[epoch].get(field)
            if value is None:
                missing.append(f"epoch:{epoch}:{field}")
            elif type(value) is not int or value < 0:
                raise ValueError(f"invalid counter in epoch {epoch}: {field}")
            else:
                summary[key] = value
        observed[str(epoch)] = summary
    totals = None
    if not missing:
        totals = {key: sum(v[key] for v in observed.values()) for key in required}
        if totals["successful"] > totals["nominal_boundaries"]:
            raise ValueError("successful updates exceed nominal accumulation boundaries")
        totals["unexplained_boundary_gap"] = totals["nominal_boundaries"] - totals["successful"]
    return {
        "input_sha256": sha256(path),
        "requested_epochs": epochs,
        "epochs": observed,
        "missing": missing,
        "totals": totals,
        "interpretation": "retained log observations; boundary gaps do not identify their cause",
    }
