# Release audit — reference implementation 0.1.0

Reviewed 2026-11-02 before the initial software push. Publication scope is newly written source/documentation and newly generated synthetic values only. No third-party implementation is relicensed.

| Area | Finding / action |
|---|---|
| New source and documentation | MIT license included; new reference implementation explicitly identified |
| Upstream license signals | Recorded in reference_review.md; no code, copied text, graphics or branding imported |
| Existing assembled research package | Overall licensing unresolved; package not published here |
| Manuscript and paper assets | Metadata only; PDFs/figures excluded |
| Dataset restrictions / raw predictions | Historical images, prediction exports, paths and census tables excluded |
| Model weights and training environments | Excluded; no GPU experiments or original research reruns |
| Missing historical artifacts | Original validator, matrix and catalog explicitly unavailable |
| Credentials / personal paths | Bounded indexed-file scan plus manual review; no credentials or private lab paths intentionally included |
| Personal information | Public-facing author names in citation metadata only; no private contact/account records |
| Size | Tiny synthetic JSON artifacts; no weights, binary data or large exports |
| Runtime dependencies | Standard library only; separate development/build tools |
| CI permissions | Read-only contents; no deployment credentials or publish job |
| Publication | Existing user-created public POP-Forensics repository used; SICA reproduction repository unchanged |

Public tree verification confirmed all 46 indexed file blobs match the published implementation commit `7dc917c274fe3c7002afdf00d9f40039b0bce6b4`. The bounded scan returned zero findings. Hosted CPU tests passed on all three declared Python versions. The SICA reproduction repository was accessed read-only.

## Security review

The Security Best Practices skill was consulted. Its reference catalog contains framework-specific Python web guidance but no applicable standard-library CLI guide. Review therefore covers this package's actual filesystem and JSON boundaries; it is not an external penetration test or formal security certification.

No critical/high findings were identified in this bounded review. Controls include relative artifact paths resolved below the evidence root (including symlinks), duplicate-key and nonstandard nonfinite JSON rejection, no pickle/model execution, no remote evidence fetches and exclusive receipt creation. Regression tests cover escaping paths, altered bytes, malformed records and output overwrites.

Known boundary SR-01 (informational): JSON manifests/vectors are memory-loaded; there are no hostile-input size quotas. Use bounded packages and OS isolation for untrusted inputs.

Known boundary SR-02 (informational): artifacts may change while verification runs. Keep the evidence directory immutable and retain externally anchored receipts; concurrent hostile filesystem mutation is outside this implementation's guarantees.

Known boundary SR-03 (scientific trust): producer summaries and booleans are not independently measured by POP. Truthfulness, completeness and preregistration require external process controls. The documentation makes this explicit.

The reproducible `python scripts/audit_release.py` scan checks indexed text files for selected token/private-key patterns, private absolute paths, binaries, symlinks and oversized files. A clean scan is a bounded check, not proof that all possible secrets or ownership issues have been detected. Inspect `git diff --cached` before each publication.
