"""Explicit SICA manifest/CSV adapters; no model or dataset code is vendored."""

import csv
import hashlib
from pathlib import Path

from ..evidence import sha256
from ..registration import read_json
from .population import validate_rows
from .scoring import predictions


def identity(source_path, image_root):
    """Map a local image path to a stable opaque ID below the declared root.

    No automatic lab-prefix rewrites: pass a root matching the exported paths,
    or explicitly rewrite your local manifests before importing. Symlinks may
    not escape the root. IDs are SHA-256 of relative POSIX path text, not pixels.
    """
    root = Path(image_root).resolve()
    path = Path(source_path)
    path = path.resolve() if path.is_absolute() else (root / path).resolve()
    if not path.is_relative_to(root):
        raise ValueError("SICA input path is outside the declared image root")
    relative = path.relative_to(root).as_posix()
    return hashlib.sha256(relative.encode()).hexdigest(), relative


def import_manifests(split_sources, image_root):
    """Convert native path/label/domain/mani_type rows to portable census input.

    Each sample occurrence has a distinct row ID; duplicate paths within one
    split are rejected. The same content across splits remains visible to census.
    """
    if not split_sources:
        raise ValueError("at least one named split source required")
    output, receipts = [], []
    for split, source in split_sources.items():
        if not isinstance(split, str) or not split:
            raise ValueError("nonempty split name required")
        rows = read_json(source)
        if not isinstance(rows, list) or not rows:
            raise ValueError("SICA manifest must be a nonempty list")
        seen = set()
        for row in rows:
            if not isinstance(row, dict) or not {"path", "label", "domain"} <= row.keys():
                raise ValueError("SICA row requires path, label, domain")
            key, relative = identity(row["path"], image_root)
            if key in seen:
                raise ValueError("duplicate path within one split")
            seen.add(key)
            label = row["label"]
            if type(label) is not int or label not in (0, 1):
                raise ValueError("native SICA label must be a binary integer")
            fake_type = row.get("mani_type") if label else "__authentic__"
            if not isinstance(fake_type, str) or not fake_type:
                raise ValueError("fake row requires a nonempty mani_type")
            output.append(
                {
                    "id": f"{split}:{key}",
                    "path": relative,
                    "label": label,
                    "split": split,
                    "domain": row["domain"],
                    "type": fake_type,
                }
            )
        receipts.append({"split": split, "sha256": sha256(source), "rows": len(rows)})
    validate_rows(output)
    return output, receipts


def import_predictions(source, image_root, split):
    """Map path-keyed SICA predictions to the same split-scoped IDs.

    Return plain CSV-ready dictionaries. Labels are retained when present.
    No paths, logits or arbitrary source metadata are copied to the output.
    """
    with open(source, newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    # Validate all source probabilities/identities before conversion.
    validated = predictions(source)
    if not rows or "path" not in rows[0]:
        raise ValueError("native prediction export requires path column")
    output, seen = [], set()
    for row in rows:
        key, _ = identity(row["path"], image_root)
        key = f"{split}:{key}"
        if key in seen:
            raise ValueError("duplicate normalized SICA prediction identity")
        seen.add(key)
        record = {"id": key, "probability": validated[row.get("id", row["path"])]["score"]}
        if "label" in row:
            record["label"] = int(row["label"])
        output.append(record)
    return output
