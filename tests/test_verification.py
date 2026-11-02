"""New reference conformance cases inspired by the paper's fault taxonomy."""

import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from popverify import verify
from popverify.registration import RegistrationError, read_json, validate
from popverify.verification import reduce_outcomes
from popverify.metrics import auc, estimands

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("synthetic", ROOT / "examples/synthetic/generate.py")
synthetic = importlib.util.module_from_spec(spec)
spec.loader.exec_module(synthetic)


class VerificationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = synthetic.generate(Path(self.temp.name) / "case")
        self.reg = self.root / "registration.json"
        self.ev = self.root / "evidence.json"

    def edit(self, mutate):
        data = read_json(self.ev)
        mutate(data)
        synthetic.write(self.ev, data)

    def result(self):
        return verify(self.reg, self.ev)

    def test_sixteen_conformance_cases(self):
        clean = read_json(self.ev)
        cases = [
            ("clean", "PASS", lambda d: None),
            (
                "overlap",
                "FAIL",
                lambda d: d["content"]["evaluation"].__setitem__(0, d["content"]["train"][0]),
            ),
            ("weights", "FAIL", lambda d: d.__setitem__("weights", {"synthetic/type-1": 0.9})),
            ("population_missing", "UNRESOLVED", lambda d: d.pop("membership")),
            ("membership", "FAIL", lambda d: d["membership"].pop("sample-0")),
            ("stalled", "FAIL", lambda d: d.__setitem__("baseline-delta", 0)),
            ("targets", "FAIL", lambda d: d["baseline-targets"]["values"].__setitem__(0, 2)),
            (
                "checkpoint_missing",
                "UNRESOLVED",
                lambda d: d.__setitem__("baseline-initial", "absent.json"),
            ),
            (
                "initialization",
                "FAIL",
                lambda d: d.__setitem__("baseline-initial", "baseline-final.json"),
            ),
            ("cache_partial", "FAIL", lambda d: d.__setitem__("cache", "baseline-final.json")),
            ("sentinel_missing", "UNRESOLVED", lambda d: d.pop("complete")),
            ("cache_uncommitted", "FAIL", lambda d: d.__setitem__("complete", False)),
            (
                "prediction_corrupt",
                "FAIL",
                lambda d: d.__setitem__("baseline-reconstruction", "candidate-reconstructed.json"),
            ),
            ("duplicate", "FAIL", lambda d: d.__setitem__("replicates", ["seed-101", "seed-101"])),
            ("lineage_missing", "UNRESOLVED", lambda d: d.pop("replicates")),
            ("bundled", "UNRESOLVED", lambda d: d.__setitem__("factors", ["features", "resize"])),
        ]
        for name, expected, mutation in cases:
            with self.subTest(name=name):
                data = copy.deepcopy(clean)
                mutation(data)
                synthetic.write(self.ev, data)
                self.assertEqual(self.result()["outcome"], expected)

    def test_fail_priority_with_missing_evidence(self):
        self.edit(lambda d: (d.pop("complete"), d.__setitem__("baseline-delta", 0)))
        self.assertEqual(self.result()["outcome"], "FAIL")
        self.assertEqual(reduce_outcomes([]), "UNRESOLVED")

    def test_bad_evidence_is_unresolved(self):
        for value in [
            [],
            {"weights": []},
            {"baseline-targets": {"dtype": "float64", "values": ["nan"]}},
        ]:
            synthetic.write(self.ev, value)
            self.assertEqual(self.result()["outcome"], "UNRESOLVED")
        self.ev.write_text('{"x": NaN}')
        self.assertEqual(self.result()["outcome"], "UNRESOLVED")
        self.ev.unlink()
        self.assertEqual(self.result()["outcome"], "UNRESOLVED")

    def test_invalid_registration(self):
        clean = read_json(self.reg)
        mutations = [
            lambda d: d.__setitem__("schema_version", 2),
            lambda d: d.__setitem__("assertions", []),
            lambda d: d["assertions"][0].__setitem__("kind", "unknown"),
            lambda d: d["assertions"][0].__setitem__("tolerance", -1),
            lambda d: d["assertions"].append(copy.deepcopy(d["assertions"][0])),
            lambda d: d["assertions"].pop(),
            lambda d: d["assertions"][2].__setitem__("expected", {"x": 0.9}),
        ]
        for mutate in mutations:
            d = copy.deepcopy(clean)
            mutate(d)
            with self.assertRaises(RegistrationError):
                validate(d)

    def test_malformed_json_duplicate_keys(self):
        self.ev.write_text('{"complete": true, "complete": false}')
        self.assertEqual(self.result()["outcome"], "UNRESOLVED")

    def test_digest_checks_bytes_and_safe_paths(self):
        (self.root / "cache.json").write_text("[]")
        self.assertEqual(self.result()["outcome"], "FAIL")
        self.edit(lambda d: d.__setitem__("cache", "../secret.json"))
        self.assertEqual(self.result()["outcome"], "UNRESOLVED")
        link = self.root / "outside.json"
        link.symlink_to(Path(self.temp.name) / "secret.json")
        self.edit(lambda d: d.__setitem__("cache", "outside.json"))
        self.assertEqual(self.result()["outcome"], "UNRESOLVED")

    def test_update_and_dtype_checks(self):
        self.edit(lambda d: d["baseline-updates"].__setitem__("skipped", 1))
        self.assertEqual(self.result()["outcome"], "FAIL")
        self.edit(lambda d: d["baseline-targets"].__setitem__("dtype", "float16"))
        self.assertEqual(self.result()["gates"]["O"], "FAIL")

    def test_reconstruction_tolerance(self):
        path = self.root / "baseline-reconstructed.json"
        values = read_json(path)
        values[0] += 5e-13
        synthetic.write(path, values)
        self.assertEqual(self.result()["outcome"], "PASS")
        values[0] += 1e-5
        synthetic.write(path, values)
        self.assertEqual(self.result()["outcome"], "FAIL")
        synthetic.write(path, values[:-1])
        self.assertEqual(self.result()["outcome"], "FAIL")

    def test_receipt_binds_inputs(self):
        receipt = self.result()
        self.assertEqual(len(receipt["inputs"]["registration"]), 64)
        self.assertIn("cache.json", receipt["artifacts"])
        self.assertEqual(receipt, self.result())

    def test_cli(self):
        def run(*args):
            return subprocess.run(
                [sys.executable, "-m", "popverify.cli", *map(str, args)],
                capture_output=True,
                text=True,
            )

        self.assertEqual(run("validate", self.reg).returncode, 0)
        good = run("verify", self.reg, self.ev, "--json")
        self.assertEqual(good.returncode, 0)
        self.assertEqual(json.loads(good.stdout)["outcome"], "PASS")
        self.edit(lambda d: d.pop("complete"))
        self.assertEqual(run("verify", self.reg, self.ev).returncode, 2)
        self.edit(lambda d: d.__setitem__("baseline-delta", 0))
        self.assertEqual(run("verify", self.reg, self.ev).returncode, 1)
        self.assertEqual(run("verify", self.reg, self.ev, "--output", self.ev).returncode, 3)
        self.assertEqual(run("verify", self.root / "absent", self.ev).returncode, 3)


class MetricTests(unittest.TestCase):
    def test_auc_ties_and_invalid_cells(self):
        self.assertEqual(auc([0, 1], [0.5, 0.5]), 0.5)
        self.assertEqual(auc([0, 1], [0.1, 0.9]), 1)
        with self.assertRaises(ValueError):
            auc([1], [0.2])
        with self.assertRaises(ValueError):
            auc([0, 1], [0.2, float("nan")])

    def test_estimand_reversal_and_missing_cells(self):
        # One domain: frequent type improves, minority type degrades more.
        types = {"doc": ["common", "rare"]}
        base = [{"domain": "doc", "type": "real", "label": 0, "score": 0.5}]
        base += [
            {"domain": "doc", "type": "common", "label": 1, "score": s}
            for s in [0.4, 0.4, 0.6, 0.6, 0.6]
        ]
        base += [{"domain": "doc", "type": "rare", "label": 1, "score": 0.6}]
        candidate = copy.deepcopy(base)
        candidate[1]["score"] = 0.6
        candidate[2]["score"] = 0.6
        candidate[-1]["score"] = 0.4
        a, b = estimands(base, types), estimands(candidate, types)
        self.assertLess(b["A_type"], a["A_type"])
        self.assertGreater(b["A_pool"], a["A_pool"])
        with self.assertRaises(ValueError):
            estimands(base[:-1], types)
        multi = copy.deepcopy(base)
        multi += [
            {"domain": "other", "type": "real", "label": 0, "score": 0.1},
            {"domain": "other", "type": "fake", "label": 1, "score": 0.9},
        ]
        scores = estimands(multi, {**types, "other": ["fake"]})
        self.assertNotEqual(scores["A_type"], scores["A_unif"])


if __name__ == "__main__":
    unittest.main()
