# Contributing

Use Python 3.10+, install `python -m pip install -e '.[dev]'`, and run the commands in the README before opening a pull request. Include a minimal synthetic regression for behavioral changes. Preserve FAIL > UNRESOLVED > PASS priority and document schema changes. Keep dependencies and abstractions small.

Report bugs through GitHub issues with package/Python versions, registration shape and a synthetic evidence package. Never include credentials, restricted data, private sample paths or third-party weights. Security-sensitive reports should first use GitHub private vulnerability reporting if the repository offers it; otherwise report the issue category without exploit data and ask the maintainer for a private channel.

No guarantee of release cadence or support SLA is made. Version 0.1 is an experimental reference implementation; breaking evidence-schema changes require a schema-version increment. Research claims need independent validation beyond software conformance.
