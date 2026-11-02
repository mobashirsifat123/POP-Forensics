"""CPU image → content census → training instrumentation → POP receipt example.

Requires Pillow and an existing CPU-capable PyTorch install. No SICA weights,
external datasets or GPU are used. Run: python examples/evidence_pipeline/run.py OUTPUT
This is a new integration fixture, not the historical forensic experiment.
"""

import argparse
import csv
import json
from pathlib import Path
import random

from PIL import Image
import torch

from popverify import verify
from popverify.evidence import sha256
from popverify.producers.io import write_json
from popverify.producers.optimization import UpdateTracker, parameter_delta, parameter_snapshot
from popverify.producers.population import census, exact_cohort
from popverify.producers.provenance import compare_predictions, inspect_cache, publish_cache
from popverify.producers.scoring import cell_weights, compare


def export_csv(path, ids, labels, scores):
    with path.open("x", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["id", "label", "probability"])
        writer.writeheader()
        writer.writerows(
            {"id": key, "label": label, "probability": score}
            for key, label, score in zip(ids, labels, scores)
        )


def run(destination):
    torch.set_num_threads(1)
    root = Path(destination)
    root.mkdir(parents=True, exist_ok=False)
    images = root / "images"
    images.mkdir()
    rng = random.Random(810)
    rows, features = [], {}
    # Each image has unique pixels; brightness is the synthetic label signal.
    for i in range(36):
        label = i % 2
        image = Image.new("RGB", (4, 4))
        center = 190 if label else 50
        pixels = [tuple(center + rng.randrange(-20, 21) for _ in range(3)) for _ in range(16)]
        image.putdata(pixels)
        name = f"sample-{i:03d}"
        image.save(images / f"{name}.png")
        features[name] = [
            sum(pixel[0] for pixel in pixels) / (16 * 255),
            sum(pixel[1] for pixel in pixels) / (16 * 255),
        ]
        rows.append(
            {
                "id": name,
                "path": f"{name}.png",
                "label": label,
                "split": "train" if i < 24 else "evaluation",
                "domain": "synthetic",
                "type": "fake" if label else "real",
            }
        )
    write_json(root / "manifest.json", rows)
    census_report = census(root / "manifest.json", images)
    write_json(root / "census.json", census_report)
    cohort = exact_cohort(census_report, ["train"], ["evaluation"])
    write_json(root / "cohort.json", cohort)
    expected_types = {"synthetic": ["fake"]}
    ids = sorted(cohort["membership"])
    labels = [cohort["membership"][key]["label"] for key in ids]
    cache_source = root / "intended-inputs.json"
    write_json(cache_source, [features[key] for key in ids])
    # Freeze intended cache bytes and optimizer requirements before fitting.
    assertions = []

    def add(key, gate, kind, expected, arm=None, tolerance=0):
        item = {
            "id": key,
            "gate": gate,
            "kind": kind,
            "evidence": key,
            "expected": expected,
            "tolerance": tolerance,
        }
        if arm:
            item["arm"] = arm
        assertions.append(item)

    add("membership", "P1", "membership", cohort["membership"])
    add("byte-content", "P1", "disjoint", True)
    add("rgb-content", "P1", "disjoint", True)
    weights = cell_weights(expected_types, cohort["membership"], "A_type")
    add("weights", "P1", "weights", weights)
    add("cache-complete", "P2", "completion", True)
    add("cache-bytes", "P2", "digest", sha256(cache_source))
    models = {}
    for arm in ("baseline", "candidate"):
        torch.manual_seed(101)
        model = torch.nn.Linear(1 if arm == "baseline" else 2, 1).double()
        models[arm] = model
        write_json(root / f"{arm}-initial.json", parameter_snapshot(model))
        add(f"{arm}-initial", "O", "initialization", sha256(root / f"{arm}-initial.json"), arm)
        add(f"{arm}-targets", "O", "targets", {"dtype": "float64", "min": 0, "max": 1}, arm)
        add(
            f"{arm}-updates",
            "O",
            "updates",
            {"successful": 40, "max_skipped": 0, "max_nonfinite": 0},
            arm,
        )
        add(f"{arm}-delta", "O", "parameter_change", 1e-4, arm)
        add(f"{arm}-reconstruction", "P2", "reconstruction", f"{arm}-saved.json", arm, 1e-12)
    write_json(
        root / "registration.json",
        {
            "schema_version": 1,
            "scope": "new CPU image evidence pipeline; not historical SICA",
            "arms": ["baseline", "candidate"],
            "assertions": assertions,
        },
    )
    publish_cache(root / "cache", {"inputs.json": cache_source})
    evidence = {
        "membership": cohort["membership"],
        "byte-content": cohort["byte_content"],
        "rgb-content": cohort["rgb_content"],
        "weights": weights,
        "cache-complete": inspect_cache(root / "cache")["complete"],
        "cache-bytes": "cache/inputs.json",
    }
    train = [r for r in rows if r["split"] == "train"]
    for arm, model in models.items():
        count = 1 if arm == "baseline" else 2
        x = torch.tensor([features[r["id"]][:count] for r in train], dtype=torch.float64)
        y = torch.tensor([r["label"] for r in train], dtype=torch.float64)
        optimizer = torch.optim.SGD(model.parameters(), lr=0.2)
        initial = parameter_snapshot(model)
        losses = []
        with UpdateTracker(optimizer) as tracker:
            for _ in range(40):
                optimizer.zero_grad()
                tracker.targets(y, "float64")
                loss = torch.nn.functional.binary_cross_entropy_with_logits(model(x).reshape(-1), y)
                tracker.loss(loss)
                losses.append(loss.item())
                loss.backward()
                tracker.attempt()
                optimizer.step()
            observed = tracker.evidence()
        final = parameter_snapshot(model)
        write_json(root / f"{arm}-final.json", final)
        write_json(root / f"{arm}-training.json", {"losses": losses, **observed})
        evidence.update(
            {
                f"{arm}-initial": f"{arm}-initial.json",
                f"{arm}-targets": observed["targets"],
                f"{arm}-updates": observed["updates"],
                f"{arm}-delta": parameter_delta(initial, final),
            }
        )
        # First prediction pass from the published intended input cache.
        inputs = torch.tensor(
            json.loads((root / "cache/inputs.json").read_text()), dtype=torch.float64
        )
        with torch.no_grad():
            saved = model(inputs[:, :count]).reshape(-1).sigmoid().tolist()
        export_csv(root / f"{arm}.csv", ids, labels, saved)
        # Reconstruct via a fresh model from non-executable JSON parameter values.
        reconstructed_model = torch.nn.Linear(count, 1).double()
        with torch.no_grad():
            for name, parameter in reconstructed_model.named_parameters():
                parameter.copy_(
                    torch.tensor(final[name]["values"], dtype=torch.float64).reshape(
                        final[name]["shape"]
                    )
                )
            reconstructed = reconstructed_model(inputs[:, :count]).reshape(-1).sigmoid().tolist()
        export_csv(root / f"{arm}-reconstructed.csv", ids, labels, reconstructed)
        residuals = compare_predictions(
            root / f"{arm}.csv", root / f"{arm}-reconstructed.csv", 1e-12, ids
        )
        write_json(root / f"{arm}-reconstruction-report.json", residuals)
        write_json(root / f"{arm}-saved.json", residuals["saved"])
        write_json(root / f"{arm}-reconstructed.json", residuals["reconstructed"])
        evidence[f"{arm}-reconstruction"] = f"{arm}-reconstructed.json"
    write_json(root / "evidence.json", evidence)
    write_json(
        root / "score.json",
        compare(cohort, root / "baseline.csv", root / "candidate.csv", expected_types),
    )
    receipt = verify(root / "registration.json", root / "evidence.json")
    write_json(root / "receipt.json", receipt)
    if receipt["outcome"] != "PASS":
        raise RuntimeError(json.dumps(receipt))
    print(
        json.dumps(
            {
                "outcome": receipt["outcome"],
                "gates": receipt["gates"],
                "evaluation_rows": len(ids),
                "torch_version": torch.__version__,
                "device": "cpu",
                "scope": receipt["scope"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    run(parser.parse_args().output)
