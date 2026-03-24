# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo>=0.20.2",
#     "higlass-python>=1.4.0",
# ]
# ///
import marimo

__generated_with = "0.20.2"
app = marimo.App(width="full")


@app.cell
def _():
    """Bootstrap published notebook dependencies and assets."""
    import importlib as _importlib
    import importlib.util as _importlib_util
    import os as _os
    import shutil as _shutil
    import subprocess as _subprocess
    import sys as _sys
    import urllib.request as _req
    from pathlib import Path as _Path

    _default_base_url = (
        "https://raw.githubusercontent.com/vedatonuryilmaz/dev_NMF_marimo/mvp0313"
    )
    pub_base_url = _os.environ.get("NMFVIS_PUB_BASE_URL", _default_base_url).rstrip(
        "/"
    )
    _required_packages = {
        "higlass": "higlass-python>=1.4.0",
    }

    _missing_packages = [
        _spec
        for _module, _spec in _required_packages.items()
        if _importlib_util.find_spec(_module) is None
    ]
    if _missing_packages:
        _uv = _shutil.which("uv")
        if _uv is None:
            raise RuntimeError(
                "The HiGlass notebook requires `uv` to install runtime "
                f"dependencies: {_missing_packages}"
            )

        _install_attempts = [
            [_uv, "pip", "install", "--python", _sys.executable, *_missing_packages],
            [
                _uv,
                "pip",
                "install",
                "--python",
                _sys.executable,
                "--system",
                *_missing_packages,
            ],
        ]
        _last_error = None
        for _cmd in _install_attempts:
            _result = _subprocess.run(_cmd, capture_output=True, text=True)
            if _result.returncode == 0:
                break
            _last_error = RuntimeError(
                "Failed to install notebook runtime dependencies with `uv`: "
                f"{' '.join(_cmd)}\nSTDOUT:\n{_result.stdout}\nSTDERR:\n{_result.stderr}"
            )
        else:
            raise _last_error

        _importlib.invalidate_caches()

    _asset_files = ["conf/higlass_index_viewconf.json"]
    for _rel in _asset_files:
        _dest = _Path(_rel)
        if not _dest.exists():
            _dest.parent.mkdir(parents=True, exist_ok=True)
            _req.urlretrieve(f"{pub_base_url}/{_rel}", _dest.as_posix())

    bootstrap_ready = True
    viewconfig_path = "conf/higlass_index_viewconf.json"
    return bootstrap_ready, pub_base_url, viewconfig_path


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo, pub_base_url):
    mo.md(
        f"""
    # HiGlass index explorer

    This notebook is self-bootstrapping for MoLab: it installs `higlass-python`
    if needed and pulls `conf/higlass_index_viewconf.json` from `{pub_base_url}`
    when the file is not already present locally.
    """
    )
    return


@app.cell
def _(viewconfig_path):
    import json

    with open(viewconfig_path, "r", encoding="utf-8") as f:
        viewconfig = json.load(f)

    return (viewconfig,)


@app.cell
def _(viewconfig):
    import copy

    plugin_url = "https://unpkg.com/higlass-multivec@0.3.3/dist/higlass-multivec.js"
    plugin_types = {"horizontal-multivec", "horizontal-stacked-bar"}

    normalized_viewconfig = copy.deepcopy(viewconfig)

    def inject_plugin_urls(_tracks):
        for _track in _tracks:
            _type = _track.get("type")
            if _type in plugin_types and "plugin_url" not in _track:
                _track["plugin_url"] = plugin_url
            _contents = _track.get("contents")
            if isinstance(_contents, list):
                inject_plugin_urls(_contents)

    for _view in normalized_viewconfig.get("views", []):
        _tracks_by_position = _view.get("tracks", {})
        for _tracks in _tracks_by_position.values():
            if isinstance(_tracks, list):
                inject_plugin_urls(_tracks)

    return (normalized_viewconfig,)


@app.cell
def _(normalized_viewconfig):
    import higlass as hg

    viewconf = hg.Viewconf(**normalized_viewconfig)
    widget = viewconf.widget()

    return viewconf, widget


@app.cell(hide_code=True)
def _(widget):
    widget
    return


if __name__ == "__main__":
    app.run()
