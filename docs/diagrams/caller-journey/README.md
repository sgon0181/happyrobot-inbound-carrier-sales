# Follow the caller: three systems views

Source snapshot: main at `2678845`. These diagrams explain one illustrative successful call, not a new live execution. Read the [blueprint](pages/01-caller-blueprint.pdf) first, then [sequence](pages/02-call-sequence.pdf), then [nested systems map](pages/03-nested-systems-map.pdf).

## What is in this folder

| Path | What it is |
|---|---|
| [caller-journey-three-views.pdf](caller-journey-three-views.pdf) | Start here: all three diagrams, one A3 page each |
| [index.html](index.html) | Interactive viewer for the same three pages |
| [pages/](pages/) | Each diagram on its own, as PDF and SVG |
| [build/](build/) | Scripts and data that regenerate everything above |

- [Local viewer](index.html): switch pages, zoom, and select C1-C7 to inspect speech, rules, data and source-file links. Open this file in a browser from the checkout.
- [Combined PDF](caller-journey-three-views.pdf): three A3 landscape pages, one diagram per page. Vector text stays sharp when enlarged.
- SVG originals: [blueprint](pages/01-caller-blueprint.svg), [sequence](pages/02-call-sequence.svg), [map](pages/03-nested-systems-map.svg).

## Read the symbols consistently

| Mark | Meaning |
|---|---|
| C1-C7, dark rounded badge | A moment in the caller's journey |
| B1-B5, gold hexagon | Build slice, not a call step or a state |
| Folded-corner file mark | Source file or code group |
| Blue rounded data panel | Temporary input, object, transformation or reply |
| Blue cylinder | Persisted Twin row state |
| Purple | HappyRobot-managed conversation |
| Teal | Repository service/App code |
| Amber | Outside integrations |
| Solid boundary | Implemented code or component |
| Dashed boundary | Mocked or conditional edge; sequence dashed arrows separately mean replies/conditional callback |

B1 is foundations; B2 verification and storage; B3 selling, reservation and close; B4 operations and booking submission; B5 QA and delivery. Badges identify feature ownership. Later R1-R6 remediation work is not another set of build slices.

## Deliberate boundaries

The caller's endpoint is a Twin reservation plus spoken mocked handoff. There is no actual transfer or voice `LOAD_BOOK` tool. The separate rep path can act while the call is still active; it is not forced to wait for hangup. Sends off/unknown disables Confirm. A reference-bearing PENDING acknowledgement is not BOOKED.

HappyRobot owns managed speech/model execution. The repo does not implement an STT/TTS engine or prove which speech settings can be changed. Name confirmation is prompt behavior, while authority/code/rate/reservation checks are service rules. Caller-spoken digits pass through HappyRobot records and the verification request; expected-code output is withheld.

State and its event share one version-checked row write. Reservation still spans call claim, booking row and call settlement, with recovery rather than a cross-table transaction. The end callback is conditional on execution and persistence and cannot recreate missing closing notes.

Repo rollout notes record Version 4 live since 2026-11-04 and an older App build. Repo QA reports the fixed prompt at 44/44 mocked checkpoints, after the earlier 58/66; human voice acceptance remains open. See [QA results](../../qa-results.md). A successful-path diagram is not a claim that every conversation follows it.

## Rebuild

Use an isolated documentation Python environment with `reportlab` and `pypdf`, then run:

```text
python docs/diagrams/caller-journey/build/build.py
```

Everything needed to rebuild is in `build/`. `build.py` holds the literal seven-step trace and three page layouts. `rendering.py` holds shared drawing primitives and legend. `viewer-template.html` is the local viewer shell. The builder writes the SVG/PDF pairs to `pages/`, the combined PDF and `index.html` to this folder, and `trace.json` to `build/`. It does not import the service, load configuration or make network requests.

Validation: source trace reviewed against the code, per-page renders checked, SVG XML parsed, three PDF pages verified, layout overflow checks clean, relative source links checked. Production Python remains unchanged.
