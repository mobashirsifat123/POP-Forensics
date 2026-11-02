"""Generate original POP SVG identity and diagrams, using the real demo receipt."""

from pathlib import Path
import json
import html

R = Path(__file__).resolve().parents[1]
A = R / "docs/assets"
NAVY = "#112C46"
BLUE = "#245CBE"
TEAL = "#087F80"
SLATE = "#536582"
LINE = "#DCE3E8"
PAPER = "#F7F8F5"


def t(x, y, s, size=20, fill=NAVY, weight="400", family="Arial, Helvetica, sans-serif", extra=""):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" font-weight="{weight}" font-family="{family}" {extra}>{html.escape(s)}</text>'


def rect(x, y, w, h, fill, stroke="none", r=0):
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}"/>'
    )


def path(d, c=LINE, w=2):
    return f'<path d="{d}" fill="none" stroke="{c}" stroke-width="{w}"/>'


def line(x, y, xx, yy, c=LINE, w=2):
    return path(f"M{x} {y}L{xx} {yy}", c, w)


def circle(x, y, r, c):
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{c}"/>'


def svg(name, w, h, title, desc, body, folder="diagrams"):
    (A / folder / name).write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="title desc"><title id="title">{html.escape(title)}</title><desc id="desc">{html.escape(desc)}</desc>{body}</svg>\n'
    )


def mark(x=0, y=0, scale=1, colors=(NAVY, BLUE, TEAL)):
    return (
        f'<g transform="translate({x} {y}) scale({scale})" fill="none" stroke-width="9" stroke-linecap="square" stroke-linejoin="round">'
        + "".join(
            [
                f'<path d="M8 58V10H24C48 10 48 38 24 38H8" stroke="{colors[0]}"/>',
                f'<rect x="57" y="10" width="38" height="48" rx="19" stroke="{colors[1]}"/>',
                f'<path d="M114 58V10H130C154 10 154 38 130 38H114" stroke="{colors[2]}"/>',
            ]
        )
        + "</g>"
    )


svg(
    "logo.svg",
    164,
    76,
    "POP logo",
    "Three original geometric letter paths for Population, Objective and Provenance.",
    mark(4, 4),
    "brand",
)
svg(
    "favicon.svg",
    80,
    80,
    "POP mark",
    "Three evidence paths converge into an inspectable receipt.",
    rect(0, 0, 80, 80, NAVY, r=12)
    + path("M16 20H34V40H62", "#8CB7FF", 5)
    + path("M16 40H62", "#59D2C4", 5)
    + path("M16 60H34V40", "#B6C3D5", 5)
    + circle(62, 40, 5, "#FFFFFF"),
    "brand",
)
# Hero, the right-hand diagram is a schematic (no fabricated scientific outcome).
for name, h in [("hero.svg", 400), ("social-preview.svg", 640)]:
    off = (h - 400) // 2
    b = rect(0, 0, 1280, h, NAVY)
    for x in range(770, 1280, 40):
        b += line(x, off + 35, x, off + 365, "#1A3851", 1)
    for y in range(off + 45, off + 380, 40):
        b += line(755, y, 1240, y, "#1A3851", 1)
    b += mark(60, off + 45, 0.52, ("#FFFFFF", "#8CB7FF", "#59D2C4"))
    b += t(
        60, off + 150, "POP-Forensics", 68, "#FFFFFF", "600", "Georgia, 'Times New Roman', serif"
    )
    b += t(63, off + 200, "Make the evidence inspectable.", 26, "#B8D2E8")
    b += t(
        63,
        off + 260,
        "POPULATION  /  OBJECTIVE  /  PROVENANCE",
        14,
        "#59D2C4",
        "600",
        extra='letter-spacing="1.5"',
    )
    b += t(63, off + 304, "A comparison-scoped verification toolkit", 20, "#E3EAF0")
    b += t(63, off + 332, "for image-forensics research.", 20, "#E3EAF0")
    for y, label, color in [(110, "P1", "#8CB7FF"), (200, "O", "#59D2C4"), (290, "P2", "#B6C3D5")]:
        b += rect(805, off + y - 22, 62, 44, "#183B56", r=4) + t(
            824, off + y + 6, label, 19, color, "600"
        )
        b += path(f"M867 {off + y}H940V{off + 200}H1000", color, 2)
    b += rect(1000, off + 135, 196, 135, "#FFFFFF", r=4) + t(
        1020, off + 166, "EVIDENCE RECEIPT", 12, SLATE, "600"
    )
    for y, w in [(184, 140), (202, 95), (220, 120)]:
        b += line(1020, off + y, 1020 + w, off + y, LINE, 4)
    b += t(1020, off + 248, "scope · hashes · assertions", 10, TEAL, "400")
    svg(
        name,
        1280,
        h,
        "POP-Forensics — Make the evidence inspectable",
        "Population, objective and provenance evidence converge into a comparison receipt.",
        b,
        "brand",
    )
# Overview
b = rect(0, 0, 1120, 270, "#FFFFFF") + t(
    28, 38, "ONE REGISTERED COMPARISON. ONE INSPECTABLE EVIDENCE CHAIN.", 14, SLATE, "600"
)
steps = [
    (28, 180, "01", "Register", "Arms, rows, weights", "and tolerances"),
    (248, 180, "02", "Collect", "Producer records", "and input artifacts"),
    (468, 210, "03", "Verify", "P1  /  O  /  P2", "Evaluate every assertion"),
    (718, 160, "04", "Decide", "Contradiction-first", "reduction"),
    (918, 174, "05", "Retain", "Outcome, hashes", "and assertion reasons"),
]
for i, (x, w, n, title, a, c) in enumerate(steps):
    b += (
        line(x, 68, x + w, 68, TEAL if i == 2 else LINE, 3)
        + t(x, 101, n, 14, TEAL if i == 2 else SLATE, "600")
        + t(x, 139, title, 27, NAVY, "600")
        + t(x, 174, a, 16)
        + t(x, 198, c, 16)
    )
    if i < 4:
        b += t(x + w + 12, 139, "→", 22, SLATE)
svg(
    "overview.svg",
    1120,
    230,
    "POP verification overview",
    "Register the comparison, collect evidence, verify P1 O P2, reduce decisions and retain a hashed receipt.",
    b,
)
# Gate pillars
b = rect(0, 0, 1120, 350, "#FFFFFF")
for x, key, col, title, q, ls in [
    (
        28,
        "P1",
        BLUE,
        "Population & estimand",
        "Which observations define the claim?",
        ["Row, label and split membership", "Content exclusions", "Registered evaluation weights"],
    ),
    (
        400,
        "O",
        TEAL,
        "Objective & optimization",
        "Was the intended training realized?",
        [
            "Probability-target validity",
            "Successful / skipped update counts",
            "Initialization and parameter changes",
        ],
    ),
    (
        772,
        "P2",
        SLATE,
        "Prediction provenance",
        "Were the intended inputs used?",
        ["Cache completion record", "Artifact digests", "External prediction reconstruction"],
    ),
]:
    b += (
        line(x, 25, x + 320, 25, col, 4)
        + t(x, 93, key, 54, col, "600", "Georgia, serif")
        + t(x, 142, title, 23, NAVY, "600")
        + t(x, 180, q, 15, SLATE)
    )
    for j, s in enumerate(ls):
        b += t(x, 226 + j * 29, s, 16)
svg(
    "three-gates.svg",
    1120,
    330,
    "Three POP evidence dimensions",
    "Population and estimand, objective and realized optimization, prediction-input provenance; each has explicit evidence checks.",
    b,
)
# Decision priority
b = (
    rect(0, 0, 1120, 382, "#FFFFFF")
    + t(30, 40, "DECISION PRIORITY", 14, SLATE, "600")
    + t(30, 80, "A contradiction always takes priority.", 28, NAVY, "600", "Georgia, serif")
)
for y, n, q, out, c, meaning in [
    (
        136,
        "1",
        "Any assertion contradicted?",
        "FAIL",
        "#B13B3B",
        "Even when other evidence is missing",
    ),
    (
        222,
        "2",
        "Otherwise, any evidence missing or unusable?",
        "UNRESOLVED",
        "#886010",
        "No contradiction has been established",
    ),
    (
        308,
        "3",
        "Otherwise, every required assertion satisfied.",
        "PASS",
        TEAL,
        "Acceptance is scoped to the registration",
    ),
]:
    b += (
        line(30, y - 25, 1090, y - 25, LINE, 1)
        + t(30, y + 8, n, 19, SLATE, "600")
        + t(77, y + 8, q, 20)
        + rect(684, y - 16, 185, 39, c, r=3)
        + t(701, y + 9, out, 16, "#FFFFFF", "600")
        + t(892, y + 5, meaning.split(" ")[0] if False else "", 12)
    )
    b += t(77, y + 34, meaning, 14, SLATE)
svg(
    "decisions.svg",
    1120,
    380,
    "Contradiction-first POP decision logic",
    "FAIL if contradicted; otherwise UNRESOLVED if evidence is missing; otherwise PASS. All assertions are evaluated.",
    b,
)
# Software actual modules
b = rect(0, 0, 1120, 365, "#FFFFFF") + t(
    28, 39, "SMALL MODULES. EXPLICIT RESPONSIBILITIES.", 14, SLATE, "600"
)
boxes = [
    (28, 90, 180, 100, "cli.py", "Commands & exit codes"),
    (265, 90, 240, 100, "registration.py", "Validate the contract"),
    (265, 230, 240, 100, "evidence.py", "Local JSON, paths, SHA-256"),
    (575, 90, 240, 100, "verification.py", "Evaluate all assertions"),
    (575, 230, 240, 100, "checks.py", "Semantic gate checks"),
    (885, 90, 205, 100, "JSON receipt", "Outcomes & reasons"),
]
for x, y, w, h, title, sub in boxes:
    b += (
        rect(x, y, w, h, PAPER, LINE, r=3)
        + t(x + 18, y + 34, title, 18, NAVY, "600", "Menlo, Consolas, monospace")
        + t(x + 18, y + 66, sub, 14, SLATE)
    )
b += (
    path("M208 140H265", BLUE, 2)
    + path("M505 140H575", BLUE, 2)
    + path("M505 280H540V162H575", TEAL, 2)
    + path("M695 190V230", TEAL, 2)
    + path("M815 140H885", BLUE, 2)
)
b += t(
    28,
    344,
    "metrics.py supplies AUC helpers separately; it does not automatically score evidence.",
    15,
    SLATE,
)
svg(
    "architecture.svg",
    1120,
    370,
    "POP software architecture",
    "CLI validates a registration and supplies local evidence to verification and semantic checks; a JSON receipt records results. Metrics are separate helpers.",
    b,
)
# Receipt values taken from actual generated CLI output
r = json.loads((R / "docs/demonstration/pass.json").read_text())
b = rect(0, 0, 1120, 420, "#FFFFFF") + rect(28, 24, 680, 366, PAPER, LINE, r=4)
b += (
    t(52, 62, "EVIDENCE RECEIPT", 13, SLATE, "600")
    + t(52, 101, r["scope"], 23, NAVY, "600", "Georgia, serif")
    + line(52, 120, 684, 120, LINE)
)
b += t(52, 152, "implementation", 15, SLATE, "400", "Menlo, monospace") + t(
    242, 152, r["implementation"], 15, NAVY, "400", "Menlo, monospace"
)
for y, key in [(187, "registration"), (218, "evidence")]:
    b += t(52, y, key + " SHA-256", 15, SLATE, "400", "Menlo, monospace") + t(
        242, y, r["inputs"][key][:26] + "…", 15, NAVY, "400", "Menlo, monospace"
    )
for i, g in enumerate(["P1", "O", "P2"]):
    b += t(52 + i * 200, 269, g + "  " + r["gates"][g], 18, TEAL, "600", "Menlo, monospace")
b += (
    line(52, 291, 684, 291, LINE)
    + t(52, 330, str(len(r["assertions"])) + " assertions evaluated", 17, NAVY)
    + t(52, 360, "All required registered assertions satisfied.", 14, SLATE)
)
b += (
    t(755, 74, r["outcome"], 48, TEAL, "600", "Georgia, serif")
    + t(755, 119, "A real synthetic CLI receipt.", 19, NAVY, "600")
    + t(755, 165, "Registration metadata", 17, SLATE)
    + t(755, 203, "Input and artifact hashes", 17, SLATE)
    + t(755, 241, "Per-assertion outcomes", 17, SLATE)
    + t(755, 279, "Reasons for every decision", 17, SLATE)
    + t(755, 337, "Hashes shown abbreviated.", 14, SLATE)
    + t(755, 361, "Full JSON is available in the demo.", 14, SLATE)
)
svg(
    "receipt.svg",
    1120,
    420,
    "An actual POP synthetic evidence receipt",
    "Generated from the PASS demonstration receipt; hashes are abbreviated for display. Includes scope, implementation, 17 assertions and per-gate decisions.",
    b,
)
