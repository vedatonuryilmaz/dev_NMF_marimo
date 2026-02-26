# PROVENANCE_LOG

## Build Iteration 1
- Spec: `agent-state/SPEC_CONTRACT.json` version `0.1.0`
- Artifact: `nmf_marimo.py`
- Confidence: `Verified (static + targeted runtime checks)`
- Notes:
  - Added canonical `mo.state` selection store.
  - Added selection normalization to native Python ints.
  - Added bidirectional widget synchronization with equality guards.

## Build Iteration 2
- Spec: `agent-state/SPEC_CONTRACT.json` version `0.2.0`
- Artifact: `higlass_marimo.py`
- Confidence: `Verified (static + live smoke checks)`
- Notes:
  - Removed HiGlass anywidget rendering path.
  - Added direct HiGlass JS viewer embed via `mo.Html`.
  - Preserved zoom controls by regenerating viewconf domain from user inputs.

## Build Iteration 3
- Spec: `agent-state/SPEC_CONTRACT.json` version `0.2.0`
- Artifact: `higlass_marimo.py`
- Confidence: `Verified (static + browser automation checks)`
- Notes:
  - Introduced custom `HiGlassViewconfWidget(anywidget.AnyWidget)` with `_esm` + `_css`.
  - Added widget status telemetry (`status` trait) for runtime visibility.
  - Browser automation confirms canvas render and no anywidget model-key errors.
