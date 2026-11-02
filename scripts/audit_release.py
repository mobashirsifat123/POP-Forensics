"""Bounded prepublication scan of Git-indexed files; not a secret-scanner guarantee."""

import json
from pathlib import Path
import re
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
paths = subprocess.check_output(["git", "ls-files", "-z"], cwd=root).decode().split("\0")
patterns = {
    "github_token": re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "cloud_key": re.compile(r"AKIA[A-Z0-9]{16}"),
    "private_absolute_path": re.compile(r"/(?:Users|home|mnt)/[A-Za-z0-9_]"),
}
findings = []
files = [p for p in paths if p]
for name in files:
    path = root / name
    if path.is_symlink():
        findings.append({"file": name, "issue": "symlink"})
        continue
    if path.stat().st_size > 2_000_000:
        findings.append({"file": name, "issue": "oversized"})
    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        findings.append({"file": name, "issue": "binary file requires review"})
        continue
    for kind, pattern in patterns.items():
        if pattern.search(content):
            findings.append({"file": name, "issue": kind})
print(json.dumps({"files_scanned": len(files), "findings": findings}, indent=2))
sys.exit(bool(findings))
