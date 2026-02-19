import marimo

__generated_with = "0.19.11"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo
    import higlass as hg
    import bioframe
    from higlass._scale import Scale

    return Scale, bioframe, hg, mo


@app.cell
def _(mo):
    mo.md(
        """
        # HiGlass: 796 ATAC-seq cancer samples

        Also view on [Resgen.io](https://resgen.io/abdenlab/tcga/full/Co53bAr9S4Czub18QCtQNw)!
        """
    )
    return


@app.cell
def _(hg):
    chromosome_labels = hg.remote(
        uid="ZpZ8c5JJRUS1J7ZkofcUrg",
        server="https://resgen.io/api/v1",
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
        server="https://resgen.io/api/v1",
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

    horizontal_multivec = hg.remote(
        uid="Ch8tF6b1TjuCobJERHmtjQ",
        server="https://resgen.io/api/v1",
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
        horizontal_multivec,
        initialXDomain=[1440763813.3127189, 1442990265.7390883],
        initialYDomain=[595697678.0762143, 595804705.51733],
    )

    hg_widget = view.widget()
    return hg_widget, view


@app.cell
def _(hg_widget, mo):
    wrapped_hg = mo.ui.anywidget(hg_widget)
    return (wrapped_hg,)


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
    hg_widget,
    mo,
    start_bp,
    view,
    wrapped_hg,
    zoom_btn,
):
    if zoom_btn.value:
        hg38 = bioframe.fetch_chromsizes("hg38")
        scale = Scale(hg38)
        hg_widget.zoom_to(
            view.uid,
            int(scale((chromosome.value, int(start_bp.value)))),
            int(scale((chromosome.value, int(end_bp.value)))),
        )

    mo.vstack(
        [
            mo.hstack([chromosome, start_bp, end_bp, zoom_btn]),
            wrapped_hg,
        ]
    )
    return


if __name__ == "__main__":
    app.run()
