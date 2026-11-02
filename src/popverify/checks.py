"""Semantic assertions over explicitly supplied producer evidence.

Producer summaries (updates, dtype, deltas) are trusted records, not replayed training.
Reconstruction compares externally recomputed predictions; it never executes model code.
"""

from .evidence import artifact, sha256, vector
from .registration import number


class InsufficientEvidence(ValueError):
    pass


def _require(condition, message):
    if not condition:
        raise InsufficientEvidence(message)


def check(a, observed, root):
    kind, expected, tol = a["kind"], a["expected"], a.get("tolerance", 0)
    if kind == "membership":
        _require(
            isinstance(observed, dict) and all(isinstance(v, dict) for v in observed.values()),
            "membership must map unique row IDs to metadata",
        )
        return observed == expected, "row membership and registered metadata"
    if kind == "disjoint":
        _require(
            isinstance(observed, dict) and set(observed) == {"train", "evaluation"},
            "disjoint needs train and evaluation content digests",
        )
        _require(
            all(
                isinstance(v, list)
                and all(
                    isinstance(x, str) and len(x) == 64 and all(c in "0123456789abcdef" for c in x)
                    for x in v
                )
                for v in observed.values()
            ),
            "content identities must be SHA-256 lists",
        )
        _require(bool(observed["train"]) and bool(observed["evaluation"]), "empty content registry")
        return not set(observed["train"]) & set(observed["evaluation"]), "content exclusion"
    if kind == "weights":
        _require(
            isinstance(observed, dict) and observed and all(number(v) for v in observed.values()),
            "weights must be a finite numeric mapping",
        )
        return (
            set(observed) == set(expected)
            and all(v >= 0 for v in observed.values())
            and abs(sum(observed.values()) - 1) <= tol + 1e-12
            and all(abs(observed[k] - expected[k]) <= tol for k in expected)
        ), "estimand weights"
    if kind == "targets":
        _require(
            isinstance(observed, dict)
            and {"dtype", "values"} <= set(observed)
            and isinstance(observed["dtype"], str)
            and isinstance(observed["values"], list)
            and bool(observed["values"])
            and all(number(v) for v in observed["values"]),
            "targets need dtype and finite numeric values",
        )
        return (
            observed["dtype"] == expected["dtype"]
            and all(expected["min"] <= v <= expected["max"] for v in observed["values"])
        ), "BCE targets"
    if kind == "updates":
        _require(
            isinstance(observed, dict)
            and {"successful", "skipped", "nonfinite"} <= set(observed)
            and all(
                type(observed[k]) is int and observed[k] >= 0
                for k in ("successful", "skipped", "nonfinite")
            ),
            "invalid optimizer counters",
        )
        return (
            observed["successful"] == expected["successful"]
            and observed["skipped"] <= expected["max_skipped"]
            and observed["nonfinite"] <= expected["max_nonfinite"]
        ), "realized optimizer updates"
    if kind == "parameter_change":
        _require(number(observed), "parameter delta must be finite and numeric")
        return observed >= expected, "minimum parameter L2 change"
    if kind in {"digest", "initialization"}:
        return sha256(artifact(root, observed)) == expected, "artifact SHA-256"
    if kind == "completion":
        _require(type(observed) is bool, "completion evidence must be boolean")
        return observed, "producer cache-completion record"
    if kind == "reconstruction":
        saved, reconstructed = vector(root, expected), vector(root, observed)
        return (
            len(saved) == len(reconstructed)
            and all(abs(x - y) <= tol for x, y in zip(saved, reconstructed))
        ), "prediction reconstruction"
    if kind == "lineage":
        _require(
            isinstance(observed, list)
            and bool(observed)
            and all(isinstance(v, str) and bool(v) for v in observed),
            "replicate identities missing",
        )
        return len(set(observed)) == len(observed), "distinct replicate identities"
    if kind == "attribution":
        _require(
            isinstance(observed, list) and all(isinstance(v, str) for v in observed),
            "changed-factor list missing",
        )
        if len(observed) != expected:
            raise InsufficientEvidence("single-factor attribution is not established")
        return True, "single registered changed factor"
    raise ValueError(f"unsupported check: {kind}")
