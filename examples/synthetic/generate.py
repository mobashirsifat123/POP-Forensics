"""Generate a tiny, deterministic CPU comparison; no historical files are read.

Run from repository root: python examples/synthetic/generate.py output/demo
Registration is written before fitting. This is a new example, not the paper's
five-seed NumPy experiment or its original internal checker.
"""

import hashlib
import json
import math
from pathlib import Path
import random
import sys


def write(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def generate(root):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=False)
    rng = random.Random(810)
    features = [[rng.uniform(-1, 1) for _ in range(2)] for _ in range(48)]
    labels = [int(x[0] + x[1] > 0) for x in features]
    train, test = features[:32], features[32:]
    content = [hashlib.sha256(json.dumps(x).encode()).hexdigest() for x in features]
    membership = {
        f"sample-{i}": {"label": labels[i + 32], "split": "evaluation"} for i in range(16)
    }
    evidence = {
        "membership": membership,
        "content": {"train": content[:32], "evaluation": content[32:]},
        "weights": {"synthetic/type-1": 1.0},
        "complete": True,
        "cache": "cache.json",
        "replicates": ["synthetic-seed-101"],
        "factors": ["feature_count"],
    }
    assertions = []

    def add(key, gate, kind, expected, arm=None, tolerance=0):
        a = {
            "id": key,
            "gate": gate,
            "kind": kind,
            "evidence": key,
            "expected": expected,
            "tolerance": tolerance,
        }
        if arm:
            a["arm"] = arm
        assertions.append(a)

    add("membership", "P1", "membership", membership)
    add("content", "P1", "disjoint", True)
    add("weights", "P1", "weights", evidence["weights"])
    write(root / "cache.json", test)
    add("complete", "P2", "completion", True)
    add("cache", "P2", "digest", digest(root / "cache.json"))
    add("replicates", "O", "lineage", True)
    add("factors", "O", "attribution", 1)
    for arm in ("baseline", "candidate"):
        write(root / f"{arm}-initial.json", [0.0, 0.0])
        for suffix, kind, expected in [
            ("targets", "targets", {"dtype": "float64", "min": 0, "max": 1}),
            ("updates", "updates", {"successful": 40, "max_skipped": 0, "max_nonfinite": 0}),
            ("delta", "parameter_change", 0.001),
            ("initial", "initialization", digest(root / f"{arm}-initial.json")),
            ("reconstruction", "reconstruction", f"{arm}-predictions.json"),
        ]:
            add(
                f"{arm}-{suffix}",
                "P2" if kind == "reconstruction" else "O",
                kind,
                expected,
                arm,
                1e-12 if kind == "reconstruction" else 0,
            )
    write(
        root / "registration.json",
        {
            "schema_version": 1,
            "scope": "synthetic feature-count comparison",
            "arms": ["baseline", "candidate"],
            "assertions": assertions,
        },
    )
    for arm, count in (("baseline", 1), ("candidate", 2)):
        weights = [0.0, 0.0]
        log = []
        for _ in range(40):
            probs = [
                1 / (1 + math.exp(-sum(x[j] * weights[j] for j in range(count)))) for x in train
            ]
            for j in range(count):
                weights[j] -= (
                    0.1 * sum((p - y) * x[j] for p, y, x in zip(probs, labels, train)) / 32
                )
            log.append({"successful": len(log) + 1, "skipped": 0, "nonfinite": 0})
        write(root / f"{arm}-final.json", weights)
        write(root / f"{arm}-log.json", log)
        predictions = [
            1 / (1 + math.exp(-sum(x[j] * weights[j] for j in range(count)))) for x in test
        ]
        write(root / f"{arm}-predictions.json", predictions)
        # Independent read-back of completed inputs and final parameters.
        cache = json.loads((root / "cache.json").read_text())
        final = json.loads((root / f"{arm}-final.json").read_text())
        reconstructed = [
            1 / (1 + math.exp(-sum(x[j] * final[j] for j in range(count)))) for x in cache
        ]
        write(root / f"{arm}-reconstructed.json", reconstructed)
        evidence.update(
            {
                f"{arm}-targets": {"dtype": "float64", "values": labels[:32]},
                f"{arm}-updates": log[-1],
                f"{arm}-delta": math.sqrt(sum(v * v for v in weights)),
                f"{arm}-initial": f"{arm}-initial.json",
                f"{arm}-reconstruction": f"{arm}-reconstructed.json",
            }
        )
    write(root / "evidence.json", evidence)
    return root


if __name__ == "__main__":
    generate(sys.argv[1])
