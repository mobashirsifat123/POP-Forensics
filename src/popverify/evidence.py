"""Local JSON artifacts only: no pickle, remote URIs or executable adapters."""

import hashlib
from pathlib import Path

from .registration import read_json


def artifact(root, relative):
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ValueError("artifact must be a relative path")
    root = Path(root).resolve()
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise ValueError("artifact escapes evidence directory")
    return path


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def vector(root, relative):
    from .registration import number

    result = read_json(artifact(root, relative))
    if not isinstance(result, list) or not result or not all(number(x) for x in result):
        raise ValueError("prediction vectors must be nonempty finite numeric JSON lists")
    return result
