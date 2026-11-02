"""Internal synthetic conformance experiment, NOT recovered historical POP validator.
Run: python scripts/historical/controlled_benchmark.py --output NEW_DIRECTORY
No external studies, blinded auditors, or operational tracker comparisons claimed.
"""

from pathlib import Path
import argparse
import json
import hashlib
import time
import shutil
import csv
import numpy as np

OUT = None


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def dump(p, x):
    Path(p).write_text(json.dumps(x, indent=2))


def auc(y, p):
    a = p[y == 1]
    b = p[y == 0]
    return float(((a[:, None] > b).sum() + 0.5 * (a[:, None] == b).sum()) / (len(a) * len(b)))


def sigmoid(z):
    return 1 / (1 + np.exp(-np.clip(z, -40, 40)))


def inspect(d, mode="combined"):
    m = json.loads((d / "receipt.json").read_text())
    failures = []
    missing = []

    def need(k):
        if k not in m:
            missing.append(k)
            return None
        return m[k]

    # File receipts are checked separately from semantic checks.
    if mode in ["digest", "combined"]:
        for f, h in m.get("hashes", {}).items():
            if not (d / f).exists():
                missing.append(f)
            elif sha(d / f) != h:
                failures.append("digest:" + f)
    if mode in ["population", "combined"]:
        pop = need("population")
        if pop:
            if set(pop["train_content"]) & set(pop["test_content"]):
                failures.append("overlap")
            if pop["observed_weights"] != pop["registered_weights"]:
                failures.append("weights")
            if pop["excluded"] != sorted(set(pop["train_content"]) & set(pop["test_content"])):
                failures.append("exclusions")
    if mode in ["optimization", "combined"]:
        for arm in ["a", "b"]:
            if not (d / f"{arm}_final.npy").exists():
                missing.append("checkpoint:" + arm)
                continue
            initial = np.load(d / f"{arm}_init.npy")
            final = np.load(d / f"{arm}_final.npy")
            log = np.load(d / f"{arm}_log.npy")
            if (
                len(log) != m["steps"]
                or not np.isfinite(log).all()
                or np.array_equal(initial, final)
            ):
                failures.append("updates:" + arm)
        targets = np.load(d / "y_train.npy")
        if np.any((targets < 0) | (targets > 1)):
            failures.append("targets")
        lineage = need("lineage")
        if lineage:
            if len(set(lineage["replicate_digests"])) != len(lineage["replicate_digests"]):
                failures.append("duplicate")
            if lineage["init_sha"] != sha(d / "a_init.npy"):
                failures.append("initialization")
            if len(lineage["changed_factors"]) != 1:
                missing.append("single-factor attribution")
    if mode in ["reconstruction", "combined"]:
        if not (d / "COMPLETE").exists():
            missing.append("completion sentinel")
        x = np.load(d / "cache.npy")
        if x.shape != tuple(m["cache_shape"]):
            failures.append("cache size")
        for arm in ["a", "b"]:
            if not (d / f"{arm}_final.npy").exists():
                missing.append("checkpoint:" + arm)
                continue
            xx = x[:, : m["features"][arm]]
            if len(xx) == m["test_n"]:
                reconstructed = sigmoid(xx @ np.load(d / f"{arm}_final.npy"))
                if not np.allclose(
                    reconstructed, np.load(d / f"{arm}_pred.npy"), atol=1e-12, rtol=0
                ):
                    failures.append("prediction:" + arm)
    if mode in ["score", "combined"]:
        for arm in ["a", "b"]:
            if (
                abs(auc(np.load(d / "y_test.npy"), np.load(d / f"{arm}_pred.npy")) - m["auc"][arm])
                > 1e-12
            ):
                failures.append("score:" + arm)
    # Partial checks cannot certify all dimensions. Their PASS means local test acceptance only.
    return ("FAIL" if failures else "UNRESOLVED" if missing else "PASS"), failures, missing


def main():
    global OUT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="New output directory for generated synthetic evidence",
    )
    OUT = parser.parse_args().output
    OUT.mkdir(parents=True, exist_ok=False)
    registration = {
        "scope": "internal synthetic logistic comparison; not external image forensics",
        "seeds": [101, 202, 303, 404, 505],
        "data_seed": 810,
        "train_n": 256,
        "test_n": 128,
        "features": {"a": 2, "b": 4},
        "steps": 80,
        "lr": 0.1,
        "estimand": "pooled AUC; fixed balanced synthetic test population",
        "selection": "none; fixed 80 updates",
        "tolerance": 1e-12,
        "limitations": "single generated population; same-author rules and mutations; no blinded human auditors",
    }
    dump(OUT / "registration.json", registration)  # saved before generation or fitting
    rng = np.random.default_rng(810)
    x = rng.normal(size=(384, 4))
    y = (x[:, 0] + 0.5 * x[:, 1] + rng.normal(size=384) > 0.0).astype(float)
    data = OUT / "data"
    data.mkdir(exist_ok=True)
    np.save(data / "features.npy", x)
    np.save(data / "labels.npy", y)
    results = []
    timings = []
    for seed in registration["seeds"]:
        d = OUT / f"seed_{seed}"
        d.mkdir(exist_ok=True)
        t = time.perf_counter()
        np.save(d / "cache.tmp.npy", x[256:])
        (d / "cache.tmp.npy").replace(d / "cache.npy")
        (d / "COMPLETE").write_text(sha(d / "cache.npy"))
        np.save(d / "y_train.npy", y[:256])
        np.save(d / "y_test.npy", y[256:])
        scores = {}
        for arm, k in registration["features"].items():
            w = np.random.default_rng(seed).normal(scale=0.01, size=k)
            np.save(d / f"{arm}_init.npy", w)
            log = []
            for step in range(80):
                p = sigmoid(x[:256, :k] @ w)
                w -= 0.1 * x[:256, :k].T @ (p - y[:256]) / 256
                log.append(
                    [
                        step + 1,
                        float(np.mean(-(y[:256] * np.log(p) + (1 - y[:256]) * np.log(1 - p)))),
                    ]
                )
            np.save(d / f"{arm}_final.npy", w)
            np.save(d / f"{arm}_log.npy", np.array(log))
            pred = sigmoid(x[256:, :k] @ w)
            np.save(d / f"{arm}_pred.npy", pred)
            scores[arm] = auc(y[256:], pred)
        hashes = {p.name: sha(p) for p in d.iterdir() if p.is_file() and p.name != "receipt.json"}
        content = [hashlib.sha256(row.tobytes()).hexdigest() for row in x]
        receipt = {
            "steps": 80,
            "test_n": 128,
            "cache_shape": [128, 4],
            "features": registration["features"],
            "auc": scores,
            "hashes": hashes,
            "population": {
                "train_content": content[:256],
                "test_content": content[256:],
                "registered_weights": [1.0],
                "observed_weights": [1.0],
                "excluded": [],
            },
            "lineage": {
                "seed": seed,
                "init_sha": sha(d / "a_init.npy"),
                "replicate_digests": [sha(d / "a_final.npy")],
                "changed_factors": ["feature_count"],
            },
        }
        dump(d / "receipt.json", receipt)
        timings.append(time.perf_counter() - t)
        assert inspect(d)[0] == "PASS", inspect(d)
        results.append({"seed": seed, **scores, "delta": scores["b"] - scores["a"]})
    clean = OUT / "seed_101"
    faults = [
        ("clean", "PASS"),
        ("overlap", "FAIL"),
        ("weights", "FAIL"),
        ("population_missing", "UNRESOLVED"),
        ("exclusions", "FAIL"),
        ("stalled", "FAIL"),
        ("targets", "FAIL"),
        ("checkpoint_missing", "UNRESOLVED"),
        ("initialization", "FAIL"),
        ("cache_partial", "FAIL"),
        ("sentinel_missing", "UNRESOLVED"),
        ("lineage_corrupt", "FAIL"),
        ("prediction_corrupt", "FAIL"),
        ("duplicate", "FAIL"),
        ("seed_missing", "UNRESOLVED"),
        ("bundled", "UNRESOLVED"),
    ]
    rows = []
    for fault, truth in faults:
        d = OUT / "mutations" / fault
        if d.exists():
            shutil.rmtree(d)
        shutil.copytree(clean, d)
        m = json.loads((d / "receipt.json").read_text())
        if fault == "overlap":
            m["population"]["test_content"][0] = m["population"]["train_content"][0]
        if fault == "weights":
            m["population"]["observed_weights"] = [0.9]
        if fault == "population_missing":
            del m["population"]
        if fault == "exclusions":
            m["population"]["excluded"] = ["unexpected"]
        if fault == "stalled":
            np.save(d / "a_final.npy", np.load(d / "a_init.npy"))
        if fault == "targets":
            z = np.load(d / "y_train.npy")
            z[0] = 2
            np.save(d / "y_train.npy", z)
        if fault == "checkpoint_missing":
            (d / "a_final.npy").unlink()
        if fault == "initialization":
            m["lineage"]["init_sha"] = "wrong"
        if fault == "cache_partial":
            np.save(d / "cache.npy", np.load(d / "cache.npy")[:64])
        if fault == "sentinel_missing":
            (d / "COMPLETE").unlink()
        if fault == "lineage_corrupt":
            np.save(d / "cache.npy", np.zeros((128, 4)))
        if fault == "prediction_corrupt":
            z = np.load(d / "a_pred.npy")
            z[0] = 0.999
            np.save(d / "a_pred.npy", z)
        if fault == "duplicate":
            m["lineage"]["replicate_digests"] *= 2
        if fault == "seed_missing":
            del m["lineage"]
        if fault == "bundled":
            m["lineage"]["changed_factors"] += ["learning_rate"]
        dump(d / "receipt.json", m)
        for mode in ["score", "population", "optimization", "digest", "reconstruction", "combined"]:
            t = time.perf_counter()
            outcome, fail, gap = inspect(d, mode)
            dt = time.perf_counter() - t
            rows.append(
                {
                    "condition": fault,
                    "truth": truth,
                    "mode": mode,
                    "outcome": outcome,
                    "seconds": dt,
                    "contradictions": ";".join(fail),
                    "gaps": ";".join(gap),
                }
            )
            if mode == "combined":
                assert outcome == truth, (fault, outcome, truth, fail, gap)
    with (OUT / "results.csv").open("w") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    summary = {}
    for mode in sorted(set(r["mode"] for r in rows)):
        rr = [r for r in rows if r["mode"] == mode]
        cm = {
            a: {
                b: sum(r["truth"] == a and r["outcome"] == b for r in rr)
                for b in ["PASS", "FAIL", "UNRESOLVED"]
            }
            for a in ["PASS", "FAIL", "UNRESOLVED"]
        }
        tp = sum(r["truth"] == "FAIL" and r["outcome"] == "FAIL" for r in rr)
        fp = sum(r["truth"] != "FAIL" and r["outcome"] == "FAIL" for r in rr)
        fn = sum(r["truth"] == "FAIL" and r["outcome"] != "FAIL" for r in rr)
        f1 = []
        for c in cm:
            ct = cm[c][c]
            cf = sum(cm[a][c] for a in cm if a != c)
            cn = sum(cm[c][b] for b in cm if b != c)
            f1.append(2 * ct / (2 * ct + cf + cn) if 2 * ct + cf + cn else 0)
        summary[mode] = {
            "confusion": cm,
            "precision": tp / (tp + fp) if tp + fp else None,
            "recall": tp / (tp + fn),
            "false_positive_rate": fp / sum(r["truth"] != "FAIL" for r in rr),
            "macro_f1": sum(f1) / 3,
            "unresolved_rate": sum(r["outcome"] == "UNRESOLVED" for r in rr) / len(rr),
            "audit_seconds": sum(r["seconds"] for r in rr),
        }
    dump(
        OUT / "summary.json",
        {
            "metrics": summary,
            "seed_results": results,
            "delta_mean": float(np.mean([r["delta"] for r in results])),
            "delta_sd": float(np.std([r["delta"] for r in results], ddof=1)),
            "fit_and_instrument_seconds": timings,
            "storage_bytes": sum(p.stat().st_size for p in clean.iterdir() if p.is_file()),
            "caveat": "descriptive finite-case conformance; no independent-study confidence interval or product ranking",
        },
    )
    print(json.dumps(summary["combined"], indent=2))


if __name__ == "__main__":
    main()
