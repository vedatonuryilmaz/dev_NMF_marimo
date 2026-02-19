import marimo

__generated_with = "0.19.11"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo
    import numpy as np
    import pandas as pd
    import plotly.graph_objects as go

    from nmf_vis.scatter import create_scatterplot
    from nmf_vis.heatmap import create_heatmap_figure

    return create_heatmap_figure, create_scatterplot, go, mo, np, pd


@app.cell
def _(mo):
    mo.md("# Explore cancer cCRE signatures")
    return


@app.cell
def _(mo):
    sort_method = mo.ui.dropdown(
        options=["component", "alphabetical", "cancer_type", "organ_system"],
        value="component",
        label="Sort by:",
    )
    return (sort_method,)


@app.cell
def _(pd):
    umap_data = pd.read_parquet("data/umap.parquet")
    return (umap_data,)


@app.cell
def _(create_scatterplot, sort_method):
    scatter = create_scatterplot(
        cfg_path="conf/config.json", sort_method=sort_method.value
    )
    return (scatter,)


@app.cell
def _(mo, scatter):
    scatter_widget = mo.ui.anywidget(scatter.widget)
    return (scatter_widget,)


@app.cell
def _(create_heatmap_figure, mo, scatter_widget, sort_method):
    selection = scatter_widget.selection

    selected_ids = None
    if selection is not None and len(selection) > 0:
        selected_ids = list(selection)
        caption = f"Showing {len(selection)} selected samples."
    else:
        caption = "Showing all samples. Use the lasso tool on the scatter to filter."

    fig = create_heatmap_figure(
        cfg_path="conf/config.json",
        sort_method=sort_method.value,
        selected_sample_ids=selected_ids,
    )

    heatmap_plot = mo.ui.plotly(fig)
    return caption, heatmap_plot, selected_ids


@app.cell
def _(caption, heatmap_plot, mo, scatter_widget, selected_ids, sort_method, umap_data):
    if selected_ids is not None and len(selected_ids) > 0:
        selected_df = umap_data.iloc[selected_ids].reset_index(drop=True)
    else:
        selected_df = umap_data

    mo.vstack(
        [
            sort_method,
            mo.md(f"**{caption}**"),
            mo.hstack([scatter_widget, heatmap_plot], widths=[0.4, 0.6]),
            mo.md("### Selected Samples"),
            mo.ui.table(selected_df),
        ]
    )
    return


if __name__ == "__main__":
    app.run()
