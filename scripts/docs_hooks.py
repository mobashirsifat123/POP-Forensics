"""Use the generated CLI transcript in the homepage instead of invented output."""

import html
from pathlib import Path


def on_env(env, config, files):
    transcript = Path("docs/demonstration/pass.txt").read_text()
    lines = transcript.splitlines()
    selected = [lines[0], ""] + [
        line
        for line in lines
        if any(key in line for key in ("P1 membership:", "O baseline-updates:", "P2 cache:"))
    ]
    env.globals["pop_demo_html"] = html.escape("\n".join(selected)).replace(
        "PASS", '<span class="pop-terminal-pass">PASS</span>'
    )
    return env
