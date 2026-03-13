import marimo

__generated_with = "0.20.2"
app = marimo.App()


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # `uv sync` (includes `higlass-python`)


    ## 796 ATAC-seq cancer samples

    Also view on [Resgen.io](https://resgen.io/abdenlab/tcga/full/Co53bAr9S4Czub18QCtQNw)!
    """)
    return


@app.cell
def _():
    # import json
    # import higlass as hg

    # with open("conf/viewconf.json", "r") as f:
    #     viewconf = hg.Viewconf(**json.load(f))

    # viewconf
    return


@app.cell
def _():
    import higlass as hg


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

    horizontal_stacked_bar = hg.remote(
        uid="HMSJyvLCSgGmrDJctdIz3w",
        server="https://resgen.io/api/v1",
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
        (horizontal_stacked_bar, "top"),
        horizontal_multivec,
        initialXDomain=[1440763813.3127189, 1442990265.7390883],
        initialYDomain=[595697678.0762143, 595804705.51733],
    )

    widget = view.widget()

    widget
    return view, widget


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
