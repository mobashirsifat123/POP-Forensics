# CLI reference

The executable is `popverify`; the distribution is `pop-forensics`. Install from the repository or a release asset; no PyPI distribution is claimed.

## Validate a registration

```sh
popverify validate REGISTRATION
```

Checks the registration schema and mandatory coverage without evaluating evidence. A valid registration prints `Registration valid` and exits 0.

## Verify evidence

```sh
popverify verify REGISTRATION EVIDENCE [--json] [--output PATH]
```

- `REGISTRATION`: path to a version-1 registration JSON.
- `EVIDENCE`: path to the observation JSON; referenced artifacts resolve below its parent directory.
- `--json`: print the complete machine-readable receipt instead of the readable assertion list.
- `--output PATH`: also save a JSON receipt. The parent directory must exist. Existing files and verification inputs cannot be overwritten.

```sh
popverify verify examples/synthetic/package/registration.json \
  examples/synthetic/package/evidence.json --json
```

## Exit codes

| Code | Meaning |
|---|---|
| 0 | PASS |
| 1 | FAIL |
| 2 | UNRESOLVED; argparse also uses 2 for command syntax errors |
| 3 | Invalid registration, inaccessible registration, invalid output destination or other handled invocation error |

Use JSON output to inspect scientific decisions; a CLI syntax error does not produce a receipt. `popverify --help` and `popverify verify --help` print the actual command options. There is no trainer, image-decoder or model-reconstruction command.

[See generated examples](examples.md).
