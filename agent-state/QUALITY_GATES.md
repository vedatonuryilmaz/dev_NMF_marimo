# QUALITY_GATES

## gate.type-safety
- Invariant: All values written to `grandscatter.Scatter.selected_points` are native Python `int`.
- Evidence: Runtime assignment test with normalized list converted from `np.uint32`.

## gate.shared-selection
- Invariant: A single shared selection state drives heatmap filtering, table filtering, jscatter selection, and grandscatter selection.
- Evidence: `nmf_marimo.py` contains one `mo.state` selection source and bidirectional sync cells.

## gate.marimo-check
- Invariant: `marimo check nmf_marimo.py` has zero `critical` findings.
- Evidence: command output logged in `EVIDENCE_LOG.md`.

## gate.higlass-render-path
- Invariant: `higlass_marimo.py` does not call `higlass-python`'s nested widget path (`view.widget()` / `_tileset_client`) that caused model-key lookup failures.
- Evidence: source scan shows no `view.widget()` usage and no `_tileset_client` references.

## gate.live-smoke
- Invariant: both marimo apps start and serve HTTP 200 responses.
- Evidence: live sessions on `127.0.0.1:8811` and `127.0.0.1:8813` with successful `curl` health checks.
