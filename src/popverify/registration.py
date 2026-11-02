"""Strict, versioned registration contract and JSON input boundary."""

import json
import math
from pathlib import Path

REQUIRED = {
    "P1": {"membership", "disjoint", "weights"},
    "O": {"targets", "updates", "parameter_change", "initialization"},
    "P2": {"completion", "digest", "reconstruction"},
}
KINDS = set().union(*REQUIRED.values()) | {"lineage", "attribution"}


class RegistrationError(ValueError):
    """The declared scope cannot be evaluated safely or unambiguously."""


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def read_json(path):
    """Reject duplicate keys and nonstandard NaN/Infinity JSON literals."""

    def invalid(value):
        raise ValueError(f"nonfinite JSON literal: {value}")

    return json.loads(
        Path(path).read_text(encoding="utf-8"),
        object_pairs_hook=_unique_pairs,
        parse_constant=invalid,
    )


def number(value):
    try:
        return type(value) in (int, float) and math.isfinite(value)
    except OverflowError:
        return False


def validate(reg):
    if not isinstance(reg, dict) or set(reg) != {"schema_version", "scope", "arms", "assertions"}:
        raise RegistrationError(
            "registration requires schema_version, scope, arms, assertions only"
        )
    if type(reg["schema_version"]) is not int or reg["schema_version"] != 1:
        raise RegistrationError("unsupported registration schema_version")
    if not isinstance(reg["scope"], str) or not reg["scope"].strip():
        raise RegistrationError("scope must be a nonempty string")
    arms = reg["arms"]
    if (
        not isinstance(arms, list)
        or len(arms) != 2
        or any(not isinstance(a, str) or not a.strip() for a in arms)
        or len(set(arms)) != 2
    ):
        raise RegistrationError("arms must name two distinct models")
    assertions = reg["assertions"]
    if not isinstance(assertions, list) or not assertions:
        raise RegistrationError("assertions must be a nonempty list")
    ids, coverage = set(), {g: set() for g in REQUIRED}
    per_arm = {arm: set() for arm in arms}
    arm_kinds = {"targets", "updates", "parameter_change", "initialization", "reconstruction"}
    for a in assertions:
        if (
            not isinstance(a, dict)
            or set(a) - {"id", "gate", "kind", "evidence", "expected", "tolerance", "arm"}
            or not {"id", "gate", "kind", "evidence", "expected"} <= set(a)
        ):
            raise RegistrationError("each assertion requires id, gate, kind, evidence, expected")
        if not isinstance(a["id"], str) or not a["id"] or a["id"] in ids:
            raise RegistrationError("assertion IDs must be nonempty and unique")
        ids.add(a["id"])
        if (
            not isinstance(a["gate"], str)
            or not isinstance(a["kind"], str)
            or a["gate"] not in REQUIRED
            or a["kind"] not in KINDS
        ):
            raise RegistrationError(f"unknown gate/kind for {a['id']}")
        if a["kind"] not in REQUIRED[a["gate"]] and a["kind"] not in {"lineage", "attribution"}:
            raise RegistrationError(f"kind belongs to another gate: {a['id']}")
        if not isinstance(a["evidence"], str) or not a["evidence"]:
            raise RegistrationError("evidence must be a top-level evidence-record key")
        tol = a.get("tolerance", 0)
        if not number(tol) or tol < 0:
            raise RegistrationError("tolerance must be finite and nonnegative")
        expected = a["expected"]
        kind = a["kind"]
        if kind in arm_kinds:
            if a.get("arm") not in arms:
                raise RegistrationError(f"{kind} requires a registered arm")
            per_arm[a["arm"]].add(kind)
        if kind in {"disjoint", "completion", "lineage"} and expected is not True:
            raise RegistrationError(f"{kind} expected must be true")
        if kind in {"membership", "weights", "updates", "targets"} and not isinstance(
            expected, dict
        ):
            raise RegistrationError(f"{kind} expected must be an object")
        if kind == "membership" and (
            not expected or any(not isinstance(v, dict) for v in expected.values())
        ):
            raise RegistrationError(
                "membership expected maps row IDs to registered label/split metadata"
            )
        if kind == "weights" and (
            not expected
            or any(not number(v) or v < 0 for v in expected.values())
            or not math.isclose(sum(expected.values()), 1, abs_tol=1e-12)
        ):
            raise RegistrationError("weights must be nonnegative and sum to one")
        if kind == "targets" and (
            set(expected) != {"dtype", "min", "max"}
            or not isinstance(expected["dtype"], str)
            or not number(expected["min"])
            or not number(expected["max"])
            or not 0 <= expected["min"] <= expected["max"] <= 1
        ):
            raise RegistrationError("targets requires dtype and probability bounds within [0,1]")
        if kind == "updates" and (
            set(expected) != {"successful", "max_skipped", "max_nonfinite"}
            or any(type(v) is not int or v < 0 for v in expected.values())
            or expected["successful"] == 0
        ):
            raise RegistrationError(
                "updates requires positive successful count and nonnegative maxima"
            )
        if kind == "parameter_change" and (not number(expected) or expected <= 0):
            raise RegistrationError("parameter_change expected must be a positive minimum L2 delta")
        if kind in {"digest", "initialization"} and (
            not isinstance(expected, str)
            or len(expected) != 64
            or any(c not in "0123456789abcdef" for c in expected)
        ):
            raise RegistrationError(f"{kind} expected must be a lowercase SHA-256 digest")
        if kind == "reconstruction" and (not isinstance(expected, str) or not expected):
            raise RegistrationError("reconstruction expected names the saved prediction JSON file")
        if kind == "attribution" and (type(expected) is not int or expected != 1):
            raise RegistrationError("attribution expected must be 1 changed factor")
        coverage[a["gate"]].add(kind)
    for gate, required in REQUIRED.items():
        if required - coverage[gate]:
            raise RegistrationError(
                f"{gate} missing required checks: {sorted(required - coverage[gate])}"
            )
    for arm, kinds in per_arm.items():
        if arm_kinds - kinds:
            raise RegistrationError(f"{arm} missing required checks: {sorted(arm_kinds - kinds)}")
    return reg
