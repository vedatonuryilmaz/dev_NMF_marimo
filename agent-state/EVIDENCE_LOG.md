# EVIDENCE_LOG

## 2026-02-25T17:19:33Z
- Checked repository state and located failure path in `nmf_marimo.py` at assignment to `gs_widget.selected_points`.
- Confirmed runtime trait contract: `grandscatter.Scatter.selected_points` rejects `np.uint32` values.

## 2026-02-25T17:19:33Z
- Runtime validation:
  - Command: `UV_CACHE_DIR=$PWD/.uv-cache uv run python - <<'PY' ...`
  - Result: assigning `[int(v) for v in np.array([79,170], dtype=np.uint32).tolist()]` to `selected_points` succeeds.
  - Output: `assigned selected_points type: <class 'list'> value: [79, 170]`

## 2026-02-25T17:19:33Z
- Static validation:
  - Command: `UV_CACHE_DIR=$PWD/.uv-cache uv run marimo check nmf_marimo.py`
  - Result: exit code 0, no critical findings.
  - Note: one non-blocking markdown-indentation warning remains.

## 2026-02-25T17:19:33Z
- Syntax validation:
  - Command: `UV_CACHE_DIR=$PWD/.uv-cache uv run python -m py_compile nmf_marimo.py`
  - Result: exit code 0.
- Artifact integrity:
  - `nmf_marimo.py` sha256: `13f4d0176e5d1ba4a6b06b8a1bd710bc38799217b0cce5d264828e0fe06d357a`

## 2026-02-25T17:38:46Z
- HiGlass marimo rendering fix implemented in `higlass_marimo.py`:
  - switched display path from `mo.ui.anywidget(hg_widget)` to `mo.as_html(hg_widget)`
  - normalized remote server URLs to `https://resgen.io/api/v1/`
  - removed hard-coded initial domains from `hg.view(...)` initialization
- Validation:
  - Command: `UV_CACHE_DIR=$PWD/.uv-cache uv run marimo check higlass_marimo.py`
  - Result: exit code 0, no critical findings (one non-blocking markdown-indentation warning).
  - Command: `UV_CACHE_DIR=$PWD/.uv-cache uv run python -m py_compile higlass_marimo.py`
  - Result: exit code 0.
  - Command: `UV_CACHE_DIR=$PWD/.uv-cache uv run higlass_marimo.py`
  - Result: exit code 0.

## 2026-02-25T17:45:14Z
- Background smoke run (live marimo servers):
  - `higlass_marimo.py` launched on `http://127.0.0.1:8811` (PID 34495)
  - `nmf_marimo.py` launched on `http://127.0.0.1:8813` (PID 34615)
- Health checks:
  - `curl http://127.0.0.1:8811/` -> HTTP 200
  - `curl http://127.0.0.1:8813/` -> HTTP 200
  - `lsof` confirms both ports are LISTENING.
- Runtime logs:
  - No traceback/error output observed from active server sessions during polling.
- Static checks:
  - `marimo check higlass_marimo.py` -> exit 0 (one markdown-indentation warning only)
  - `marimo check nmf_marimo.py` -> exit 0 (one markdown-indentation warning only)

## 2026-02-25T18:05:54Z
- User-reported runtime browser error:
  - `Error rendering anywidget: Model not found for key: ...` while loading `higlass_marimo.py`.
- Remediation implemented:
  - Replaced anywidget-based HiGlass display with direct `mo.Html` embed and `hglib.viewer(...)`.
  - Removed `view.widget()`/`mo.ui.anywidget(...)` dependency from `higlass_marimo.py`.
  - Added deterministic initial X-domain and retained zoom controls by rebuilding viewconf from inputs.
- Verification:
  - Command: `rg -n "anywidget|view\\.widget\\(|hg_widget" higlass_marimo.py` -> no matches.
  - Command: `UV_CACHE_DIR=$PWD/.uv-cache uv run marimo check higlass_marimo.py` -> exit 0, no critical findings (one markdown-indentation warning).
  - Command: `UV_CACHE_DIR=$PWD/.uv-cache uv run python -m py_compile higlass_marimo.py` -> exit 0.
  - Live sessions:
    - `higlass_marimo.py` on `127.0.0.1:8811` (PID 35657), `curl` -> 200.
    - `nmf_marimo.py` on `127.0.0.1:8813` (PID 35687), `curl` -> 200.

## 2026-02-25T18:09:14Z
- Gate packet verification:
  - `jq` validation passed for `HANDOFF.json`, registry, and both new gate manifests.
  - `gate.higlass-render-path` command output was empty (no forbidden anywidget patterns in `higlass_marimo.py`).
  - `gate.live-smoke` command output:
  - `higlass 200`
  - `nmf 200`

## 2026-02-25T18:20:35Z
- HiGlass renderer revised again:
  - moved from `mo.Html` script embed to custom `HiGlassViewconfWidget(anywidget.AnyWidget)`.
  - custom widget consumes only `viewconf` and `height` traits (no nested `_tileset_client` model).
  - added `status` trait for runtime telemetry (`loading`, `hglib-loaded`, `viewer-ready`, or failure details).
- Validation:
  - Command: `UV_CACHE_DIR=$PWD/.uv-cache uv run marimo check higlass_marimo.py`
  - Result: exit code 0, one non-critical markdown-indentation warning.
  - Command: `UV_CACHE_DIR=$PWD/.uv-cache uv run python -m py_compile higlass_marimo.py`
  - Result: exit code 0.
  - Command: `rg -n "view\\.widget\\(|_tileset_client" higlass_marimo.py`
  - Result: no matches.
  - Browser automation (`playwright`):
    - `canvas_count=1`
    - `anywidget_err_count=0`
    - `failed_count=0`
    - screenshot captured at `.runlogs/higlass_playwright_latest.png`.
  - Live health checks:
    - `higlass 200` on `127.0.0.1:8811`
    - `nmf 200` on `127.0.0.1:8813`

## 2026-02-25T18:22:24Z
- Post-patch validation after adding widget `_css` and status line simplification:
  - Command: `UV_CACHE_DIR=$PWD/.uv-cache uv run marimo check higlass_marimo.py`
  - Result: exit code 0, one non-critical markdown-indentation warning.
  - Command: `UV_CACHE_DIR=$PWD/.uv-cache uv run python -m py_compile higlass_marimo.py`
  - Result: exit code 0.
  - Command: `rg -n "view\\.widget\\(|_tileset_client" higlass_marimo.py`
  - Result: no matches.
  - Browser automation (`playwright`):
    - `canvas_count=1`
    - `anywidget_err_count=0`
    - screenshot captured at `.runlogs/higlass_playwright_latest.png`.
  - Live health checks:
    - `higlass 200` on `127.0.0.1:8811` (PID 42745)
    - `nmf 200` on `127.0.0.1:8813` (PID 40989)
- Artifact integrity:
  - `higlass_marimo.py` sha256: `228b4cef76a53b3b4ac0e9d874b37caa4091c60114f469c3e308ab3fcc3d34a4`

## 2026-02-25T19:01:58Z
- Loop-break checkpoint for native HiGlass marimo path (`higlass_marimo.py`).
- Verified with browser automation (WebGL-enabled headless):
  - `wrapped_hg_widget.value` reports `viewconf tracks: views=1 top=3`.
  - `location` updates to domain coordinates in some runs.
  - `Model not found for key ...` error no longer observed in the WebGL-enabled probe after `_tileset_client` compatibility patch.
- Persistent blocker evidence:
  - `resgen.io` request count remains `0` under Marimo-mount probes, while same viewconf in standalone plain-HTML HiGlass test issues `5` requests.
  - HiGlass canvas and DOM nodes exist (`canvas 1276x1120`, `tiled-plot-div` present), but visible track rendering remains blank in Marimo app screenshots.
- Differential test result:
  - Standalone HTML (`hglib.viewer` outside Marimo): `RESGEN_REQ_COUNT 5` with same viewconf.
  - Marimo anywidget mount: `RESGEN_REQ_COUNT 0`.
- Interpretation: unresolved runtime integration mismatch remains between Marimo anywidget mount and HiGlass viewer request/render lifecycle.

## 2026-02-25T19:01:58Z (continued)
- HTTP header probe on Marimo app root:
  - `curl -sv http://127.0.0.1:8811/`
  - Response: `HTTP/1.1 200 OK`, no CSP header present in response.
- Additional native patching applied in `higlass_marimo.py` after loop-break checkpoint:
  - post-viewer layout width forcing for `.react-grid-item` and `.tiled-plot-div`
  - post-layout `zoomTo` refresh trigger for first view initial X-domain
- Static validation: `python -m py_compile higlass_marimo.py` exit code 0.
- Runtime re-verification after this last patch was intentionally deferred to avoid unconstrained looping (user directive).

## 2026-02-25T19:19:43Z
- Replaced `higlass_marimo.py` runtime monkey-patching flow with a local custom widget implementation:
  - `higlass_marimo_widget.js` created from upstream `src/higlass/widget.js` behavior (from `rep_higlasspython.cxml`) with marimo-safe lifecycle and status telemetry.
  - `higlass_marimo_widget.css` added with local host/container sizing and HiGlass CSS import.
  - `higlass_marimo.py` now uses `MarimoHiGlassWidget(anywidget.AnyWidget)` and no longer rewrites `higlass._widget` at runtime.
  - Track composition restored to include plugin-backed `horizontal-stacked-bar` row as in original notebook source.
- Validation:
  - Command: `UV_CACHE_DIR=$PWD/.uv-cache uv run marimo check higlass_marimo.py`
  - Result: exit code 0; one non-critical `markdown-indentation` warning.
  - Command: `UV_CACHE_DIR=$PWD/.uv-cache uv run python -m py_compile higlass_marimo.py`
  - Result: exit code 0.
  - Command: `UV_CACHE_DIR=$PWD/.uv-cache uv run higlass_marimo.py`
  - Result: exit code 0 (only matplotlib writable-cache warning).
  - Command: `MPLCONFIGDIR=$PWD/.matplotlib_cache UV_CACHE_DIR=$PWD/.uv-cache uv run marimo run higlass_marimo.py --headless --port 8811`
  - Result: blocked by sandbox bind policy (`[Errno 1] operation not permitted` on `127.0.0.1:8811`), so live browser verification was not executed in this run.

## 2026-02-25T20:16:01Z
- Escalated runtime server check completed:
  - Command: `MPLCONFIGDIR=$PWD/.matplotlib_cache UV_CACHE_DIR=$PWD/.uv-cache uv run marimo run higlass_marimo.py --headless --port 8811`
  - Result: server started successfully on `http://localhost:8811`.
  - Command: `curl -sS -D - http://127.0.0.1:8811/`
  - Result: `HTTP/1.1 200 OK` with marimo app HTML payload.
- Browser-automation limitation:
  - Command: `UV_CACHE_DIR=$PWD/.uv-cache uv run --with playwright python -c "import playwright; print(playwright.__version__)"`
  - Result: failed to resolve `https://pypi.org/simple/playwright/` (DNS/network restricted), so automated visual/network tile assertions were not run in this environment.
- Front-end syntax validation:
  - Command: `node --check higlass_marimo_widget.js`
  - Result: exit code 0.

## 2026-02-25T21:39:23Z
- HiGlass invalid viewconf root cause reproduced in `higlassmarimo2.py`:
  - `horizontal-stacked-bar` was created with `plugin_url` in track JSON.
  - Browser validation error matched user report: additional properties on `.views[0].tracks.top[2]`.
- Remediation implemented:
  - Replaced direct `.track(..., plugin_url=...)` path with a typed `hg.PluginTrack` subclass for `horizontal-stacked-bar`.
  - This keeps plugin registration in widget `_plugin_urls` and removes schema-invalid `plugin_url` from the track payload.
  - Aligned IDs/layout/domains with target config:
    - view uid `IpFAULSQShmBHSlLf6IGOg`
    - track uids `XTqEyYTGSPKXALEFFm4uug`, `L7GdwprJSsGz2kMR1ntLgA`, `fhp73d7gSzKoAjQ9UJLorQ`, `W9HY2pJqSAWMpWbza0nPag`
    - multivec tileset `E0AXSsX2Qqy4B4b68SoqgQ`
    - layout `w=12`, `h=12`, `x=0`, `y=0`
    - top-level `trackSourceServers` + `exportViewUrl`.
- Validation:
  - Command: `UV_CACHE_DIR=$PWD/.uv-cache uv run marimo check higlassmarimo2.py`
  - Result: exit code 0; one non-critical `markdown-indentation` warning.
  - Command: `UV_CACHE_DIR=$PWD/.uv-cache uv run python -m py_compile higlassmarimo2.py`
  - Result: exit code 0.
  - Command: `MPLCONFIGDIR=$PWD/.matplotlib_cache UV_CACHE_DIR=$PWD/.uv-cache uv run marimo run higlassmarimo2.py --headless --port 8815`
  - Result: app served successfully, `curl http://127.0.0.1:8815/` -> `HTTP 200`.
  - Command: `UV_CACHE_DIR=$PWD/.uv-cache uv run python - <<'PY' ...` (viewconf inspection)
  - Result: `actual_has_plugin_url_on_track2: False`; `actual_plugin_urls_for_widget` includes `https://unpkg.com/higlass-multivec@0.3.3/dist/higlass-multivec.js`.
- Artifact integrity:
  - `higlassmarimo2.py` sha256: `26a4f841f2b65c5f9a6c5faec8299ce7be8696376e6546bd8943cb892dd86d3f`
