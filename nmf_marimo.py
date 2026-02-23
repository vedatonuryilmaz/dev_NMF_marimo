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
    from nmf_vis.heatmap import (
        create_heatmap_figure,
        create_grandscatter_widget,
        get_grandscatter_initial_projection,
    )

    return create_grandscatter_widget, create_heatmap_figure, create_scatterplot, get_grandscatter_initial_projection, go, mo, np, pd


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
def _(create_grandscatter_widget, mo):
    """Grandscatter: interactive multi-dimensional NMF proportion explorer.

    Create in a dedicated cell to simplify Marimo binding lifecycle.
    Drag axis handles to rotate the 16-dim NMF proportion cloud.
    Uses orthographic projection (default) so all data points are always
    within the axis extents at every rotation angle.
    """
    try:
        gs_widget = create_grandscatter_widget(
            cfg_path="conf/config.json",
            selected_sample_ids=None,
        )
        grandscatter_plot = mo.ui.anywidget(gs_widget)
    except Exception as e:
        gs_widget = None
        grandscatter_plot = mo.md(
            f"**\u26a0\ufe0f Grandscatter widget error:** {type(e).__name__}: {str(e)[:200]}\n\n"
            f"Please check the browser console for details."
        )

    return grandscatter_plot, gs_widget


@app.cell
def _(get_grandscatter_initial_projection, mo):
    """Build a JS hover-tooltip overlay for the grandscatter widget.

    Pre-computes the initial orthographic 2-D positions using the same
    circular basis that grandscatter uses on first render.  A floating
    tooltip shows *(cancer type, dominant component)* for the nearest
    sample whenever the mouse is within a small radius of a data point.

    The tooltip is accurate for the initial view; after axis rotation the
    closest match may shift slightly, but remains a good approximation.
    Use the lasso tool for precise selection after rotating axes.
    """
    import json as _json

    try:
        proj = get_grandscatter_initial_projection("conf/config.json")
        points_json = _json.dumps(proj["points"])
    except Exception:
        points_json = "[]"

    tooltip_html = f"""
<style>
  .gs-tooltip {{
    position: fixed;
    background: rgba(15,15,15,0.82);
    color: #f0f0f0;
    padding: 5px 10px;
    border-radius: 5px;
    font-size: 12px;
    font-family: monospace;
    pointer-events: none;
    display: none;
    z-index: 9999;
    white-space: nowrap;
    box-shadow: 0 2px 8px rgba(0,0,0,0.4);
  }}
</style>
<div class="gs-tooltip" id="gs-hover-tip"></div>
<script type="module">
const POINTS = {points_json};
const tip = document.getElementById("gs-hover-tip");

function nearest(nx, ny) {{
  let best = null, bestD = Infinity;
  for (let i = 0; i < POINTS.length; i++) {{
    const p = POINTS[i];
    const d = (p.x - nx) ** 2 + (p.y - ny) ** 2;
    if (d < bestD) {{ bestD = d; best = p; }}
  }}
  return {{ ...best, dist: bestD }};
}}

function attach() {{
  // Wait for the grandscatter container and its canvas
  const widget = document.querySelector(".grandscatter-widget");
  if (!widget) {{ requestAnimationFrame(attach); return; }}
  const canvas = widget.querySelector("canvas");
  if (!canvas) {{ requestAnimationFrame(attach); return; }}

  canvas.addEventListener("mousemove", (e) => {{
    const r = canvas.getBoundingClientRect();
    // Map pixel → [-1, 1] NDC (y flipped for screen-to-math coords)
    const nx = (e.clientX - r.left) / r.width  * 2 - 1;
    const ny = -((e.clientY - r.top)  / r.height * 2 - 1);
    const hit = nearest(nx, ny);
    if (hit && hit.dist < 0.03) {{
      tip.innerHTML = "<b>" + hit.ct + "</b> &nbsp;|&nbsp; Comp_" + hit.comp;
      tip.style.display = "block";
      tip.style.left = (e.clientX + 14) + "px";
      tip.style.top  = (e.clientY - 36) + "px";
    }} else {{
      tip.style.display = "none";
    }}
  }});

  canvas.addEventListener("mouseleave", () => {{ tip.style.display = "none"; }});
}}

attach();
</script>
"""

    hover_overlay = mo.Html(tooltip_html)
    return hover_overlay,


@app.cell
def _(gs_widget, selected_ids):
    if gs_widget is not None:
        # Update selection on existing widget for fast feedback
        if selected_ids is not None and len(selected_ids) > 0:
            gs_widget.selected_points = selected_ids
        else:
            gs_widget.selected_points = []
    return


@app.cell
def _(caption, grandscatter_plot, hover_overlay, heatmap_plot, mo, scatter_widget, selected_ids, sort_method, umap_data):
    if selected_ids is not None and len(selected_ids) > 0:
        selected_df = umap_data.iloc[selected_ids].reset_index(drop=True)
    else:
        selected_df = umap_data

    mo.vstack(
        [
            sort_method,
            mo.md(f"**{caption}**"),
            mo.hstack([scatter_widget, heatmap_plot], widths=[0.4, 0.6]),
            mo.md("### Multi-Dimensional NMF Proportions"),
            mo.md(
                "_Drag axis handles to rotate and explore the 16-dimensional NMF "
                "proportion space.  "
                "Hover over a point to see its cancer type and dominant component.  "
                "Use the lasso tool to select samples and filter the heatmap & table._"
            ),
            hover_overlay,
            grandscatter_plot,
            mo.md("### Selected Samples"),
            mo.ui.table(selected_df),
        ]
    )
    return


if __name__ == "__main__":
    app.run()
