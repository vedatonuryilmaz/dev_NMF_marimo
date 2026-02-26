import marimo

__generated_with = "0.19.11"
app = marimo.App()


@app.cell
def _():
    import pathlib
    import re

    import anywidget
    import higlass._widget as hg_widget_module
    import marimo as mo

    def patch_higlass_for_marimo() -> str:
        if getattr(hg_widget_module, "_marimo_patch_applied", False):
            return "already-patched"

        widget_js_path = pathlib.Path(hg_widget_module.__file__).parent / "widget.js"
        widget_js = widget_js_path.read_text()

        guarded_register_block = """await requireScripts(model.get("_plugin_urls"));
    const hasJupyterServer =
      JSON.stringify(model.get("_viewconf")).includes('"server":"jupyter"');
    if (hasJupyterServer && model.get("_tileset_client")) {
      await registerJupyterHiGlassDataFetcher(model);
    }"""

        patched_js, register_replacements = re.subn(
            r"await Promise\.all\(\[\s*"
            r'requireScripts\(model\.get\("_plugin_urls"\)\),\s*'
            r"registerJupyterHiGlassDataFetcher\(model\),\s*"
            r"\]\);",
            guarded_register_block,
            widget_js,
            count=1,
            flags=re.MULTILINE,
        )
        patched_js, css_helper_replacements = re.subn(
            r"export default \{",
            """
async function ensureHiGlassStyles(el) {
  const root = el.getRootNode();
  if (!(root instanceof ShadowRoot)) {
    return;
  }

  let sourceStyles = Array.from(document.head.querySelectorAll("style"));
  if (sourceStyles.length === 0) {
    await new Promise((resolve) => setTimeout(resolve, 50));
    sourceStyles = Array.from(document.head.querySelectorAll("style"));
  }

  sourceStyles.forEach((style, idx) => {
    const key = `higlass-shadow-${idx}-${style.textContent.length}`;
    if (root.querySelector(`style[data-higlass-shadow-copy="${key}"]`)) {
      return;
    }
    const clone = document.createElement("style");
    clone.setAttribute("data-higlass-shadow-copy", key);
    clone.textContent = style.textContent;
    root.appendChild(clone);
  });
}

export default {
""",
            patched_js,
            count=1,
            flags=re.MULTILINE,
        )
        patched_js, render_hook_replacements = re.subn(
            r"async render\(\{ model, el \}\) \{",
            (
                "async render({ model, el }) {\n"
                '    el.style.width = "100%";\n'
                '    el.style.height = "1120px";\n'
                '    el.style.minHeight = "1120px";\n'
                "    await ensureHiGlassStyles(el);"
            ),
            patched_js,
            count=1,
            flags=re.MULTILINE,
        )
        patched_js, viewer_replacements = re.subn(
            r"let api = await hglib\.viewer\(el, viewconf, options\);",
            "let api = await hglib.viewer(el, viewconf, options);\n    await ensureHiGlassStyles(el);",
            patched_js,
            count=1,
            flags=re.MULTILINE,
        )
        if (
            register_replacements != 1
            or css_helper_replacements != 1
            or render_hook_replacements != 1
            or viewer_replacements != 1
        ):
            raise RuntimeError("Unable to patch HiGlass widget.js for marimo")

        class MarimoHiGlassWidget(hg_widget_module.HiGlassWidget):
            _esm = patched_js

            def __init__(self, viewconf: dict, plugin_urls: list[str] | None, **viewer_options):
                import anywidget as _anywidget

                # Marimo cannot resolve nested IPY_MODEL references for _tileset_client.
                _anywidget.AnyWidget.__init__(
                    self,
                    _viewconf=viewconf,
                    _plugin_urls=plugin_urls,
                    _options=viewer_options,
                    _tileset_client=None,
                )

        hg_widget_module.HiGlassWidget = MarimoHiGlassWidget
        hg_widget_module._marimo_patch_applied = True
        return "applied"

    patch_higlass_for_marimo()

    return (mo,)


@app.cell
def _():
    import higlass as hg

    return (hg,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        "# `pip install higlass-python`\n\n"
        "## 796 ATAC-seq cancer samples\n\n"
        "Also view on [Resgen.io](https://resgen.io/abdenlab/tcga/full/Co53bAr9S4Czub18QCtQNw)!"
    )
    return


@app.cell
def _(hg, mo):
    from typing import ClassVar, Literal

    class HorizontalStackedBarPluginTrack(hg.PluginTrack):
        type: Literal["horizontal-stacked-bar"] = "horizontal-stacked-bar"
        plugin_url: ClassVar[str] = (
            "https://unpkg.com/higlass-multivec@0.3.3/dist/higlass-multivec.js"
        )

    server_url = "https://resgen.io/api/v1/"

    chromosome_labels = hg.remote(
        uid="ZpZ8c5JJRUS1J7ZkofcUrg",
        server=server_url,
    ).track(
        "chromosome-labels",
        uid="XTqEyYTGSPKXALEFFm4uug",
        options={
            "color": "#808080",
            "stroke": "#ffffff",
            "fontSize": 12,
            "fontIsLeftAligned": False,
            "showMousePosition": False,
            "mousePositionColor": "#000000",
        },
        width=2533,
        height=30,
    )

    horizontal_gene_annotations = hg.remote(
        uid="M9A9klpwTci5Vf4bHZ864g",
        server=server_url,
    ).track(
        "horizontal-gene-annotations",
        uid="L7GdwprJSsGz2kMR1ntLgA",
        options={
            "fontSize": 10,
            "labelColor": "black",
            "labelBackgroundColor": "#ffffff",
            "labelPosition": "hidden",
            "labelLeftMargin": 0,
            "labelRightMargin": 0,
            "labelTopMargin": 0,
            "labelBottomMargin": 0,
            "minHeight": 24,
            "plusStrandColor": "blue",
            "minusStrandColor": "red",
            "trackBorderWidth": 0,
            "trackBorderColor": "black",
            "showMousePosition": False,
            "mousePositionColor": "#000000",
            "geneAnnotationHeight": 16,
            "geneLabelPosition": "outside",
            "geneStrandSpacing": 4,
        },
        width=2533,
        height=90,
    )

    horizontal_stacked_bar = HorizontalStackedBarPluginTrack(
        server=server_url,
        tilesetUid="HMSJyvLCSgGmrDJctdIz3w",
        uid="fhp73d7gSzKoAjQ9UJLorQ",
        options={
            "labelPosition": "topLeft",
            "labelColor": "black",
            "labelTextOpacity": 0.4,
            "valueScaling": "exponential",
            "trackBorderWidth": 0,
            "trackBorderColor": "black",
            "backgroundColor": "white",
            "barBorder": True,
            "sortLargestOnTop": True,
            "selectRows": None,
            "name": "Epilogos (hg38)",
            "colorScale": [
                "#FF0000",
                "#FF4500",
                "#32CD32",
                "#008000",
                "#006400",
                "#C2E105",
                "#FFFF00",
                "#66CDAA",
                "#8A91D0",
                "#CD5C5C",
                "#E9967A",
                "#BDB76B",
                "#808080",
                "#C0C0C0",
                "#FFFFFF",
            ],
        },
        width=20,
        height=20,
    )

    horizontal_multivec = hg.remote(
        uid="E0AXSsX2Qqy4B4b68SoqgQ",
        server=server_url,
    ).track(
        "horizontal-multivec",
        uid="W9HY2pJqSAWMpWbza0nPag",
        options={
            "labelPosition": "topLeft",
            "labelLeftMargin": 0,
            "labelRightMargin": 0,
            "labelTopMargin": 0,
            "labelBottomMargin": 0,
            "labelShowResolution": True,
            "labelShowAssembly": True,
            "labelColor": "black",
            "labelTextOpacity": 0.4,
            "minHeight": 100,
            "valueScaling": "linear",
            "trackBorderWidth": 0,
            "trackBorderColor": "black",
            "heatmapValueScaling": "linear",
            "selectRows": None,
            "selectRowsAggregationMode": "mean",
            "selectRowsAggregationWithRelativeHeight": True,
            "colorbarBackgroundColor": "#ffffff",
            "colorbarPosition": "topRight",
            "zeroValueColor": None,
            "name": "tcga.by_component.1000.mv5",
            "scaleStartPercent": "0.00000",
            "scaleEndPercent": "0.14444",
            "colorRange": ["rgba(255,255,255,1)", "rgba(0,0,0,1)"],
        },
        width=2533,
        height=968,
    )

    view = hg.view(
        chromosome_labels,
        horizontal_gene_annotations,
        (horizontal_stacked_bar, "top"),
        horizontal_multivec,
        uid="IpFAULSQShmBHSlLf6IGOg",
        width=12,
        height=12,
        initialXDomain=[1440763813.3127189, 1442990265.7390883],
        initialYDomain=[595697678.0762143, 595804705.51733],
    )

    viewconf = view.viewconf(
        editable=True,
        trackSourceServers=["/api/v1", "http://higlass.io/api/v1"],
        exportViewUrl="/api/v1/viewconfs",
    )
    widget = viewconf.widget(editable=True, viewEditable=True, tracksEditable=True)
    widget.layout.width = "100%"
    widget.layout.height = "1120px"
    wrapped_widget = mo.ui.anywidget(widget)

    wrapped_widget
    return view, viewconf, widget, wrapped_widget


@app.cell
def _(view, widget):
    import bioframe
    from higlass._scale import Scale
    hg38 = bioframe.fetch_chromsizes('hg38')
    scale = Scale(hg38)

    widget.zoom_to(
        view.uid,
        int(scale(("chr8", 127_500_000))),
        int(scale(("chr8", 128_500_000)))
    )
    return
if __name__ == "__main__":
    app.run()
