# Design references and attribution review

Reviewed 2026-11-02 via GitHub repository metadata, file trees and README/documentation; selected reproduction scripts were also read. Commit snapshots identify what was inspected, not compatibility guarantees.

| Reference | Inspected commit | Relevant engineering practices | License signals and release decision |
|---|---|---|---|
| [ForensicHub](https://github.com/scu-zjz/ForensicHub) | `92653068ccb22744a5e58df6e47cc813e0441202` | Component organization for data/models/transforms/evaluators; configuration-driven train/test workflows; install guide and citations | GitHub identifies CC-BY-4.0; individual model assets may differ. No code/assets copied. |
| [IMDL-BenCo](https://github.com/scu-zjz/IMDLBenCo) | `1026ba9b4451c22675d40c4e3f7c5ec9f37bdf63` | Packaged CLI, reusable evaluation modules, separate documentation, tests/publishing workflows, versioned fixes | GitHub identifies CC-BY-4.0; model-zoo subcomponents have separate licenses. No code/assets copied. |
| [SICA/OpenMMSec](https://github.com/venus-guangjian/SICA_OpenMMSec) | `def6e344ca3f18a2313adb6be3bd1f8fb8d27e7d` | Clear model/data identity, inference/checkpoint entry points, external training guidance, citation | GitHub has no detected repository license; README identifies CC-BY-NC-4.0 and restricted dataset access. Dataset terms are not inferred to license every code file. Link only. |
| [SICA reproduction](https://github.com/mobashirsifat123/Strarting_case_for_ForensicHub_by_SICA) | `ca85c0c7a1bfa5a21a64cf0924012677fca4e43f` | Separate training configurations, score export, metric aggregation, checkpoint verification and reproduction protocols | No detected repository license. No source, data or prose copied; repository unchanged. |

Adopted: concise project identity, executable installation and example commands, real module boundaries, separate producer/verification workflows, schema documentation, CI, citations and explicit limitations. Avoided: model registries, large training dependencies, copied branding/README prose, detector leaderboards and unsupported benchmark claims.

Inspection of release/maintenance signals is not a claim to have installed or tested those external projects. None is required to run POP's included example. Their authors retain ownership of their work. ForensicHub, IMDL-BenCo and SICA/OpenMMSec remain independent projects with their own access and licensing terms.
