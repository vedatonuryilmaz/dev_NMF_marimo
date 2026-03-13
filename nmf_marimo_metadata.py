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
def _(mo):
    shared_selected_ids, set_shared_selected_ids = mo.state([])
    return set_shared_selected_ids, shared_selected_ids


@app.cell
def _(pd):
    umap_data = pd.read_parquet("data/umap.parquet")
    return (umap_data,)


@app.cell
def _(pd):
    clinical_metadata = pd.read_csv(
        "data/unified_clinical_metadata_tcga_corces_unified_clinical_metadata_final.csv"
    )
    metadata_tooltips = (
        pd.read_csv("data/unified_clinical_metadata_data_dictionary_final.csv")
        .dropna(subset=["description"])
        .drop_duplicates(subset=["column"])
        .set_index("column")["description"]
        .to_dict()
    )
    return clinical_metadata, metadata_tooltips


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
def _(np):
    def normalize_selection(selection):
        if selection is None:
            return []
        if isinstance(selection, np.ndarray):
            values = selection.tolist()
        else:
            values = list(selection)
        return [int(v) for v in values]

    return (normalize_selection,)


@app.cell
def _(pd):
    metadata_groups = {
        "Overview": [
            "selection_index",
            "Sample ID",
            "patient_id",
            "Cancer Type",
            "UMAP-1",
            "UMAP-2",
            "cancer_type_full",
            "primary_diagnosis",
            "molecular_subtype",
            "vital_status",
            "age_at_diagnosis_years",
            "sample_types",
            "tss_enrichment_mean",
            "frip_mean",
            "final_reads_mean",
        ],
        "Demographics": [
            "selection_index",
            "Sample ID",
            "patient_id",
            "cancer_type",
            "cancer_type_full",
            "age_at_diagnosis_years",
            "gender",
            "race",
            "ethnicity",
            "sample_types",
            "laterality",
        ],
        "Diagnosis & Stage": [
            "selection_index",
            "Sample ID",
            "patient_id",
            "cancer_type",
            "primary_diagnosis",
            "morphology_code",
            "tissue_or_organ_of_origin",
            "tumor_grade",
            "residual_disease",
            "ajcc_stage_simple",
            "ajcc_pathologic_stage",
            "ajcc_pathologic_t",
            "ajcc_pathologic_n",
            "ajcc_pathologic_m",
        ],
        "Survival & Treatment": [
            "selection_index",
            "Sample ID",
            "patient_id",
            "vital_status",
            "os_event",
            "os_time_days",
            "os_time_months",
            "days_to_death",
            "days_to_last_followup",
            "received_surgery",
            "received_chemotherapy",
            "received_radiation",
            "received_hormone_therapy",
            "received_immunotherapy",
            "treatment_types",
            "treatment_outcomes",
        ],
        "Molecular & QC": [
            "selection_index",
            "Sample ID",
            "patient_id",
            "molecular_subtype",
            "subtype_method",
            "subtype_source",
            "subtype_available",
            "receptor_status",
            "brca_ic10",
            "msi_mantis_score",
            "msi_sensor_score",
            "batch_numbers",
            "tss_enrichment_mean",
            "frip_mean",
            "final_reads_mean",
        ],
    }
    base_tooltips = {
        "selection_index": "Row index in the linked assay views used for synchronized selections.",
        "Sample ID": "ATAC-seq sample barcode shown in the scatter, heatmap, and grandscatter views.",
        "Cancer Type": "Cancer type label from the assay view used for coloring and selection.",
        "UMAP-1": "First UMAP embedding coordinate from the assay view.",
        "UMAP-2": "Second UMAP embedding coordinate from the assay view.",
        "sample_count": "Number of assay rows currently linked to the same patient_id.",
        "sample_ids": "Semicolon-delimited sample barcodes linked to this patient in the current view.",
        "cancer_types": "Cancer type labels represented by the repeated assay rows.",
    }
    wrapped_columns = [
        "Sample ID",
        "sample_ids",
        "cancer_type_full",
        "primary_diagnosis",
        "tissue_or_organ_of_origin",
        "treatment_types",
        "treatment_outcomes",
        "molecular_subtype",
        "subtype_method",
        "subtype_source",
        "receptor_status",
        "batch_numbers",
    ]
    format_mapping = {
        "UMAP-1": "{:.2f}",
        "UMAP-2": "{:.2f}",
        "age_at_diagnosis_years": "{:.1f}",
        "os_time_days": "{:.0f}",
        "os_time_months": "{:.1f}",
        "days_to_death": "{:.0f}",
        "days_to_last_followup": "{:.0f}",
        "msi_mantis_score": "{:.3f}",
        "msi_sensor_score": "{:.3f}",
        "tss_enrichment_mean": "{:.2f}",
        "frip_mean": "{:.3f}",
        "final_reads_mean": "{:,.0f}",
    }
    flag_columns = [
        "os_event",
        "received_surgery",
        "received_chemotherapy",
        "received_radiation",
        "received_hormone_therapy",
        "received_immunotherapy",
        "subtype_available",
    ]

    def format_flag(value):
        if pd.isna(value):
            return None
        normalized = str(value).strip().lower()
        if normalized in {"true", "1", "yes"}:
            return "Yes"
        if normalized in {"false", "0", "no"}:
            return "No"
        return value

    for _column in flag_columns:
        format_mapping[_column] = format_flag

    def patient_id_from_sample_id(sample_id):
        parts = str(sample_id).split("-")
        if len(parts) >= 4 and parts[1] == "TCGA":
            return "-".join(parts[1:4])
        if len(parts) >= 3 and parts[0] == "TCGA":
            return "-".join(parts[:3])
        return None

    def summarize_cancer_types(cancer_types):
        unique_types = sorted({str(value) for value in cancer_types if pd.notna(value)})
        if len(unique_types) <= 6:
            return ", ".join(unique_types)
        return f"{', '.join(unique_types[:6])} + {len(unique_types) - 6} more"

    def build_metadata_views(umap_df, clinical_df, selected_ids):
        if selected_ids is not None and len(selected_ids) > 0:
            assay_df = umap_df.iloc[selected_ids].copy()
            is_filtered = True
        else:
            assay_df = umap_df.copy()
            is_filtered = False

        assay_df = assay_df.reset_index().rename(columns={"index": "selection_index"})
        assay_df["patient_id"] = assay_df["Sample ID"].map(patient_id_from_sample_id)

        merged_df = assay_df.merge(clinical_df, on="patient_id", how="left")

        duplicate_patients = (
            assay_df.groupby("patient_id", dropna=False)
            .agg(
                sample_count=("Sample ID", "size"),
                cancer_types=("Cancer Type", summarize_cancer_types),
                sample_ids=("Sample ID", lambda values: "; ".join(map(str, values))),
            )
            .reset_index()
        )
        duplicate_patients = duplicate_patients[duplicate_patients["sample_count"] > 1]

        summary = {
            "is_filtered": is_filtered,
            "sample_count": int(len(assay_df)),
            "unique_patient_count": int(assay_df["patient_id"].nunique(dropna=True)),
            "matched_sample_count": int(merged_df["case_uuid"].notna().sum()),
            "duplicate_patient_count": int(len(duplicate_patients)),
            "cancer_type_count": int(assay_df["Cancer Type"].nunique(dropna=True)),
            "cancer_types_label": summarize_cancer_types(assay_df["Cancer Type"]),
        }

        return assay_df, merged_df, duplicate_patients, summary

    return base_tooltips, build_metadata_views, format_mapping, metadata_groups, wrapped_columns


@app.cell
def _(normalize_selection, scatter_widget, set_shared_selected_ids):
    _incoming_ids = normalize_selection(scatter_widget.selection)

    def _update(current_ids):
        if _incoming_ids == current_ids:
            return current_ids
        return _incoming_ids

    set_shared_selected_ids(_update)
    return


@app.cell
def _(create_heatmap_figure, mo, shared_selected_ids, sort_method):
    selection = shared_selected_ids()

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
def _(build_metadata_views, clinical_metadata, selected_ids, umap_data):
    (
        _selected_assay_df,
        selected_metadata_df,
        duplicate_patients_df,
        metadata_summary,
    ) = build_metadata_views(umap_data, clinical_metadata, selected_ids)
    return (
        duplicate_patients_df,
        metadata_summary,
        selected_metadata_df,
    )


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
def _(gs_widget, normalize_selection, set_shared_selected_ids):
    if gs_widget is not None:
        _incoming_ids = normalize_selection(gs_widget.selected_points)

        def _update(current_ids):
            if _incoming_ids == current_ids:
                return current_ids
            return _incoming_ids

        set_shared_selected_ids(_update)
    return


@app.cell
def _(normalize_selection, scatter_widget, shared_selected_ids):
    target_ids = shared_selected_ids()
    _current_ids = normalize_selection(scatter_widget.selection)
    if _current_ids != target_ids:
        scatter_widget.selection = target_ids
    return


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
      tip.innerHTML = "<b>" + hit.ct + "</b> &nbsp;|&nbsp; " + hit.comp;
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
def _(gs_widget, normalize_selection, shared_selected_ids):
    _selected_ids = shared_selected_ids()
    if gs_widget is not None:
        _current_ids = normalize_selection(gs_widget.selected_points)
        if _current_ids != _selected_ids:
            gs_widget.selected_points = _selected_ids
    return


@app.cell
def _(
    base_tooltips,
    caption,
    duplicate_patients_df,
    format_mapping,
    grandscatter_plot,
    heatmap_plot,
    hover_overlay,
    metadata_groups,
    metadata_summary,
    metadata_tooltips,
    mo,
    scatter_widget,
    selected_metadata_df,
    sort_method,
    wrapped_columns,
):
    header_tooltips = {**metadata_tooltips, **base_tooltips}

    def make_table(dataframe, columns, label, page_size=12, max_height=360):
        available_columns = [column for column in columns if column in dataframe.columns]
        return mo.ui.table(
            dataframe[available_columns],
            selection=None,
            pagination=True,
            page_size=page_size,
            show_data_types=False,
            show_column_summaries=False,
            freeze_columns_left=[
                column
                for column in ["selection_index", "Sample ID", "patient_id"]
                if column in available_columns
            ],
            wrapped_columns=[
                column for column in wrapped_columns if column in available_columns
            ],
            header_tooltip={
                column: header_tooltips[column]
                for column in available_columns
                if column in header_tooltips
            },
            format_mapping={
                column: format_mapping[column]
                for column in available_columns
                if column in format_mapping
            },
            max_height=max_height,
            label=label,
        )

    metadata_tabs = mo.ui.tabs(
        {
            name: make_table(selected_metadata_df, columns, f"{name} metadata")
            for name, columns in metadata_groups.items()
        }
        | {
            "All metadata": make_table(
                selected_metadata_df,
                list(selected_metadata_df.columns),
                "All linked metadata",
                page_size=10,
                max_height=420,
            )
        }
    )

    duplicate_patients_view = (
        mo.accordion(
            {
                "Patients with multiple ATAC-seq samples in this view": make_table(
                    duplicate_patients_df,
                    ["patient_id", "sample_count", "cancer_types", "sample_ids"],
                    "Repeated patients",
                    page_size=8,
                    max_height=260,
                )
            },
            lazy=True,
        )
        if not duplicate_patients_df.empty
        else mo.md("_No repeated patient IDs in the current view._")
    )

    metadata_scope = (
        "Current selection" if metadata_summary["is_filtered"] else "All assay samples"
    )
    metadata_caption = (
        f"{metadata_summary['matched_sample_count']}/{metadata_summary['sample_count']} "
        "rows matched the unified clinical metadata table. "
        f"Cancer types in view: {metadata_summary['cancer_types_label']}."
    )

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
            mo.md("### Linked Clinical Metadata"),
            mo.md(
                f"_{metadata_scope}: {metadata_caption}_"
            ),
            mo.hstack(
                [
                    mo.stat(
                        metadata_summary["sample_count"],
                        label="Samples in view",
                        caption="Assay rows linked to the current selection.",
                        bordered=True,
                    ),
                    mo.stat(
                        metadata_summary["unique_patient_count"],
                        label="Unique patients",
                        caption="Distinct `patient_id` values in view.",
                        bordered=True,
                    ),
                    mo.stat(
                        metadata_summary["cancer_type_count"],
                        label="Cancer types",
                        caption="Distinct cancer labels represented in view.",
                        bordered=True,
                    ),
                    mo.stat(
                        metadata_summary["duplicate_patient_count"],
                        label="Repeated patients",
                        caption="Patients appearing in more than one assay row.",
                        bordered=True,
                    ),
                ],
                widths=[1, 1, 1, 1],
            ),
            duplicate_patients_view,
            metadata_tabs,
        ]
    )
    return


if __name__ == "__main__":
    app.run()
