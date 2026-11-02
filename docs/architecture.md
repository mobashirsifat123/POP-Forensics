# Architecture

The package uses small modules instead of an extensible training framework:

| Module | Responsibility |
|---|---|
| registration.py | Strict JSON parsing, schema/coverage/tolerance validation |
| evidence.py | Confined artifact resolution, streaming SHA-256, numeric vector reads |
| checks.py | Semantic assertion implementations |
| verification.py | Full assertion evaluation, decision priority, evidence-bound receipts |
| metrics.py | O(n log n) tie-aware rank AUC; domain/type aggregation |
| cli.py | Human/JSON interface, exit codes and exclusive receipt writes |

No framework registry, tracker dependency, network service, automatic training instrumentation or model loader is present. Producers own feature generation, decoding, instrumentation and reconstruction. The public `verify(registration_path, evidence_path)` API composes the modules. Module separation follows actual responsibilities; no empty package hierarchy is included.

Version 1 JSON is the stable interface for this release. A future plugin system should only be introduced after distinct integrations demonstrate its need. Current checks support the documented image-forensics audit hazards, with an intentionally bounded BCE-oriented objective contract.

## Producer tools

`popverify.producers` adds independently invoked evidence collection: `population`, `sica`, `scoring`, `optimization`, `logs`, `provenance`, shared output helpers and a dedicated module CLI. Its outputs feed the original verification contract. Runtime remains standard-library by default; the optional image extra uses Pillow and the training example uses the caller's PyTorch environment. [Usage and boundaries](evidence_producers.md).
