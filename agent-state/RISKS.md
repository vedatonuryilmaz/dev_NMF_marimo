# RISKS

## R1: Index-order divergence across data sources
- Probability: Medium
- Impact: High
- Description: If UMAP rows, heatmap rows, and grandscatter rows diverge in ordering, shared index-based selection may highlight/filter mismatched samples.
- Mitigation: Validate and enforce explicit sample-id alignment in a follow-up change.

## R2: Reactive feedback churn
- Probability: Low
- Impact: Medium
- Description: Bidirectional widget sync can oscillate if equality guards are removed or bypassed.
- Mitigation: Keep normalization + equality checks before every setter write.

## R3: External script dependency for HiGlass viewer
- Probability: Medium
- Impact: Medium
- Description: `higlass_marimo.py` now imports HiGlass frontend from `esm.sh`; viewer render depends on external CDN/network availability.
- Mitigation: Vendor a pinned local JS asset in follow-up if offline or deterministic builds are required.

## R4: Local widget drift from upstream HiGlass frontend
- Probability: Medium
- Impact: Medium
- Description: `higlass_marimo_widget.js` is now a local fork of upstream `src/higlass/widget.js`. Future upstream behavior changes may not automatically propagate, creating divergence over time.
- Mitigation: Diff local widget code against upstream on dependency upgrades and keep a browser smoke gate asserting non-zero tile requests.

## R5: Hidden environment mismatch (WebGL / runtime policy)
- Probability: Medium
- Impact: High
- Description: Headless probes required explicit WebGL flags; non-WebGL browser contexts fail hard. There may also be runtime policy differences between plain HTML and Marimo mount that block downstream tile fetch/render behavior.
- Mitigation: Add one headed/manual smoke check in user browser plus one automated gate that validates HiGlass track draw heuristics, not only canvas existence.

## R6: Jupyter-backed tracks unsupported in custom marimo widget path
- Probability: Low
- Impact: Medium
- Description: The custom marimo widget path is designed for remote/server-backed tracks; Jupyter-backed (`server: "jupyter"`) track fetchers are currently marked unsupported.
- Mitigation: Implement an explicit marimo-compatible tileset-client bridge if/when local in-memory HiGlass data sources are required.

## R7: Cross-version viewconf mismatch for plugin track metadata
- Probability: High
- Impact: High
- Description: The reference repo viewconf includes `plugin_url` directly on the `horizontal-stacked-bar` track, but the current HiGlass schema in this environment rejects that field as invalid.
- Mitigation: Keep a conversion rule in code: store plugin URL via `hg.PluginTrack`/widget `_plugin_urls`, and keep the serialized track payload schema-valid.
