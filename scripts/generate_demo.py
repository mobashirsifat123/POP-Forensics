"""Regenerate documentation transcripts and receipts using the real CLI.

No historical evidence or source-package implementation is changed. Run from
repository root after installing POP: python scripts/generate_demo.py
"""

import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "output" / "documentation-demo"
DEST = ROOT / "docs" / "demonstration"


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)
    summaries = {}
    for name, expected_code in (("pass", 0), ("fail", 1), ("unresolved", 2)):
        case = WORK / name
        if case.exists():
            shutil.rmtree(case)
        shutil.copytree(ROOT / "examples/synthetic/package", case)
        data = json.loads((case / "evidence.json").read_text())
        if name == "fail":
            data["baseline-delta"] = 0
        if name == "unresolved":
            del data["complete"]
        (case / "evidence.json").write_text(json.dumps(data, indent=2) + "\n")
        command = [
            sys.executable,
            "-m",
            "popverify.cli",
            "verify",
            "registration.json",
            "evidence.json",
        ]
        human = subprocess.run(command, cwd=case, capture_output=True, text=True)
        machine = subprocess.run(command + ["--json"], cwd=case, capture_output=True, text=True)
        if human.returncode != expected_code or machine.returncode != expected_code:
            raise RuntimeError(f"{name}: unexpected exit codes: {human.stderr} {machine.stderr}")
        receipt = json.loads(machine.stdout)
        if receipt["outcome"] != name.upper():
            raise RuntimeError(f"{name}: unexpected outcome")
        (DEST / f"{name}.txt").write_text(human.stdout)
        (DEST / f"{name}.json").write_text(machine.stdout)
        summaries[name] = {
            "outcome": receipt["outcome"],
            "exit_code": machine.returncode,
            "gates": receipt["gates"],
            "inputs": receipt["inputs"],
        }
    (DEST / "summary.json").write_text(json.dumps(summaries, indent=2) + "\n")
    print(
        json.dumps(
            {
                key: {"outcome": val["outcome"], "exit_code": val["exit_code"]}
                for key, val in summaries.items()
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
