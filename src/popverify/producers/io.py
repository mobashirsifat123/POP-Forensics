"""Explicit, non-overwriting JSON outputs for evidence-producing commands."""

import json
import os
from pathlib import Path
import tempfile


def write_json(path, value):
    """Create a new JSON file; never overwrite a registration or prior receipt."""
    data = json.dumps(value, indent=2, allow_nan=False) + "\n"
    with Path(path).open("x", encoding="utf-8") as stream:
        stream.write(data)


def atomic_json(path, value):
    """Publish new JSON bytes atomically on the same filesystem.

    A hard-link commit refuses an existing destination; no platform-specific
    replace operation can silently overwrite a prior evidence artifact.
    """
    path = Path(path)
    data = (json.dumps(value, indent=2, allow_nan=False) + "\n").encode()
    fd, temp = tempfile.mkstemp(prefix=".pop-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temp, path)
    finally:
        Path(temp).unlink(missing_ok=True)
