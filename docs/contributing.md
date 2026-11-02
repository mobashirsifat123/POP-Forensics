--8<-- "CONTRIBUTING.md"

## Build this documentation

Documentation dependencies are separate from runtime dependencies:

```sh
python -m pip install -r requirements-docs.txt
python -m pip install -e .
python scripts/generate_demo.py
python scripts/generate_visuals.py
mkdocs build --strict
mkdocs serve
```

Open the local URL printed by MkDocs. The site uses Material for MkDocs, local system fonts and original SVG assets. Search is built locally; no analytics or external font requests are configured.

The `Documentation` workflow builds the site and uploads a preview artifact on pull requests and this design branch. Pages deployment is gated to a manual dispatch on main after approval and Pages setup. The stable v0.1.1 release is unchanged.
