"""CPU-only independent re-scoring of pre-existing exports; no model calls.
Pass --root to the directory containing the retained historical evidence.
Only stdout is written. Pixel/byte hashes are trusted saved census measurements,
not a new decode or image-content census. Paths of inputs and their SHA256 are emitted.
"""

import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import rankdata, t

ap = argparse.ArgumentParser()
ap.add_argument("--root", required=True)
ap.add_argument("--path-prefix-from")
ap.add_argument("--path-prefix-to")
args = ap.parse_args()

if (args.path_prefix_from is None) != (args.path_prefix_to is None):
    ap.error("--path-prefix-from and --path-prefix-to must be supplied together")
root = Path(args.root)
work = root / "paper_submission_audit_20261019"
aud = work / "execution/audits"
receipts = []


def read(p):
    p = Path(p)
    receipts.append({"path": str(p), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()})
    return pd.read_parquet(p) if p.suffix == ".parquet" else pd.read_csv(p, keep_default_na=False)


def auc(y, s):
    y = np.asarray(y, dtype=int)
    s = np.asarray(s, float)
    assert np.isfinite(s).all()
    n = int(y.sum())
    m = len(y) - n
    assert n * m > 0
    return float((rankdata(s)[y == 1].sum() - n * (n + 1) / 2) / (n * m))


def normalize(d):
    d = d.copy()
    if args.path_prefix_from is not None:
        d.path = d.path.str.replace(args.path_prefix_from, args.path_prefix_to, regex=False)
    assert d.path.is_unique
    if "prob" in d:
        d = d.rename(columns={"prob": "probability"})
    return d.set_index("path", drop=False)


c = read(aud / "manifest_image_census.parquet")
assert c.path.is_unique
tr = c[c.split.eq("train")]
od = c[~c.split.isin(["train", "id_test"])]
strict = od[od.strict_ok]
train_bytes = set(tr.sha256.dropna()) - {""}
train_pixels = set(tr.rgb_sha256.dropna()) - {""}
bm = strict.sha256.isin(train_bytes)
pm = strict.rgb_sha256.isin(train_pixels)
flags = read(aud / "final_duplicate_flags.parquet")
f = flags.set_index("path")
cohorts = {"strict": set(strict.path), "byte_excluded": set(strict.loc[~bm, "path"])}
for name, col in [
    ("train_exact_and_near_excluded", "train_overlap_exact_or_near"),
    ("train_and_validation_exact_and_near_excluded", "train_or_validation_overlap_exact_or_near"),
    ("train_visual_family_sensitivity", "train_overlap_family_sensitivity"),
    (
        "train_and_validation_visual_family_sensitivity",
        "train_or_validation_overlap_family_sensitivity",
    ),
]:
    cohorts[name] = set(strict.path) - set(f.index[f[col]])
clean = sorted(cohorts["train_exact_and_near_excluded"])
truth = c.set_index("path").loc[clean]
expected = {d: set(g.loc[g.label.eq(1), "mani_type"]) for d, g in strict.groupby("domain")}


def score(d, col="probability"):
    d = d.loc[clean]
    assert np.array_equal(d.label.astype(int), truth.label.astype(int))
    domains = {}
    for dom, types in expected.items():
        q = d.loc[truth.domain.eq(dom)]
        ts = truth.loc[q.index]
        assert set(ts.loc[ts.label.eq(1), "mani_type"]) == types
        vals = {}
        for mt in sorted(types):
            k = ts.label.eq(0) | (ts.label.eq(1) & ts.mani_type.eq(mt))
            vals[mt] = auc(q.loc[k, "label"], q.loc[k, col])
        pooled = auc(q.label, q[col])
        weighted = sum(
            vals[mt] * int((ts.label.eq(1) & ts.mani_type.eq(mt)).sum()) for mt in types
        ) / int(ts.label.eq(1).sum())
        assert abs(pooled - weighted) < 1e-12
        domains[dom] = {
            "n": len(q),
            "n_real": int(ts.label.eq(0).sum()),
            "n_fake": int(ts.label.eq(1).sum()),
            "types": vals,
            "pooled": pooled,
        }
    return {
        "n": len(d),
        "primary": float(np.mean([np.mean(list(v["types"].values())) for v in domains.values()])),
        "pooled": float(np.mean([v["pooled"] for v in domains.values()])),
        "domains": domains,
    }


results = {}
for seed in [42, 43, 44]:
    for arm in ["base", "buggy", "loss_fixed", "no_preservation"]:
        d = normalize(read(work / f"execution/predictions/{arm}_s{seed}.csv"))
        results[f"{arm}_{seed}"] = score(d)
p = normalize(read(work / "execution/predictions/patch_moe.csv"))
results["patch_fresh"] = score(p)
results["patch_matched_base"] = score(p, "base_probability")
a = normalize(
    read(root / "research_artifacts/autoresearch_sica_v1/locked_eval/locked_predictions.csv")
)
results["patch_archived"] = score(a)
# Refit training-source prior independently; no OOD labels used in fitting.
doc = c[c.domain.eq("Doc")]
fit = doc[doc.split.eq("train")]
test = doc[doc.split.eq("doc_ood")].copy()
prior = {s: (int(g.label.sum()) + 1) / (len(g) + 2) for s, g in fit.groupby("ori_dataset")}
fallback = (int(fit.label.sum()) + 1) / (len(fit) + 2)
test["score"] = test.ori_dataset.map(prior).fillna(fallback)
r = test[test.label.eq(0)]
source_types = {
    mt: auc(pd.concat([r, g]).label, pd.concat([r, g]).score)
    for mt, g in test[test.label.eq(1)].groupby("mani_type")
}
source = {
    "n": len(test),
    "prior": prior,
    "pooled": auc(test.label, test.score),
    "primary": float(np.mean(list(source_types.values()))),
    "types": source_types,
}
ambiguity = {}
for dom, g in strict.groupby("domain"):
    z = g.groupby("rgb_sha256").label.agg(["sum", "count"])
    z["real"] = z["count"] - z["sum"]
    mixed = z[(z["sum"] > 0) & (z.real > 0)]
    ambiguity[dom] = {
        "groups": len(mixed),
        "rows": int(mixed["count"].sum()),
        "minimum_errors": int(np.minimum(mixed["sum"], mixed.real).sum()),
    }
contrasts = {}
for aa, bb in [
    ("base", "buggy"),
    ("base", "loss_fixed"),
    ("base", "no_preservation"),
    ("buggy", "loss_fixed"),
    ("no_preservation", "loss_fixed"),
]:
    delta = (
        np.array(
            [
                results[f"{bb}_{s}"]["primary"] - results[f"{aa}_{s}"]["primary"]
                for s in [42, 43, 44]
            ]
        )
        * 100
    )
    half = t.ppf(0.975, 2) * delta.std(ddof=1) / np.sqrt(3)
    contrasts[f"{bb}_minus_{aa}"] = {
        "seed_delta_pp": delta.tolist(),
        "mean_pp": float(delta.mean()),
        "sd_pp": float(delta.std(ddof=1)),
        "conditional_t95_pp": [float(delta.mean() - half), float(delta.mean() + half)],
    }
out = {
    "scope": "Independent rank-sum AUC from raw saved CSV; existing image-census hashes/flags, not fresh image decode; no model inference",
    "inputs": receipts,
    "census": {
        "total": len(c),
        "splits": {
            s: {
                "nominal": len(g),
                "strict": int(g.strict_ok.sum()),
                "permissive": int(g.permissive_ok.sum()),
            }
            for s, g in c.groupby("split")
        },
        "strict_ood": len(strict),
        "byte_train_matches": int(bm.sum()),
        "pixel_train_matches": int(pm.sum()),
        "additional_pixel_matches": int((pm & ~bm).sum()),
    },
    "cohorts": {
        k: {"n": len(v), "sha256": hashlib.sha256("\n".join(sorted(v)).encode()).hexdigest()}
        for k, v in cohorts.items()
    },
    "scores": results,
    "contrasts": contrasts,
    "source_prior": source,
    "mixed_pixel_groups": ambiguity,
}
print(json.dumps(out, indent=2, allow_nan=False))
