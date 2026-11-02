"""Image census/exclusions adapted from phase1_cpu.py on pro6000.

The decoded digest preserves the research convention:
SHA256(b'RGB:<width>:<height>:' + contiguous RGB pixels), no EXIF transpose.
Only strict decoding is accepted; permissive retries and pHash are not included.
"""

import hashlib
import io
from pathlib import Path
import warnings

from ..evidence import artifact, sha256
from ..registration import read_json


def inspect_image(path):
    """Inspect one local image without modifying it (Pillow optional dependency).

    A process-global truncated-image flag is neither changed nor trusted: refuse
    permissive Pillow settings. Do not mutate that setting concurrently.
    """
    try:
        from PIL import Image, ImageFile
    except ImportError as exc:
        raise RuntimeError("image census requires: pip install 'pop-forensics[images]'") from exc
    if ImageFile.LOAD_TRUNCATED_IMAGES:
        raise ValueError("strict census requires Pillow LOAD_TRUNCATED_IMAGES=False")
    result = {
        "sha256": None,
        "rgb_sha256": None,
        "strict_ok": False,
        "bytes": None,
        "width": None,
        "height": None,
        "format": None,
        "error": None,
        "warnings": [],
    }
    try:
        raw = Path(path).read_bytes()
        result.update(sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))
    except OSError as exc:
        result["error"] = type(exc).__name__
        return result
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            with Image.open(io.BytesIO(raw)) as image:
                # Full decode before accepting dimensions or a pixel digest.
                rgb = image.convert("RGB")
                rgb.load()
                digest = hashlib.sha256()
                digest.update(f"RGB:{rgb.width}:{rgb.height}:".encode())
                digest.update(rgb.tobytes())
                result.update(
                    strict_ok=True,
                    rgb_sha256=digest.hexdigest(),
                    width=rgb.width,
                    height=rgb.height,
                    format=image.format,
                )
        except (OSError, ValueError, Image.DecompressionBombError) as exc:
            result["error"] = type(exc).__name__
        result["warnings"] = sorted({type(w.message).__name__ for w in caught})
    return result


def validate_rows(rows):
    """Require stable identities; no normalization or silent row intersections."""
    if not isinstance(rows, list) or not rows:
        raise ValueError("manifest must be a nonempty JSON list")
    seen = set()
    for row in rows:
        if (
            not isinstance(row, dict)
            or not {"id", "path", "label", "split", "domain", "type"} <= row.keys()
        ):
            raise ValueError("each row requires id, path, label, split, domain, type")
        if any(
            not isinstance(row[k], str) or not row[k]
            for k in ("id", "path", "split", "domain", "type")
        ):
            raise ValueError("identity and metadata fields must be nonempty strings")
        if row["id"] in seen:
            raise ValueError(f"duplicate row ID: {row['id']}")
        seen.add(row["id"])
        if type(row["label"]) is not int or row["label"] not in (0, 1):
            raise ValueError("labels must be binary integers")
    return rows


def census(manifest, image_root):
    """Read relative image paths below image_root; output contains IDs, not paths."""
    from PIL import __version__ as pillow_version

    rows = validate_rows(read_json(manifest))
    inspected, records = {}, []
    for row in rows:
        path = artifact(image_root, row["path"])
        if path not in inspected:
            inspected[path] = inspect_image(path)
        metadata = {k: row[k] for k in ("id", "label", "split", "domain", "type")}
        records.append({**metadata, **inspected[path]})
    return {
        "schema_version": 1,
        "producer": "pop-image-census",
        "manifest_sha256": sha256(manifest),
        "pillow_version": pillow_version,
        "decode": "strict RGB; dimension-prefixed SHA-256; no EXIF transpose",
        "rows": records,
        "count": len(records),
        "strict_ok": sum(r["strict_ok"] for r in records),
    }


def exact_cohort(census_report, train_splits, evaluation_splits):
    """Exclude unreadable rows and training byte/RGB matches before scoring.

    No near-duplicate matching is inferred. Selection exposure can be excluded
    by explicitly adding selection splits to train_splits for a separate scope.
    """
    if not train_splits or not evaluation_splits or set(train_splits) & set(evaluation_splits):
        raise ValueError("nonempty disjoint train/evaluation split selections required")
    rows = census_report["rows"]
    # Reuse metadata validation with anonymous placeholder paths; never expose lab paths.
    validate_rows([{**r, "path": r["id"]} for r in rows])
    for row in rows:
        if type(row.get("strict_ok")) is not bool:
            raise ValueError("census strict_ok must be boolean")
        for key in ("sha256", "rgb_sha256"):
            value = row.get(key)
            if value is not None and (
                not isinstance(value, str)
                or len(value) != 64
                or any(c not in "0123456789abcdef" for c in value)
            ):
                raise ValueError("invalid census content digest")
        if row["strict_ok"] and (not row.get("sha256") or not row.get("rgb_sha256")):
            raise ValueError("decodable census row lacks content hashes")
    present = {r["split"] for r in rows}
    if not set(train_splits + evaluation_splits) <= present:
        raise ValueError("requested split missing from census")
    training = [r for r in rows if r["split"] in train_splits]
    if any(not r["strict_ok"] or not r["sha256"] or not r["rgb_sha256"] for r in training):
        raise ValueError("training content registry incomplete; cannot establish exclusion")
    byte_set = {r["sha256"] for r in training}
    rgb_set = {r["rgb_sha256"] for r in training}
    kept, excluded = [], []
    for row in rows:
        if row["split"] not in evaluation_splits:
            continue
        reasons = []
        if not row["strict_ok"]:
            reasons.append("strict_decode_failed")
        if row["sha256"] in byte_set:
            reasons.append("training_byte_match")
        if row["rgb_sha256"] in rgb_set:
            reasons.append("training_rgb_match")
        if reasons:
            excluded.append({"id": row["id"], "reasons": reasons})
        else:
            if not row["sha256"] or not row["rgb_sha256"]:
                raise ValueError("accepted row lacks content hashes")
            kept.append(row)
    if not kept:
        raise ValueError("no eligible evaluation rows")
    membership = {r["id"]: {k: r[k] for k in ("label", "split", "domain", "type")} for r in kept}
    return {
        "membership": membership,
        "excluded": excluded,
        "byte_content": {"train": sorted(byte_set), "evaluation": [r["sha256"] for r in kept]},
        "rgb_content": {"train": sorted(rgb_set), "evaluation": [r["rgb_sha256"] for r in kept]},
        "cohort_sha256": hashlib.sha256("\n".join(sorted(membership)).encode()).hexdigest(),
    }
