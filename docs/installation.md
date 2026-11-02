# Installation

Clone the repository and run `python3 -m venv .venv`, activate it, then `python -m pip install .`. Python 3.10+ is required. No GPU, detector dependencies, NumPy or external service is required. Do not use `pip install pop-forensics` from PyPI: this release is distributed through this Git repository.

For development, use `python -m pip install -e '.[dev]'`. The `dev` extra installs build tooling and Ruff. Tests use standard-library unittest. A regular install exposes `popverify` in the activated environment. If it is not found, confirm the environment is active or invoke `.venv/bin/popverify`.

The locally tested version and packaging results are recorded in [test_report.md](test_report.md). CI declares additional Python targets; their status must be checked in Actions. Dependency ranges for development tools are not a locked environment. Runtime uses only Python's standard library.
