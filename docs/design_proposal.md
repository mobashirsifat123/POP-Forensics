# Visual redesign proposal

Status: implemented on `visual-documentation-refresh` for review. Stable version v0.1.1, main and all release tags remain unchanged.

## Direction

An evidence ledger: deep navy ink, paper backgrounds, fine rules and a three-path POP monogram. A restrained serif display face gives the documentation an academic editorial character; system sans-serif body text and monospace receipts prioritize reading. All graphics are original vector artwork.

Tagline: **Make the evidence inspectable.**

| Token | Value | Role |
|---|---|---|
| Ink | `#112C46` | Headings, identity, hero background |
| Blue | `#245CBE` | P1, links and primary actions |
| Teal | `#087F80` | O and secondary accents |
| Slate | `#536582` | P2 and secondary labels |
| Paper | `#F7F8F5` | Homepage background |
| Line | `#DCE3E8` | Rules, connectors and boundaries |

Status colors are reserved for evidence outcomes, paired with text labels and symbols. Gate colors identify evidence dimensions; they are not verdicts. Diagrams use consistent strokes, hierarchy and readable labels.

## Content plan

README: hero → research purpose → three gates → decision precedence → workflow and architecture → executable quick start → generated receipt → reference links and scientific limits.

Documentation: an editorial introduction with a three-path visual anchor; persistent navigation and search; task-oriented installation/example pages; dedicated gate guides, schema, CLI and API references. Existing methodology, evidence schema and limitations remain their canonical Markdown sources rather than copied content.

## Interaction plan

Search is the primary discovery interaction. Persistent navigation and active section markers preserve orientation. Copy controls make commands usable; outcome tabs let readers compare generated evidence conditions. Hover/focus transitions clarify links. No decorative animation, parallax or entrance effects are required.

## Reference lessons

ForensicHub provides a concise project identity and separates framework overview from configuration-led guides. IMDL-BenCo separates installation from task-specific quick-start workflows and makes library/CLI usage visible. SICA/OpenMMSec separates the research narrative, dataset access and inference resources. POP adopts the navigation clarity and explicit setup paths, while using its own evidence-led identity. No upstream text, source, branding or assets are copied.

References: [ForensicHub](https://github.com/scu-zjz/ForensicHub), [documentation](https://scu-zjz.github.io/ForensicHub-doc/); [IMDL-BenCo](https://github.com/scu-zjz/IMDLBenCo), [installation guide](https://scu-zjz.github.io/IMDLBenCo-doc/guide/quickstart/install.html); [SICA/OpenMMSec](https://github.com/venus-guangjian/SICA_OpenMMSec).

## Publication boundary

Build and preview the website on this branch. CI builds a downloadable site artifact; a separate Pages deployment job is permitted only on main after review/merge. No new release, tag rewrite or automatic merge is part of this redesign. Social-preview assets are supplied; publishing repository branding is deferred to review if account access is unavailable.
