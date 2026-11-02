"""Tie-aware rank AUC and three explicit domain/type estimands."""

from collections import defaultdict
from statistics import mean

from .registration import number


def auc(labels, scores):
    labels, scores = list(labels), list(scores)
    if (
        len(labels) != len(scores)
        or not labels
        or any(type(y) is not int or y not in (0, 1) for y in labels)
    ):
        raise ValueError("equal nonempty vectors and binary integer labels required")
    if not all(number(s) for s in scores):
        raise ValueError("scores must be finite")
    positive = sum(labels)
    negative = len(labels) - positive
    if not positive or not negative:
        raise ValueError("AUC needs both classes")
    ordered = sorted(zip(scores, labels))
    ranks, start = 0.0, 0
    while start < len(ordered):
        end = start + 1
        while end < len(ordered) and ordered[end][0] == ordered[start][0]:
            end += 1
        ranks += ((start + 1 + end) / 2) * sum(y for _, y in ordered[start:end])
        start = end
    return (ranks - positive * (positive + 1) / 2) / (positive * negative)


def estimands(rows, expected_types):
    """Rows have domain/type/label/score; authentic controls are shared per domain.

    expected_types maps every registered domain to its fake-type list. Missing
    cells raise ValueError instead of silently renormalizing the target estimand.
    Returns A_type, A_unif, A_pool and individual type AUCs. No bootstrap is run.
    """
    if not expected_types or any(
        not isinstance(v, list) or not v or len(set(v)) != len(v) for v in expected_types.values()
    ):
        raise ValueError("register nonempty distinct fake types for each domain")
    grouped = defaultdict(list)
    for row in rows:
        if row["domain"] not in expected_types:
            raise ValueError("unregistered domain")
        grouped[row["domain"]].append(row)
    by_type, pooled, balanced = {}, [], []
    for domain, types in expected_types.items():
        group = grouped[domain]
        if {r["type"] for r in group if r["label"] == 1} != set(types):
            raise ValueError(f"missing or unexpected fake types in {domain}")
        values = {}
        for fake_type in types:
            cell = [r for r in group if r["label"] == 0 or r["type"] == fake_type]
            values[fake_type] = auc([r["label"] for r in cell], [r["score"] for r in cell])
        pooled.append(auc([r["label"] for r in group], [r["score"] for r in group]))
        balanced.append(mean(values.values()))
        by_type[domain] = values
    return {
        "A_type": mean(balanced),
        "A_unif": mean(v for d in by_type.values() for v in d.values()),
        "A_pool": mean(pooled),
        "per_type": by_type,
    }
