# Test report — 0.1.0

Local execution: 2026-11-02, macOS arm64, CPython 3.14.3; no GPU or historical model execution. Runtime dependencies: none. Development tools: Ruff 0.17.3, build 1.6.1, packaging 26.3 and pyproject-hooks 1.3.3. These are observed local versions, not a locked dependency set.

| Check | Status | Details |
|---|---|---|
| unittest full suite | PASS | 12 test methods, including 16 conformance subcases |
| Conformance | PASS | New clean case + 15 faults/gaps: 1 PASS, 10 FAIL, 5 UNRESOLVED |
| Decision precedence | PASS | Contradiction remains FAIL alongside missing evidence |
| Registration/evidence boundaries | PASS | Empty/incomplete contracts, malformed JSON, duplicate keys, missing records |
| Artifact/path/reconstruction | PASS | Digest mismatch, confined paths/symlinks, missing files, numeric tolerance and length |
| Optimization | PASS | Invalid probability target, stalled parameters, skipped updates and dtype mismatch |
| Metrics | PASS | Ties, missing classes/types, domain/type weighting and sign reversal |
| CLI | PASS | Readable/JSON receipts, validation and 0/1/2/3 exit behavior |
| Ruff lint / format | PASS | Full Python tree |
| Distribution build | PASS | Source archive and wheel |
| Committed synthetic example | PASS | Both arms, all three gates |
| Clean-wheel install | PASS | Separate environment; import and committed-example verification from outside checkout |

The clean-wheel full suite passed from outside the checkout. [GitHub Actions run 41427565932](https://github.com/mobashirsifat123/POP-Forensics/actions/runs/41427565932) passed on Linux for Python 3.10, 3.12 and 3.14 at implementation commit `7dc917c274fe3c7002afdf00d9f40039b0bce6b4`. Current remote CI is available in the repository Actions tab; its results, rather than declared matrix targets, determine hosted compatibility. The workflow targets Python 3.10, 3.12 and 3.14 on Linux. Source tests run before build; wheel smoke tests then verify generated and committed packages.

No failing or skipped local tests were retained in this report. Initial environment setup briefly ran tests before installation finished; rerunning after installation succeeded. No real-world detector effectiveness, historical-scope reproduction, blinded audit, scalability or comparative product test is claimed.

Reproduce with the commands in the README. Tests use unittest and temporary directories; synthetic registration and evidence are independently varied to exercise contradictions and gaps. Cases are dependent author-designed fixtures, so their agreement is not an independent sensitivity estimate.
