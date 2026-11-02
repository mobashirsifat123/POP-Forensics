"""Evidence-producing commands; independent from the original verifier CLI.

Run python -m popverify.producers.cli --help. These emit observations/diagnostics,
not registered POP decisions. Invalid input returns exit code 3.
"""

import argparse
import json
from pathlib import Path
import sys

from ..registration import read_json
from .io import write_json
from .logs import summarize_training_log
from .sica import import_manifests, import_predictions
import csv
from .population import census, exact_cohort
from .provenance import classify_reconstruction, compare_predictions, inspect_cache, publish_cache
from .scoring import compare


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="POP evidence producers from the SICA audit workflow"
    )
    commands = parser.add_subparsers(dest="command", required=True)
    image = commands.add_parser("census", help="strict byte/RGB image census")
    image.add_argument("manifest", type=Path)
    image.add_argument("image_root", type=Path)
    cohort = commands.add_parser(
        "cohort", help="exclude unreadable and exact training-matched rows"
    )
    cohort.add_argument("census", type=Path)
    cohort.add_argument("--train-split", action="append", required=True)
    cohort.add_argument("--evaluation-split", action="append", required=True)
    score = commands.add_parser("score", help="score both arms on an explicit cohort")
    score.add_argument("cohort", type=Path)
    score.add_argument("baseline", type=Path)
    score.add_argument("candidate", type=Path)
    score.add_argument("expected_types", type=Path)
    publish = commands.add_parser("publish-cache", help="atomically publish a new cache directory")
    publish.add_argument("destination", type=Path)
    publish.add_argument("files", nargs="+", type=Path)
    check = commands.add_parser("inspect-cache", help="check committed cache bytes")
    check.add_argument("directory", type=Path)
    reconstruct = commands.add_parser(
        "reconstruction", help="compare independently produced prediction CSVs"
    )
    reconstruct.add_argument("saved", type=Path)
    reconstruct.add_argument("reconstructed", type=Path)
    reconstruct.add_argument("--tolerance", type=float, required=True)
    reconstruct.add_argument("--alternative", type=Path)
    native = commands.add_parser("sica-manifests", help="convert native SICA split manifests")
    native.add_argument("image_root", type=Path)
    native.add_argument("--split", action="append", required=True, help="NAME=MANIFEST_JSON")
    native_predictions = commands.add_parser("sica-predictions", help="convert path-keyed SICA CSV")
    native_predictions.add_argument("input", type=Path)
    native_predictions.add_argument("image_root", type=Path)
    native_predictions.add_argument("--split", required=True)
    logs = commands.add_parser("training-log", help="summarize retained DE3 JSONL counters")
    logs.add_argument("input", type=Path)
    logs.add_argument("--epoch", action="append", type=int, required=True)
    for sub in (
        image,
        cohort,
        score,
        publish,
        check,
        reconstruct,
        native,
        native_predictions,
        logs,
    ):
        sub.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.output.exists() or args.output.is_symlink():
            raise FileExistsError("output already exists")
        if not args.output.parent.is_dir():
            raise ValueError("output parent must exist")
        if args.command == "sica-manifests":
            sources = {}
            for item in args.split:
                name, path = item.split("=", 1)
                if name in sources:
                    raise ValueError("duplicate split name")
                sources[name] = path
            result, _ = import_manifests(sources, args.image_root)
        elif args.command == "sica-predictions":
            result = import_predictions(args.input, args.image_root, args.split)
            with args.output.open("x", newline="", encoding="utf-8") as stream:
                writer = csv.DictWriter(stream, fieldnames=list(result[0]))
                writer.writeheader()
                writer.writerows(result)
            print(json.dumps({"command": args.command, "rows": len(result)}))
            return 0
        elif args.command == "training-log":
            result = summarize_training_log(args.input, args.epoch)
        elif args.command == "census":
            result = census(args.manifest, args.image_root)
        elif args.command == "cohort":
            result = exact_cohort(read_json(args.census), args.train_split, args.evaluation_split)
        elif args.command == "score":
            result = compare(
                read_json(args.cohort),
                args.baseline,
                args.candidate,
                read_json(args.expected_types),
            )
        elif args.command == "publish-cache":
            names = {p.name: p for p in args.files}
            if len(names) != len(args.files):
                raise ValueError("source basenames must be unique")
            result = publish_cache(args.destination, names)
        elif args.command == "inspect-cache":
            result = inspect_cache(args.directory)
        elif args.alternative:
            result = classify_reconstruction(
                args.saved, args.reconstructed, args.alternative, args.tolerance
            )
        else:
            result = compare_predictions(args.saved, args.reconstructed, args.tolerance)
        write_json(args.output, result)
        print(json.dumps({"command": args.command, "output": str(args.output)}, indent=2))
        return 0
    except (OSError, ValueError, TypeError, KeyError, RuntimeError, ImportError) as exc:
        print(f"POP evidence producer: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
