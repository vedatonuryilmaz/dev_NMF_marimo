import marimo

__generated_with = "0.19.11"
app = marimo.App(width="full")


@app.cell
def _():
    import json
    import pathlib

    import anywidget
    import bioframe
    import higlass as hg
    import marimo as mo
    import traitlets as t
    from higlass._scale import Scale

    class MarimoHiGlassWidget(anywidget.AnyWidget):
        _esm = pathlib.Path(__file__).with_name("higlass_marimo_widget.js")
        _css = pathlib.Path(__file__).with_name("higlass_marimo_widget.css")

        _viewconf = t.Dict(allow_none=False).tag(sync=True)
        _options = t.Dict(default_value={}).tag(sync=True)
        _plugin_urls = t.List(default_value=[]).tag(sync=True)
        location = t.List(t.Any(), default_value=[]).tag(sync=True)
        status = t.Unicode(default_value="init").tag(sync=True)
        height = t.Int(default_value=1120).tag(sync=True)

        def __init__(
            self,
            viewconf: dict,
            plugin_urls: list[str] | None = None,
            height: int = 1120,
            **viewer_options,
        ):
            super().__init__(
                _viewconf=viewconf,
                _plugin_urls=plugin_urls or [],
                _options=viewer_options,
                height=height,
            )

        def reload(self, *items):
            msg = json.dumps(["reload", items])
            self.send(msg)

        def zoom_to(
            self,
            view_id: str,
            start1: int,
            end1: int,
            start2: int | None = None,
            end2: int | None = None,
            animate_time: int = 500,
        ):
            msg = json.dumps(["zoomTo", view_id, start1, end1, start2, end2, animate_time])
            self.send(msg)

    return MarimoHiGlassWidget, Scale, bioframe, hg, mo


@app.cell
def _(mo):
    mo.md(
        "# HiGlass: 796 ATAC-seq cancer samples\n\n"
        "Also view on [Resgen.io](https://resgen.io/abdenlab/tcga/full/Co53bAr9S4Czub18QCtQNw)!"
    )
    return


@app.cell
def _(MarimoHiGlassWidget, hg):
    server_url = "https://resgen.io/api/v1"

    chromosome_labels = hg.remote(
        uid="ZpZ8c5JJRUS1J7ZkofcUrg",
        server=server_url,
    ).track(
        "chromosome-labels",
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

    horizontal_stacked_bar = hg.remote(
        uid="HMSJyvLCSgGmrDJctdIz3w",
        server=server_url,
    ).track(
        "horizontal-stacked-bar",
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
        plugin_url="https://unpkg.com/higlass-multivec@0.3.3/dist/higlass-multivec.js",
    )

    horizontal_multivec = hg.remote(
        uid="Ch8tF6b1TjuCobJERHmtjQ",
        server=server_url,
    ).track(
        "horizontal-multivec",
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
        initialXDomain=[1440763813.3127189, 1442990265.7390883],
        initialYDomain=[595697678.0762143, 595804705.51733],
    )

    reference_widget = view.widget()
    higlass_widget = MarimoHiGlassWidget(
        viewconf=reference_widget._viewconf,
        plugin_urls=reference_widget._plugin_urls,
        height=1120,
        **(reference_widget._options or {}),
    )
    return higlass_widget, view


@app.cell
def _(higlass_widget, mo):
    wrapped_hg_widget = mo.ui.anywidget(higlass_widget)
    wrapped_hg = wrapped_hg_widget
    return wrapped_hg, wrapped_hg_widget


@app.cell
def _(mo):
    chromosome = mo.ui.text(value="chr8", label="Chromosome")
    start_bp = mo.ui.number(value=127_500_000, label="Start")
    end_bp = mo.ui.number(value=128_500_000, label="End")
    zoom_btn = mo.ui.run_button(label="Zoom to region")
    return chromosome, end_bp, start_bp, zoom_btn


@app.cell
def _(
    Scale,
    bioframe,
    chromosome,
    end_bp,
    higlass_widget,
    start_bp,
    view,
    zoom_btn,
):
    if zoom_btn.value:
        hg38 = bioframe.fetch_chromsizes("hg38")
        scale = Scale(hg38)
        higlass_widget.zoom_to(
            view.uid,
            int(scale((chromosome.value, int(start_bp.value)))),
            int(scale((chromosome.value, int(end_bp.value)))),
        )
    return


@app.cell
def _(mo, wrapped_hg_widget):
    widget_value = wrapped_hg_widget.value
    location = widget_value.get("location")
    status = widget_value.get("status", "unknown")
    viewconf_value = widget_value.get("_viewconf", {})
    views = viewconf_value.get("views", [])
    top_tracks = []
    if views:
        top_tracks = views[0].get("tracks", {}).get("top", [])
    location_text = "unknown" if location is None else str(location)

    status_text = mo.md(
        f"**HiGlass status:** `{status}`  \n"
        f"**Location state:** `{location_text}`  \n"
        f"**Viewconf tracks:** `views={len(views)} top={len(top_tracks)}`"
    )
    return (status_text,)


@app.cell
def _(
    chromosome,
    end_bp,
    mo,
    start_bp,
    status_text,
    wrapped_hg,
    zoom_btn,
):
    app_view = mo.vstack(
        [
            mo.hstack([chromosome, start_bp, end_bp, zoom_btn]),
            status_text,
            wrapped_hg,
        ]
    )
    app_view
    return


if __name__ == "__main__":
    app.run()
