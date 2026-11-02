"""Stable fingerprints and prediction reconstruction checks.

Adapted from fingerprint_cached_inputs.py and the SICA reconstruction workflow.
The model-independent comparator consumes externally produced predictions; no
GPU model or third-party checkpoint loader is imported here.
"""

import os
from pathlib import Path
import shutil
import tempfile

from ..evidence import artifact, sha256
from ..registration import number, read_json
from .io import write_json
from .scoring import predictions


def fingerprint(path):
    """Refuse inputs whose inode/size/mtime/ctime changes while being hashed."""
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError("fingerprint requires a regular, non-symlink file")

    def signature(stat):
        return (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns)

    before = path.stat()
    digest = sha256(path)
    after = path.stat()
    if signature(before) != signature(after):
        raise ValueError("artifact changed during fingerprinting")
    return {"sha256": digest, "bytes": after.st_size}


def publish_cache(destination, files):
    """Stage input files and a commit manifest, then publish the whole directory.

    New destinations only. A cooperative sibling lock serializes this producer;
    external hostile filesystem mutations are not prevented. Readers must call
    inspect_cache() rather than treating directory/file existence as completion.
    This supports supplied bytes; it cannot prove their scientific correctness.
    """
    destination = Path(destination)
    parent = destination.parent
    if not parent.is_dir() or not files:
        raise ValueError("existing destination parent and nonempty source mapping required")
    for name in files:
        if (
            not isinstance(name, str)
            or Path(name).name != name
            or name in {".", "..", "COMMIT.json"}
            or not name
        ):
            raise ValueError("cache names must be plain filenames other than COMMIT.json")
    lock = parent / ("." + destination.name + ".publish.lock")
    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    staging = None
    try:
        os.close(fd)
        if destination.exists() or destination.is_symlink():
            raise FileExistsError(destination)
        staging = Path(tempfile.mkdtemp(prefix=".pop-cache-", dir=parent))
        manifest = {}
        for name, source in files.items():
            before = fingerprint(source)
            target = staging / name
            with open(source, "rb") as inp, target.open("xb") as out:
                shutil.copyfileobj(inp, out)
                out.flush()
                os.fsync(out.fileno())
            if fingerprint(source) != before or fingerprint(target) != before:
                raise ValueError("source changed during cache publication")
            manifest[name] = before
        write_json(staging / "COMMIT.json", {"schema_version": 1, "files": manifest})
        with (staging / "COMMIT.json").open("rb") as stream:
            os.fsync(stream.fileno())
        os.rename(staging, destination)
        staging = None
        return {
            "complete": True,
            "manifest": fingerprint(destination / "COMMIT.json"),
            "files": manifest,
        }
    finally:
        if staging is not None:
            shutil.rmtree(staging)
        lock.unlink(missing_ok=True)


def inspect_cache(directory):
    """Check a published directory against its commit; missing is not complete.

    This producer emits diagnostics, not an aggregate POP verdict. Bind the
    independently retained COMMIT digest through a registered digest assertion.
    """
    directory = Path(directory)
    if not directory.is_dir() or directory.is_symlink():
        raise ValueError("cache directory missing or symlinked")
    manifest_path = directory / "COMMIT.json"
    if not manifest_path.exists():
        return {"complete": None, "missing": ["COMMIT.json"], "contradictions": []}
    fingerprint(manifest_path)
    manifest = read_json(manifest_path)
    if (
        not isinstance(manifest, dict)
        or manifest.get("schema_version") != 1
        or not isinstance(manifest.get("files"), dict)
        or not manifest["files"]
    ):
        raise ValueError("invalid cache commit manifest")
    missing, contradictions = [], []
    for name, expected in manifest["files"].items():
        if (
            not isinstance(name, str)
            or Path(name).name != name
            or name in {"COMMIT.json", ".", ".."}
        ):
            raise ValueError("invalid manifest artifact name")
        if (
            not isinstance(expected, dict)
            or set(expected) != {"sha256", "bytes"}
            or type(expected["bytes"]) is not int
            or expected["bytes"] < 0
            or not isinstance(expected["sha256"], str)
            or len(expected["sha256"]) != 64
            or any(c not in "0123456789abcdef" for c in expected["sha256"])
        ):
            raise ValueError("invalid cache artifact fingerprint")
        target = artifact(directory, name)
        if not target.exists():
            missing.append(name)
        elif fingerprint(directory / name) != expected:
            contradictions.append(name)
    unexpected = sorted(
        p.name
        for p in directory.iterdir()
        if p.name not in manifest["files"] and p.name != "COMMIT.json"
    )
    contradictions.extend("unexpected:" + name for name in unexpected)
    return {
        "complete": False if contradictions else None if missing else True,
        "missing": missing,
        "contradictions": contradictions,
        "manifest": fingerprint(manifest_path),
    }


def compare_predictions(saved_csv, reconstructed_csv, tolerance, row_ids=None):
    """Compare identity-aligned external prediction exports, no imputation.

    Optional row_ids must be the registered order. Without a subset, both CSVs
    must have identical ID sets. Labels, when present in both, must also agree.
    """
    if not number(tolerance) or tolerance < 0:
        raise ValueError("tolerance must be finite and nonnegative")
    saved, reconstructed = predictions(saved_csv), predictions(reconstructed_csv)
    if row_ids is None:
        if saved.keys() != reconstructed.keys():
            raise ValueError("prediction identity sets differ")
        row_ids = sorted(saved)
    if (
        not row_ids
        or len(set(row_ids)) != len(row_ids)
        or not set(row_ids) <= saved.keys()
        or not set(row_ids) <= reconstructed.keys()
    ):
        raise ValueError("registered row order is empty, duplicated or missing from predictions")
    errors, left, right = [], [], []
    for key in row_ids:
        a, b = saved[key], reconstructed[key]
        if "label" in a and "label" in b and a["label"] != b["label"]:
            raise ValueError("saved/reconstructed labels disagree")
        left.append(a["score"])
        right.append(b["score"])
        errors.append(abs(a["score"] - b["score"]))
    return {
        "count": len(errors),
        "max_absolute_error": max(errors),
        "mean_absolute_error": sum(errors) / len(errors),
        "rows_above_tolerance": sum(e > tolerance for e in errors),
        "tolerance": tolerance,
        "matches": all(e <= tolerance for e in errors),
        "input_sha256": {"saved": sha256(saved_csv), "reconstructed": sha256(reconstructed_csv)},
        "row_ids": list(row_ids),
        "saved": left,
        "reconstructed": right,
    }


def classify_reconstruction(saved_csv, complete_csv, alternative_csv, tolerance):
    """Diagnose mixed complete/alternative input signatures, not causality.

    Mirrors the paper's completed-cache/zero-patch comparison, but accepts any
    externally computed alternative and never labels a cache race as proven.
    """
    complete = compare_predictions(saved_csv, complete_csv, tolerance)
    alternative = compare_predictions(saved_csv, alternative_csv, tolerance, complete["row_ids"])
    # Enforce the same full population for both alternatives.
    if predictions(alternative_csv).keys() != predictions(saved_csv).keys():
        raise ValueError("alternative reconstruction population differs")
    classes = {"complete_only": [], "alternative_only": [], "both": [], "neither": []}
    for key, saved, a, b in zip(
        complete["row_ids"],
        complete["saved"],
        complete["reconstructed"],
        alternative["reconstructed"],
    ):
        good_a, good_b = abs(saved - a) <= tolerance, abs(saved - b) <= tolerance
        name = (
            "both"
            if good_a and good_b
            else "complete_only"
            if good_a
            else "alternative_only"
            if good_b
            else "neither"
        )
        classes[name].append(key)
    return {
        "counts": {name: len(ids) for name, ids in classes.items()},
        "rows": classes,
        "complete_comparison": {
            k: v for k, v in complete.items() if k not in {"saved", "reconstructed", "row_ids"}
        },
        "alternative_comparison": {
            k: v for k, v in alternative.items() if k not in {"saved", "reconstructed", "row_ids"}
        },
        "interpretation": "numerical reconstruction signatures, not independent proof of historical input timing",
    }
