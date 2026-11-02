"""Identity-aligned cohort scoring adapted from score_cohorts.py.

Unlike the research script, no lab paths, fixed cohort counts or model loading
are embedded here. Missing predictions never silently change the population.
"""

import csv
import hashlib
import json

from ..evidence import sha256
from ..metrics import estimands
from ..registration import number


def predictions(path):
    """Accept public-export IDs (id or path) and probability; reject ambiguity."""
    with open(path, newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        fields = reader.fieldnames
        if not fields or len(set(fields)) != len(fields):
            raise ValueError("missing or duplicated CSV columns")
        identity = "id" if "id" in fields else "path"
        if identity not in fields or "probability" not in fields:
            raise ValueError("prediction CSV requires id (or path) and probability")
        result = {}
        for row in reader:
            key = row[identity]
            if not key or key in result:
                raise ValueError("empty or duplicate prediction identity")
            probability = float(row["probability"])
            if not number(probability) or not 0 <= probability <= 1:
                raise ValueError("probability must be finite and within [0,1]")
            if "label" in row and row["label"] not in ("0", "1"):
                raise ValueError("prediction labels must be 0 or 1")
            result[key] = {
                "score": probability,
                **({"label": int(row["label"])} if "label" in row else {}),
            }
    if not result:
        raise ValueError("empty predictions")
    return result


def cell_weights(expected_types, membership, estimand):
    if estimand not in {"A_type", "A_unif", "A_pool"}:
        raise ValueError("unknown estimand")
    # Validate expected cells and all metadata through the scoring helper first.
    estimands([{**r, "score": 0.5} for r in membership.values()], expected_types)
    domains = len(expected_types)
    types = sum(len(v) for v in expected_types.values())
    weights = {}
    for domain, fake_types in expected_types.items():
        counts = {
            t: sum(
                r["label"] == 1 and r["domain"] == domain and r["type"] == t
                for r in membership.values()
            )
            for t in fake_types
        }
        for fake_type in fake_types:
            # JSON tuple keys avoid collisions when a domain or type contains '/'.
            key = json.dumps([domain, fake_type], separators=(",", ":"))
            weights[key] = (
                1 / domains / len(fake_types)
                if estimand == "A_type"
                else 1 / types
                if estimand == "A_unif"
                else counts[fake_type] / sum(counts.values()) / domains
            )
    return weights


def compare(cohort, baseline_csv, candidate_csv, expected_types):
    membership = cohort["membership"]
    if not isinstance(membership, dict) or not membership:
        raise ValueError("nonempty registered cohort required")
    arms, coverage = {}, {}
    for name, source in (("baseline", baseline_csv), ("candidate", candidate_csv)):
        records = predictions(source)
        missing = set(membership) - records.keys()
        if missing:
            raise ValueError(f"{name}: {len(missing)} cohort predictions missing")
        coverage[name] = {
            "available": len(records),
            "cohort": len(membership),
            "unused": len(records.keys() - membership.keys()),
        }
        aligned = []
        for key, row in membership.items():
            if "label" in records[key] and records[key]["label"] != row["label"]:
                raise ValueError(f"{name}: prediction/cohort label mismatch")
            aligned.append({**row, "score": records[key]["score"]})
        arms[name] = estimands(aligned, expected_types)
    return {
        "n": len(membership),
        "coverage": coverage,
        "scores": arms,
        "delta_pp": {
            k: 100 * (arms["candidate"][k] - arms["baseline"][k])
            for k in ("A_type", "A_unif", "A_pool")
        },
        "input_sha256": {"baseline": sha256(baseline_csv), "candidate": sha256(candidate_csv)},
        "cohort_sha256": hashlib.sha256("\n".join(sorted(membership)).encode()).hexdigest(),
        "interpretation": "fixed-score paired contrast; no seed uncertainty or historical certification",
    }
