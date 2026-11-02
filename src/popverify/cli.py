"""Portable CLI. Exit codes: PASS=0, FAIL=1, UNRESOLVED=2, invalid invocation=3."""

import argparse
import json
import sys
from pathlib import Path

from .registration import read_json, validate
from .verification import verify


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="POP comparison verification (reference implementation)"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("verify", help="verify registered evidence")
    run.add_argument("registration", type=Path)
    run.add_argument("evidence", type=Path)
    run.add_argument("--json", action="store_true", help="print machine-readable receipt")
    run.add_argument("--output", type=Path, help="also save JSON receipt")
    lint = sub.add_parser("validate", help="validate a registration without evaluating evidence")
    lint.add_argument("registration", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "validate":
            validate(read_json(args.registration))
            print("Registration valid")
            return 0
        if args.output and args.output.resolve() in {
            args.registration.resolve(),
            args.evidence.resolve(),
        }:
            raise ValueError("output cannot overwrite a verification input")
        receipt = verify(args.registration, args.evidence)
        rendered = json.dumps(receipt, indent=2, allow_nan=False) + "\n"
        if args.output:
            # Exclusive creation prevents accidental destruction of evidence/artifacts.
            with args.output.open("x", encoding="utf-8") as stream:
                stream.write(rendered)
        if args.json:
            print(rendered, end="")
        else:
            print(f"{receipt['outcome']} | {receipt['scope']}")
            for result in receipt["assertions"]:
                print(
                    f"  {result['gate']} {result['id']}: {result['outcome']} — {result['reason']}"
                )
        return {"PASS": 0, "FAIL": 1, "UNRESOLVED": 2}[receipt["outcome"]]
    except (OSError, ValueError, TypeError) as exc:
        print(f"popverify: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
