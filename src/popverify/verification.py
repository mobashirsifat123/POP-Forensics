"""Evidence-bound receipts with contradiction-first reduction."""

from pathlib import Path

from .checks import check
from .evidence import sha256
from .registration import read_json, validate


def reduce_outcomes(outcomes):
    values = list(outcomes)
    if "FAIL" in values:
        return "FAIL"
    if not values or "UNRESOLVED" in values:
        return "UNRESOLVED"
    return "PASS"


def verify(registration, evidence):
    """Verify JSON paths; invalid registrations raise ValueError.

    Missing/malformed evidence is UNRESOLVED, positive contradictions are FAIL.
    Every assertion is evaluated even after one fails. Receipt hashes bind input
    bytes and examined artifacts; they are not independent truth attestations.
    """
    registration, evidence = Path(registration), Path(evidence)
    reg = validate(read_json(registration))
    input_hashes = {"registration": sha256(registration)}
    issue = None
    try:
        input_hashes["evidence"] = sha256(evidence)
        records = read_json(evidence)
        if not isinstance(records, dict):
            raise ValueError("evidence must be an object")
    except (OSError, ValueError) as exc:
        records, issue = {}, f"evidence unavailable or malformed: {exc}"
    results, artifacts = [], {}
    for a in reg["assertions"]:
        outcome, reason = "UNRESOLVED", issue or f"missing evidence: {a['evidence']}"
        if a["evidence"] in records:
            try:
                observed = records[a["evidence"]]
                valid, reason = check(a, observed, evidence.parent)
                outcome = "PASS" if valid else "FAIL"
                if a["kind"] in {"digest", "initialization", "reconstruction"}:
                    from .evidence import artifact

                    names = [observed]
                    if a["kind"] == "reconstruction":
                        names.append(a["expected"])
                    for name in names:
                        artifacts[name] = sha256(artifact(evidence.parent, name))
            except (OSError, ValueError, TypeError, KeyError, OverflowError) as exc:
                reason = f"insufficient evidence: {exc}"
                outcome = "UNRESOLVED"
        results.append(
            {
                "id": a["id"],
                "gate": a["gate"],
                "kind": a["kind"],
                "outcome": outcome,
                "reason": reason,
            }
        )
    return {
        "schema_version": 1,
        "implementation": "popverify-reference-0.1.0",
        "scope": reg["scope"],
        "outcome": reduce_outcomes(r["outcome"] for r in results),
        "gates": {
            g: reduce_outcomes(r["outcome"] for r in results if r["gate"] == g)
            for g in ("P1", "O", "P2")
        },
        "inputs": input_hashes,
        "artifacts": artifacts,
        "assertions": results,
    }
