"""Check built-site local links/images and the README's repository-relative assets."""

from html.parser import HTMLParser
from pathlib import Path
import re
from urllib.parse import unquote, urljoin, urlsplit

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.targets = []
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.add(attrs["id"])
        for key in ("href", "src"):
            if key in attrs:
                self.targets.append(attrs[key])


def main():
    failures = []
    count = 0
    parsers = {}
    for file in SITE.rglob("*.html"):
        parser = Links()
        parser.feed(file.read_text())
        parsers[file.resolve()] = parser
    for file, parser in parsers.items():
        source = "/POP-Forensics/" + file.relative_to(SITE.resolve()).as_posix()
        for target in parser.targets:
            if target.startswith(("http:", "https:", "mailto:", "data:", "javascript:")):
                continue
            url = urlsplit(urljoin(source, target))
            path = unquote(url.path).removeprefix("/POP-Forensics/")
            dest = SITE / path
            if dest.is_dir():
                dest /= "index.html"
            if not dest.exists():
                failures.append(f"{file.relative_to(SITE)}: missing {target}")
            elif (
                url.fragment
                and dest.suffix == ".html"
                and unquote(url.fragment) not in parsers[dest.resolve()].ids
            ):
                failures.append(f"{file.relative_to(SITE)}: missing anchor {target}")
            count += 1
    readme = (ROOT / "README.md").read_text()
    targets = re.findall(r'\]\(([^)]+)\)|(?:src|href)="([^"]+)"', readme)
    for pair in targets:
        target = next(v for v in pair if v)
        if not target.startswith(("https:", "http:", "#")):
            if not (ROOT / unquote(target).split("#")[0]).exists():
                failures.append(f"README: missing {target}")
    if failures:
        raise SystemExit("\n".join(failures))
    print(f"Checked {len(parsers)} HTML pages, {count} local targets and README links: PASS")


if __name__ == "__main__":
    main()
