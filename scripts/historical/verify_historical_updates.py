"""CPU only: read original nine-run JSONL logs and initialization receipts."""

import json
import hashlib
import argparse
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--root", type=Path, required=True)
args = ap.parse_args()
root = args.root / "paper_submission_audit_20261019/execution/checkpoints"
out = {}
for seed in [42, 43, 44]:
    arms = {}
    for arm in ["buggy", "loss_fixed", "no_preservation"]:
        p = root / f"{arm}_s{seed}"
        logs = [json.loads(x) for x in (p / "log.txt").read_text().splitlines() if x.strip()]
        init = json.loads((p / "initialization.json").read_text())
        base = json.loads((p / "frozen_base_verification.json").read_text())
        assert [x["epoch"] for x in logs] == list(range(10))
        counts = [x["train_actual_optimizer_steps"] for x in logs]
        arms[arm] = {
            "source": str(p),
            "log_sha256": hashlib.sha256((p / "log.txt").read_bytes()).hexdigest(),
            "updates": counts,
            "post_warmup_updates": sum(counts[2:]),
            "nonfinite_steps": sum(x["train_nonfinite_steps"] for x in logs),
            "initialization": init,
            "base_receipt": base,
            "data_signatures": [x["train_data_signature"] for x in logs],
        }
    paired = {
        k: len({a["initialization"][k] for a in arms.values()}) == 1
        for k in [
            "trainable_initial_sha256",
            "base_initial_sha256",
            "torch_rng_sha256",
            "numpy_rng_sha256",
            "python_rng_sha256",
        ]
    }
    paired["realized_data_signatures_equal"] = (
        len({tuple(a["data_signatures"]) for a in arms.values()}) == 1
    )
    out[str(seed)] = {"arms": arms, "pairing": paired}
print(json.dumps(out, indent=2))
