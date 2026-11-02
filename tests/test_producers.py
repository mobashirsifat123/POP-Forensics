"""Regression tests for the adapted evidence-producing workflow."""

import copy
import csv
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from popverify.producers.io import atomic_json, write_json
from popverify.producers.optimization import UpdateTracker, parameter_delta
from popverify.producers.population import census, exact_cohort
from popverify.producers.provenance import (
    classify_reconstruction,
    compare_predictions,
    fingerprint,
    inspect_cache,
    publish_cache,
)
from popverify.producers.scoring import cell_weights, compare

PIL_AVAILABLE = importlib.util.find_spec("PIL") is not None


class ProducerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def file(self, name, value):
        path = self.root / name
        write_json(path, value)
        return path

    def csv(self, name, rows):
        path = self.root / name
        with path.open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=["id", "probability", "label"])
            writer.writeheader()
            writer.writerows(rows)
        return path

    @unittest.skipUnless(PIL_AVAILABLE, "install images extra for strict image census")
    def test_census_reencoded_overlap_and_corrupt_image(self):
        from PIL import Image

        image = Image.new("RGB", (3, 2), (20, 40, 60))
        image.save(self.root / "train.png")
        image.save(self.root / "reencoded.bmp")
        Image.new("RGB", (4, 2), (200, 90, 80)).save(self.root / "novel.png")
        (self.root / "broken.png").write_bytes(b"bad-image")
        rows = [
            {
                "id": key,
                "path": path,
                "label": label,
                "split": split,
                "domain": "doc",
                "type": "fake" if label else "real",
            }
            for key, path, label, split in [
                ("train", "train.png", 0, "train"),
                ("copy", "train.png", 0, "eval"),
                ("rgb", "reencoded.bmp", 0, "eval"),
                ("novel", "novel.png", 1, "eval"),
                ("broken", "broken.png", 1, "eval"),
            ]
        ]
        report = census(self.file("manifest.json", rows), self.root)
        self.assertEqual(report["strict_ok"], 4)
        self.assertNotIn("path", report["rows"][0])
        self.assertEqual(report["rows"][0]["rgb_sha256"], report["rows"][2]["rgb_sha256"])
        self.assertNotEqual(report["rows"][0]["sha256"], report["rows"][2]["sha256"])
        cohort = exact_cohort(report, ["train"], ["eval"])
        self.assertEqual(list(cohort["membership"]), ["novel"])
        reasons = {r["id"]: r["reasons"] for r in cohort["excluded"]}
        self.assertIn("training_byte_match", reasons["copy"])
        self.assertEqual(reasons["rgb"], ["training_rgb_match"])
        self.assertEqual(reasons["broken"], ["strict_decode_failed"])
        report["rows"][0]["strict_ok"] = False
        with self.assertRaises(ValueError):
            exact_cohort(report, ["train"], ["eval"])

    @unittest.skipUnless(PIL_AVAILABLE, "install images extra")
    def test_census_paths_duplicates_and_permissive_setting(self):
        from PIL import ImageFile

        row = {
            "id": "one",
            "path": "../escape.png",
            "split": "train",
            "label": 0,
            "domain": "doc",
            "type": "real",
        }
        manifest = self.file("manifest.json", [row])
        with self.assertRaises(ValueError):
            census(manifest, self.root)
        manifest.write_text(json.dumps([row, row]))
        with self.assertRaises(ValueError):
            census(manifest, self.root)
        manifest.write_text(json.dumps([{**row, "path": "absent.png"}]))
        with patch.object(ImageFile, "LOAD_TRUNCATED_IMAGES", True):
            with self.assertRaises(ValueError):
                census(manifest, self.root)

    def test_atomic_json_never_overwrites(self):
        target = self.root / "receipt.json"
        atomic_json(target, {"original": 1})
        with self.assertRaises(FileExistsError):
            atomic_json(target, {"changed": 1})
        self.assertEqual(json.loads(target.read_text()), {"original": 1})
        self.assertEqual(list(self.root.glob(".pop-*")), [])

    def test_publish_integrity_missing_and_tampered_cache(self):
        source = self.file("features.json", [1, 2, 3])
        destination = self.root / "cache"
        report = publish_cache(destination, {"features.json": source})
        self.assertTrue(report["complete"])
        self.assertTrue(inspect_cache(destination)["complete"])
        with self.assertRaises(FileExistsError):
            publish_cache(destination, {"features.json": source})
        (destination / "features.json").write_text("[0]")
        self.assertFalse(inspect_cache(destination)["complete"])
        (destination / "features.json").unlink()
        self.assertIsNone(inspect_cache(destination)["complete"])
        (destination / "COMMIT.json").unlink()
        self.assertEqual(inspect_cache(destination)["missing"], ["COMMIT.json"])

    def test_cache_source_changes_and_partial_publication(self):
        source = self.file("features.json", [1, 2])
        destination = self.root / "cache"
        with patch(
            "popverify.producers.provenance.shutil.copyfileobj", side_effect=OSError("interrupted")
        ):
            with self.assertRaises(OSError):
                publish_cache(destination, {"features.json": source})
        self.assertFalse(destination.exists())
        self.assertEqual(list(self.root.glob(".pop-cache-*")), [])
        self.assertFalse((self.root / ".cache.publish.lock").exists())
        with self.assertRaises(ValueError):
            publish_cache(destination, {"../bad": source})
        symlink = self.root / "symlink.json"
        symlink.symlink_to(source)
        with self.assertRaises(ValueError):
            fingerprint(symlink)

    def test_fingerprint_detects_midread_mutation(self):
        source = self.file("data.json", [1])

        def mutate(path):
            path.write_text("[100000, 200000, 300000]")
            return "a" * 64

        with patch("popverify.producers.provenance.sha256", side_effect=mutate):
            with self.assertRaises(ValueError):
                fingerprint(source)

    def test_scoring_aligns_ids_and_preserves_type_weights(self):
        membership = {"r": {"label": 0, "split": "eval", "domain": "doc", "type": "real"}}
        for i in range(5):
            membership[f"c{i}"] = {"label": 1, "split": "eval", "domain": "doc", "type": "common"}
        membership["rare"] = {"label": 1, "split": "eval", "domain": "doc", "type": "rare"}
        expected = {"doc": ["common", "rare"]}
        a = [
            {
                "id": key,
                "label": row["label"],
                "probability": 0.5 if key == "r" else 0.4 if key in {"c0", "c1"} else 0.6,
            }
            for key, row in membership.items()
        ]
        b = copy.deepcopy(a)
        for row in b:
            if row["id"] in {"c0", "c1"}:
                row["probability"] = 0.6
            elif row["id"] == "rare":
                row["probability"] = 0.4
        left, right = self.csv("a.csv", a), self.csv("b.csv", list(reversed(b)))
        report = compare({"membership": membership}, left, right, expected)
        self.assertLess(report["delta_pp"]["A_type"], 0)
        self.assertGreater(report["delta_pp"]["A_pool"], 0)
        self.assertAlmostEqual(sum(cell_weights(expected, membership, "A_type").values()), 1)
        self.assertNotEqual(
            cell_weights(expected, membership, "A_type"),
            cell_weights(expected, membership, "A_pool"),
        )
        right.write_text("id,probability,label\nr,0.5,0\n")
        with self.assertRaises(ValueError):
            compare({"membership": membership}, left, right, expected)

    def test_prediction_comparison_and_mixed_signatures(self):
        def rows(scores):
            return [{"id": str(i), "probability": p, "label": i % 2} for i, p in enumerate(scores)]

        saved = self.csv("saved.csv", rows([0.1, 0.7, 0.3, 0.9]))
        complete = self.csv("complete.csv", list(reversed(rows([0.1, 0.4, 0.3, 0.2]))))
        alternative = self.csv("alternative.csv", rows([0.5, 0.7, 0.3, 0.4]))
        report = classify_reconstruction(saved, complete, alternative, 1e-6)
        self.assertEqual(
            report["counts"], {"complete_only": 1, "alternative_only": 1, "both": 1, "neither": 1}
        )
        self.assertFalse(compare_predictions(saved, complete, 1e-6)["matches"])
        self.assertTrue(compare_predictions(saved, saved, 0)["matches"])
        with self.assertRaises(ValueError):
            compare_predictions(saved, complete, float("nan"))
        with self.assertRaises(ValueError):
            compare_predictions(saved, complete, 1e-6, ["0", "0"])
        complete.write_text("id,probability,label\n0,0.1,1\n")
        with self.assertRaises(ValueError):
            compare_predictions(saved, complete, 1e-6)

    def test_invalid_prediction_exports(self):
        saved = self.csv("saved.csv", [{"id": "a", "probability": 0.5, "label": 0}])
        for contents in [
            "id,probability\na,NaN\n",
            "id,probability\na,1.1\n",
            "id,probability\na,0.5\na,0.6\n",
            "id,id,probability\na,a,0.5\n",
        ]:
            saved.write_text(contents)
            with self.assertRaises(ValueError):
                compare_predictions(saved, saved, 0)

    def test_producer_cli_error_codes(self):
        command = [sys.executable, "-m", "popverify.producers.cli"]
        missing = subprocess.run(
            command
            + [
                "inspect-cache",
                str(self.root / "absent"),
                "--output",
                str(self.root / "result.json"),
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(missing.returncode, 3)
        source = self.file("features.json", [1])
        output = self.root / "report.json"
        args = ["publish-cache", str(self.root / "cache"), str(source), "--output", str(output)]
        good = subprocess.run(command + args, capture_output=True, text=True)
        self.assertEqual(good.returncode, 0, good.stderr)
        again = subprocess.run(command + args, capture_output=True, text=True)
        self.assertEqual(again.returncode, 3)


class FakeHandle:
    def __init__(self, optimizer):
        self.optimizer = optimizer

    def remove(self):
        self.optimizer.hook = None


class FakeOptimizer:
    def register_step_post_hook(self, hook):
        self.hook = hook
        return FakeHandle(self)

    def step(self):
        if self.hook:
            self.hook(self, (), {})


class OptimizationTests(unittest.TestCase):
    def test_actual_steps_skips_and_nonfinite_losses(self):
        optimizer = FakeOptimizer()
        with UpdateTracker(optimizer) as tracker:
            tracker.loss(0.4)
            tracker.targets([0, 0.9, 1], "float32")
            tracker.attempt()
            optimizer.step()
            tracker.attempt()  # scaler skipped this optimizer call
            tracker.loss(float("inf"))
            evidence = tracker.evidence()
        self.assertEqual(evidence["updates"], {"successful": 1, "skipped": 1, "nonfinite": 1})
        self.assertEqual(evidence["targets"]["values"], [0, 0.9, 1])
        self.assertIsNone(optimizer.hook)
        with self.assertRaises(RuntimeError):
            tracker.attempt()

    def test_missing_attempt_and_bad_targets(self):
        optimizer = FakeOptimizer()
        with UpdateTracker(optimizer) as tracker:
            optimizer.step()
            with self.assertRaises(ValueError):
                tracker.evidence()
        with UpdateTracker(optimizer) as tracker:
            tracker.targets([2, float("inf")], "float16")
            report = tracker.evidence()
            self.assertNotIn("targets", report)
            self.assertEqual(report["diagnostics"]["outside_unit_targets"], 1)
            self.assertEqual(report["diagnostics"]["nonfinite_targets"], 1)

    def test_parameter_change_and_identity_checks(self):
        before = {"w": {"shape": [2], "values": [1, 2]}}
        after = {"w": {"shape": [2], "values": [4, 6]}}
        self.assertEqual(parameter_delta(before, after), 5)
        with self.assertRaises(ValueError):
            parameter_delta(before, {"other": after["w"]})
        with self.assertRaises(ValueError):
            parameter_delta(before, {"w": {"shape": [1], "values": [4]}})


if __name__ == "__main__":
    unittest.main()


class SicaAdapterTests(unittest.TestCase):
    def test_native_manifest_and_predictions_align_without_private_paths(self):
        from popverify.producers.sica import import_manifests, import_predictions

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / "native.json"
            manifest.write_text(
                json.dumps(
                    [
                        {
                            "path": str(root / "image.png"),
                            "label": 1,
                            "domain": "Doc",
                            "mani_type": "AIGC",
                        }
                    ]
                )
            )
            rows, receipts = import_manifests({"doc_ood": manifest}, root)
            csv_path = root / "native.csv"
            with csv_path.open("w", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=["path", "label", "probability"])
                writer.writeheader()
                writer.writerow({"path": str(root / "image.png"), "label": 1, "probability": 0.8})
            predictions = import_predictions(csv_path, root, "doc_ood")
            self.assertEqual(rows[0]["id"], predictions[0]["id"])
            self.assertNotIn(str(root), json.dumps(rows))
            self.assertEqual(rows[0]["path"], "image.png")
            self.assertEqual(receipts[0]["rows"], 1)
            manifest.write_text(
                json.dumps(
                    [{"path": "../escape.png", "label": 1, "domain": "Doc", "mani_type": "fake"}]
                )
            )
            with self.assertRaises(ValueError):
                import_manifests({"doc_ood": manifest}, root)

    def test_legacy_log_gaps_do_not_invent_scaler_cause(self):
        from popverify.producers.logs import summarize_training_log

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "log.txt"
            path.write_text(
                "\n".join(
                    json.dumps(
                        {
                            "epoch": e,
                            "train_actual_optimizer_steps": n,
                            "train_nominal_accumulation_boundaries": 10,
                            "train_nonfinite_steps": 0,
                        }
                    )
                    for e, n in [(0, 10), (1, 9)]
                )
            )
            result = summarize_training_log(path, [0, 1])
            self.assertEqual(result["totals"]["unexplained_boundary_gap"], 1)
            self.assertEqual(result["missing"], [])
            self.assertIsNone(summarize_training_log(path, [0, 1, 2])["totals"])
            path.write_text(path.read_text() + "\n" + json.dumps({"epoch": 1}))
            with self.assertRaises(ValueError):
                summarize_training_log(path, [0, 1])
