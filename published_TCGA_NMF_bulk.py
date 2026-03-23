import marimo

__generated_with = "0.19.11"
app = marimo.App(width="full")


@app.cell
def _():
    import json
    import re

    return json, re


@app.cell
def _():
    """Bootstrap local code/data needed by the published notebook."""
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
        "numpy": "numpy>=2.3,<3",
        "pandas": "pandas>=3.0.0",
        "plotly": "plotly>=6.1.2",
        "pyarrow": "pyarrow>=18.0.0",
        "anywidget": "anywidget>=0.9.18",
        "jscatter": "jupyter-scatter[all]>=0.22.0",
        "seaborn": "seaborn>=0.13.2",
        "grandscatter": "grandscatter>=0.2.1",
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
                "The published notebook requires `uv` to install runtime "
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

    _module_files = [
        "nmf_vis/color_utils.py",
        "nmf_vis/data_utils.py",
        "nmf_vis/heatmap.py",
        "nmf_vis/upt_heatmap.py",
        "nmf_vis/scatter.py",
        "nmf_vis/sort_utils.py",
    ]
    _asset_files = [
        "conf/upt_pub_nmf_config.json",
        "conf/cancer_type_color_map.json",
        "conf/nmf_component_color_map.json",
        "conf/tissue_source_tcga.json",
        "conf/emb.json",
        "conf/vocab.json",
        "data/0302_corces_submitter_metadata_expanded_v2.csv",
        "data/canonical/tcga_atac_nmf_k24_H_proportions.csv",
        "data/canonical/tcga_atac_nmf_k24_H_proportions.npy",
        "data/canonical/tcga_atac_nmf_k24_metadata_sorted.csv",
        "data/canonical/tcga_atac_nmf_k24_umap_coordinates.csv",
        "data/cn-aware-unadjusted/confounded_nmf_k24_H_proportions.csv",
        "data/cn-aware-unadjusted/confounded_nmf_k24_H_proportions.npy",
        "data/cn-aware-unadjusted/confounded_nmf_k24_metadata_sorted.csv",
        "data/cn-aware-unadjusted/confounded_nmf_k24_umap_coordinates.csv",
        "data/cn-aware-adjusted/adjusted_nmf_k24_H_proportions.csv",
        "data/cn-aware-adjusted/adjusted_nmf_k24_H_proportions.npy",
        "data/cn-aware-adjusted/adjusted_nmf_k24_metadata_sorted.csv",
        "data/cn-aware-adjusted/adjusted_nmf_k24_umap_coordinates.csv",
    ]

    for _rel in [*_module_files, *_asset_files]:
        _dest = _Path(_rel)
        if not _dest.exists():
            _dest.parent.mkdir(parents=True, exist_ok=True)
            _req.urlretrieve(f"{pub_base_url}/{_rel}", _dest.as_posix())

    _pkg_init = _Path("nmf_vis/__init__.py")
    if not _pkg_init.exists():
        _pkg_init.write_text("", encoding="utf-8")

    _cwd = _os.getcwd()
    if _cwd not in _sys.path:
        _sys.path.insert(0, _cwd)

    bootstrap_ready = True
    cfg_path = "conf/upt_pub_nmf_config.json"
    heatmap_cfg_path = "conf/upt_pub_nmf_config.json"
    return bootstrap_ready, cfg_path, heatmap_cfg_path, pub_base_url


@app.cell
def _(bootstrap_ready):
    import marimo as mo
    import numpy as np
    import pandas as pd
    import plotly.graph_objects as go

    from nmf_vis.data_utils import (
        get_available_analyses,
        load_analysis_umap_data,
        resolve_analysis_cfg,
    )
    from nmf_vis.color_utils import distinct_palette
    from nmf_vis.upt_heatmap import (
        create_heatmap_figure,
        get_grandscatter_initial_projection,
    )

    return (
        create_heatmap_figure,
        distinct_palette,
        get_available_analyses,
        get_grandscatter_initial_projection,
        go,
        load_analysis_umap_data,
        mo,
        np,
        pd,
        resolve_analysis_cfg,
    )


@app.cell
def _(mo):
    mo.md("# Explore cancer cCRE signatures")
    return


@app.cell
def _(cfg_path, get_available_analyses, mo):
    analysis_options = get_available_analyses(cfg_path)
    analysis_name = mo.ui.dropdown(
        options=analysis_options,
        value=analysis_options[0],
        label="Analysis:",
    )
    return analysis_name, analysis_options


@app.cell
def _(mo):
    sort_method = mo.ui.dropdown(
        options=["component", "alphabetical", "cancer_type", "organ_system"],
        value="component",
        label="Sort by:",
    )
    return (sort_method,)


@app.cell
def _(cfg_path, json, pd):
    cfg = json.loads(open(cfg_path, "r", encoding="utf-8").read())
    strip_specs = cfg.get("HEATMAP_STRIPS", [])
    strip_spec_by_column = {spec["column"]: spec for spec in strip_specs}
    strip_field_labels = [spec.get("label", spec["column"]) for spec in strip_specs]
    strip_label_to_column = {
        spec.get("label", spec["column"]): spec["column"] for spec in strip_specs
    }
    strip_id_column = cfg.get("STRIP_METADATA_ID_COLUMN", "submitter_id")
    strip_metadata = (
        pd.read_csv(cfg["STRIP_METADATA_FILENAME"])
        .drop_duplicates(subset=[strip_id_column])
        .rename(columns={strip_id_column: "patient_id"})
    )
    cancer_color_map_path = cfg.get("JSON_FILENAME_CANCER_TYPE_COLORS")
    cancer_color_map = (
        json.loads(open(cancer_color_map_path, "r", encoding="utf-8").read())
        if cancer_color_map_path
        else {}
    )
    unknown_color = cfg.get("STRIP_UNKNOWN_COLOR", "#CCCCCC")
    return (
        cancer_color_map,
        strip_field_labels,
        strip_label_to_column,
        strip_metadata,
        strip_spec_by_column,
        unknown_color,
    )


@app.cell
def _(clinical_metadata, mo, strip_field_labels, strip_label_to_column):
    preferred_color_fields = [
        "Cancer Type",
        "cancer_type_full",
        "primary_diagnosis",
        "molecular_subtype",
        "vital_status",
        "sample_types",
        "gender",
        "race",
        "ethnicity",
        "ajcc_stage_simple",
        "received_surgery",
        "received_chemotherapy",
        "received_radiation",
        "received_hormone_therapy",
        "received_immunotherapy",
    ]
    color_field_labels = []
    for label in [*preferred_color_fields, *strip_field_labels]:
        if (
            label == "Cancer Type"
            or label in clinical_metadata.columns
            or label in strip_label_to_column
        ):
            if label not in color_field_labels:
                color_field_labels.append(label)
    color_field_to_column = {
        label: ("Cancer Type" if label == "Cancer Type" else label)
        for label in preferred_color_fields
        if label == "Cancer Type" or label in clinical_metadata.columns
    } | strip_label_to_column

    color_by = mo.ui.dropdown(
        options=color_field_labels,
        value="Cancer Type",
        label="Color by:",
    )
    return color_by, color_field_to_column


@app.cell
def _(mo):
    shared_selected_ids, set_shared_selected_ids = mo.state([])
    return set_shared_selected_ids, shared_selected_ids


@app.cell
def _(mo):
    metadata_tab_name, set_metadata_tab_name = mo.state("Overview")
    return metadata_tab_name, set_metadata_tab_name


@app.cell
def _(analysis_name, cfg_path, load_analysis_umap_data):
    umap_data = load_analysis_umap_data(cfg_path, analysis_name=analysis_name.value)
    return (umap_data,)


@app.cell
def _(analysis_name, set_shared_selected_ids):
    _selected_analysis = analysis_name.value

    def _clear_if_needed(current_ids):
        if not current_ids:
            return current_ids
        return []

    set_shared_selected_ids(_clear_if_needed)
    return (_selected_analysis,)


@app.cell
def _(umap_data):
    sample_id_to_index = {
        str(sample_id): int(index)
        for index, sample_id in enumerate(umap_data["Sample ID"].astype(str).tolist())
    }
    return (sample_id_to_index,)


@app.cell
def _(pd, pub_base_url):
    clinical_metadata = pd.read_csv(
        f"{pub_base_url}/data/unified_clinical_metadata_tcga_corces_unified_clinical_metadata_final.csv"
    )
    metadata_tooltips = (
        pd.read_csv(
            f"{pub_base_url}/data/unified_clinical_metadata_data_dictionary_final.csv"
        )
        .dropna(subset=["description"])
        .drop_duplicates(subset=["column"])
        .set_index("column")["description"]
        .to_dict()
    )
    return clinical_metadata, metadata_tooltips


@app.cell
def _(pd, re):
    def patient_id_from_sample_id(sample_id):
        parts = str(sample_id).split("-")
        if len(parts) >= 4 and parts[1] == "TCGA":
            return "-".join(parts[1:4])
        if len(parts) >= 3 and parts[0] == "TCGA":
            return "-".join(parts[:3])
        return None

    def _unique_sorted_unknown_last(values):
        unique_values = sorted({str(value) for value in values if pd.notna(value)})
        if "Unknown" in unique_values:
            unique_values = [
                value for value in unique_values if value != "Unknown"
            ] + ["Unknown"]
        return unique_values

    def _cohort_color_lookup(values, cancer_color_map, unknown_color):
        lookup = {}
        for value in _unique_sorted_unknown_last(values):
            if value == "Unknown":
                lookup[value] = unknown_color
                continue

            preferred_keys = [value, f"{value}x", f"{value}xx"]
            color = None
            for key in preferred_keys:
                color = cancer_color_map.get(key)
                if color is not None:
                    break
            if color is None:
                for key, candidate in cancer_color_map.items():
                    if str(key).startswith(value):
                        color = candidate
                        break
            lookup[value] = color or unknown_color
        return lookup

    def build_color_lookup(
        distinct_palette,
        values,
        selected_color_column,
        strip_spec_by_column,
        cancer_color_map,
        unknown_color,
    ):
        if selected_color_column == "Cancer Type":
            return _cohort_color_lookup(values, cancer_color_map, unknown_color)

        strip_spec = strip_spec_by_column.get(selected_color_column)
        if strip_spec is None:
            unique_values = _unique_sorted_unknown_last(values)
            non_unknown = [value for value in unique_values if value != "Unknown"]
            palette = distinct_palette(max(1, len(non_unknown)))
            lookup = {}
            palette_index = 0
            for value in unique_values:
                if value == "Unknown":
                    lookup[value] = unknown_color
                else:
                    lookup[value] = palette[palette_index % len(palette)]
                    palette_index += 1
            return lookup

        if strip_spec.get("palette_source") == "cancer_type_colors":
            return _cohort_color_lookup(values, cancer_color_map, unknown_color)

        if "color_map" in strip_spec:
            lookup = {
                str(key): str(color)
                for key, color in strip_spec["color_map"].items()
            }
            lookup.setdefault("Unknown", unknown_color)
            return lookup

        palette = [str(color) for color in strip_spec.get("palette", [])]
        unique_values = _unique_sorted_unknown_last(values)
        if not palette:
            return {
                value: unknown_color if value == "Unknown" else unknown_color
                for value in unique_values
            }

        lookup = {}
        for index, value in enumerate(unique_values):
            if value == "Unknown":
                lookup[value] = unknown_color
            else:
                lookup[value] = palette[index % len(palette)]
        return lookup

    def standardize_sample_id_column(df):
        candidate_columns = [
            "sample_id",
            "Sample ID",
            "Sample_ID",
            "sample",
            "Unnamed: 0",
        ]
        for candidate in candidate_columns:
            if candidate in df.columns:
                if candidate == "Sample ID":
                    return df, candidate
                return df.rename(columns={candidate: "Sample ID"}), "Sample ID"
        first_column = df.columns[0]
        return df.rename(columns={first_column: "Sample ID"}), "Sample ID"

    def sorted_component_columns(df):
        def component_index(column_name):
            match = re.match(r"(?i)^comp(?:onent)?[_\\s-]*(\\d+)$", str(column_name).strip())
            return int(match.group(1)) if match else None

        indexed_columns = [
            (component_index(column), column)
            for column in df.columns
            if column != "Sample ID"
        ]
        explicit_components = [
            (index, column) for index, column in indexed_columns if index is not None
        ]
        if explicit_components:
            return [column for _, column in sorted(explicit_components, key=lambda item: item[0])]
        return [
            column
            for column in df.columns
            if column != "Sample ID" and pd.api.types.is_numeric_dtype(df[column])
        ]

    return (
        build_color_lookup,
        patient_id_from_sample_id,
        sorted_component_columns,
        standardize_sample_id_column,
    )


@app.cell
def _(clinical_metadata, patient_id_from_sample_id, strip_metadata, umap_data):
    umap_display_df = umap_data.copy()
    umap_display_df["patient_id"] = umap_display_df["Sample ID"].map(patient_id_from_sample_id)
    umap_display_df = umap_display_df.merge(clinical_metadata, on="patient_id", how="left")
    umap_display_df = umap_display_df.merge(strip_metadata, on="patient_id", how="left")
    return (umap_display_df,)


@app.cell
def _(
    build_color_lookup,
    cancer_color_map,
    color_by,
    color_field_to_column,
    distinct_palette,
    strip_spec_by_column,
    umap_display_df,
    unknown_color,
):
    selected_color_column = color_field_to_column[color_by.value]
    scatter_display_df = umap_display_df.copy()
    if selected_color_column not in scatter_display_df.columns:
        scatter_display_df[selected_color_column] = "Unknown"
    scatter_display_df["Color Label"] = (
        scatter_display_df[selected_color_column]
        .fillna("Unknown")
        .astype(str)
    )
    sample_color_map = build_color_lookup(
        distinct_palette,
        scatter_display_df["Color Label"].tolist(),
        selected_color_column,
        strip_spec_by_column,
        cancer_color_map,
        unknown_color,
    )
    return sample_color_map, scatter_display_df, selected_color_column


@app.cell
def _(color_by, sample_color_map, scatter_display_df):
    import jscatter

    tooltip_fields = ["Sample ID", "Cancer Type", "Color Label"]
    scatter = jscatter.Scatter(
        data=scatter_display_df,
        x="UMAP-1",
        y="UMAP-2",
        color_by="Color Label",
        color_map=sample_color_map,
        height=600,
        width=600,
        lasso_callback=True,
        selection_mode="lasso",
    )
    scatter.tooltip(enable=True, properties=tooltip_fields)
    scatter.size(default=5)
    scatter.options(
        {
            "aspectRatio": 1.0,
            "regl_scatterplot_options": {
                "showLegend": True,
                "xAxis": {"showGrid": True},
                "yAxis": {"showGrid": True},
                "title": f"UMAP of NMF Components (colored by {color_by.value})",
            },
        }
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
        normalized_values = sorted({int(v) for v in values})
        return normalized_values

    return (normalize_selection,)


@app.cell
def _(pd):
    def extract_selection_indices(table_value):
        if table_value is None:
            return []

        if isinstance(table_value, pd.DataFrame):
            if "selection_index" not in table_value.columns:
                return []
            values = table_value["selection_index"].dropna().tolist()
        elif isinstance(table_value, list):
            values = []
            for row in table_value:
                if not isinstance(row, dict):
                    continue
                value = row.get("selection_index")
                if value is not None and pd.notna(value):
                    values.append(value)
        else:
            return []

        return sorted({int(value) for value in values})

    return (extract_selection_indices,)


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
def _(
    normalize_selection,
    scatter_widget,
    set_shared_selected_ids,
):
    _incoming_ids = normalize_selection(scatter_widget.selection)

    def _update_if_changed(current_ids):
        return current_ids if normalize_selection(current_ids) == _incoming_ids else _incoming_ids

    set_shared_selected_ids(_update_if_changed)
    return


@app.cell
def _(analysis_name, create_heatmap_figure, heatmap_cfg_path, mo, shared_selected_ids, sort_method):
    selection = shared_selected_ids()

    selected_ids = None
    if selection is not None and len(selection) > 0:
        selected_ids = list(selection)
        caption = f"Showing {len(selection)} selected samples."
    else:
        caption = "Showing all samples. Select samples in the scatter, heatmap, or grandscatter to link all views."

    fig = create_heatmap_figure(
        cfg_path=heatmap_cfg_path,
        sort_method=sort_method.value,
        selected_sample_ids=selected_ids,
        analysis_name=analysis_name.value,
    )

    heatmap_plot = mo.ui.plotly(fig)

    return caption, heatmap_plot, selected_ids


@app.cell
def _(heatmap_plot, sample_id_to_index):
    def extract_selected_sample_ids(plot_points):
        seen = set()
        for point in plot_points or []:
            if not isinstance(point, dict):
                continue
            sample_id = point.get("x")
            if sample_id is None:
                continue
            sample_id = str(sample_id)
            if sample_id not in sample_id_to_index:
                continue
            seen.add(sample_id)
        return sorted(seen, key=lambda sample_id: sample_id_to_index[sample_id])

    heatmap_selected_sample_ids = extract_selected_sample_ids(heatmap_plot.value)
    return extract_selected_sample_ids, heatmap_selected_sample_ids


@app.cell
def _(build_metadata_views, clinical_metadata, selected_ids, strip_metadata, umap_data):
    enriched_metadata = clinical_metadata.merge(strip_metadata, on="patient_id", how="left")
    (
        _selected_assay_df,
        selected_metadata_df,
        duplicate_patients_df,
        metadata_summary,
    ) = build_metadata_views(umap_data, enriched_metadata, selected_ids)
    return (
        duplicate_patients_df,
        metadata_summary,
        selected_metadata_df,
    )


@app.cell
def _(
    analysis_name,
    cfg_path,
    mo,
    pd,
    resolve_analysis_cfg,
    sample_color_map,
    scatter_display_df,
    sorted_component_columns,
    standardize_sample_id_column,
):
    """Grandscatter: interactive multi-dimensional NMF proportion explorer.

    Create in a dedicated cell to simplify Marimo binding lifecycle.
    Drag axis handles to rotate the 24-component NMF proportion cloud.
    Uses orthographic projection (default) so all data points are always
    within the axis extents at every rotation angle.
    """
    try:
        from grandscatter import Scatter

        resolved_cfg = resolve_analysis_cfg(cfg_path, analysis_name=analysis_name.value)
        component_path = resolved_cfg.get(
            "GRANDSCATTER_CSV_FILENAME",
            resolved_cfg.get("DEFAULT_CSV_FILENAME"),
        )
        component_df, _sample_id_column = standardize_sample_id_column(
            pd.read_csv(component_path)
        )
        axis_fields = sorted_component_columns(component_df)
        grandscatter_df = component_df[["Sample ID", *axis_fields]].copy()
        grandscatter_df = grandscatter_df.merge(
            scatter_display_df[["Sample ID", "Color Label"]],
            on="Sample ID",
            how="left",
        )
        grandscatter_df["Color Label"] = (
            grandscatter_df["Color Label"].fillna("Unknown").astype(str).astype("category")
        )
        gs_widget = Scatter(
            grandscatter_df[[*axis_fields, "Color Label"]],
            axis_fields=axis_fields,
            label_field="Color Label",
            label_colors=sample_color_map,
            base_point_size=6,
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
def _(
    gs_widget,
    normalize_selection,
    set_shared_selected_ids,
):
    if gs_widget is not None:
        def _sync_grandscatter_selection(change):
            incoming_ids = normalize_selection(change.get("new"))

            def _update_if_changed(current_ids):
                normalized_current = normalize_selection(current_ids)
                return (
                    current_ids
                    if normalized_current == incoming_ids
                    else incoming_ids
                )

            set_shared_selected_ids(_update_if_changed)

        _observer = getattr(gs_widget, "_marimo_selection_observer", None)
        if _observer is not None:
            gs_widget.unobserve(_observer, names="selected_points")

        gs_widget.observe(_sync_grandscatter_selection, names="selected_points")
        gs_widget._marimo_selection_observer = _sync_grandscatter_selection
    return


@app.cell
def _(
    heatmap_selected_sample_ids,
    sample_id_to_index,
    set_shared_selected_ids,
):
    _incoming_ids = sorted(
        {sample_id_to_index[sample_id] for sample_id in heatmap_selected_sample_ids}
    )

    if heatmap_selected_sample_ids:
        def _update_if_changed(current_ids):
            return current_ids if current_ids == _incoming_ids else _incoming_ids

        set_shared_selected_ids(_update_if_changed)
    return


@app.cell
def _(normalize_selection, scatter_widget, shared_selected_ids):
    target_ids = shared_selected_ids()
    _current_ids = normalize_selection(scatter_widget.selection)
    if _current_ids != target_ids:
        scatter_widget.selection = target_ids
    return


@app.cell
def _(analysis_name, cfg_path, get_grandscatter_initial_projection, mo):
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
        proj = get_grandscatter_initial_projection(
            cfg_path,
            analysis_name=analysis_name.value,
        )
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
  const widget = document.querySelector(".grandscatter-widget");
  if (!widget) {{ requestAnimationFrame(attach); return; }}
  const canvas = widget.querySelector("canvas");
  if (!canvas) {{ requestAnimationFrame(attach); return; }}

  canvas.addEventListener("mousemove", (e) => {{
    const r = canvas.getBoundingClientRect();
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
    extract_selection_indices,
    format_mapping,
    grandscatter_plot,
    heatmap_plot,
    hover_overlay,
    analysis_name,
    color_by,
    metadata_tab_name,
    metadata_groups,
    metadata_summary,
    metadata_tooltips,
    mo,
    normalize_selection,
    scatter_widget,
    set_metadata_tab_name,
    set_shared_selected_ids,
    selected_metadata_df,
    sort_method,
    wrapped_columns,
):
    header_tooltips = {**metadata_tooltips, **base_tooltips}
    table_initial_selection = (
        list(range(len(selected_metadata_df))) if metadata_summary["is_filtered"] else None
    )

    def make_table(
        dataframe,
        columns,
        label,
        page_size=12,
        max_height=360,
        *,
        selection=None,
        initial_selection=None,
    ):
        available_columns = [column for column in columns if column in dataframe.columns]

        def _sync_table_selection(table_value):
            selected_indices = extract_selection_indices(table_value)

            def _update_if_changed(current_ids):
                normalized_current = normalize_selection(current_ids)
                return (
                    current_ids
                    if normalized_current == selected_indices
                    else selected_indices
                )

            set_shared_selected_ids(_update_if_changed)

        return mo.ui.table(
            dataframe[available_columns],
            selection=selection,
            initial_selection=initial_selection,
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
            on_change=_sync_table_selection if selection is not None else None,
        )

    metadata_tables = {
        name: make_table(
            selected_metadata_df,
            columns,
            f"{name} metadata",
            selection="multi",
            initial_selection=table_initial_selection,
        )
        for name, columns in metadata_groups.items()
    }
    metadata_tables["All metadata"] = make_table(
        selected_metadata_df,
        list(selected_metadata_df.columns),
        "All linked metadata",
        page_size=10,
        max_height=420,
        selection="multi",
        initial_selection=table_initial_selection,
    )
    active_metadata_tab = metadata_tab_name()
    if active_metadata_tab not in metadata_tables:
        active_metadata_tab = next(iter(metadata_tables))

    metadata_tabs = mo.ui.tabs(
        metadata_tables,
        value=active_metadata_tab,
        on_change=lambda selected_tab: set_metadata_tab_name(
            lambda current_tab: (
                current_tab if current_tab == selected_tab else selected_tab
            )
        ),
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
            mo.hstack([analysis_name, sort_method, color_by], widths=[0.3, 0.3, 0.3]),
            mo.md(f"**{caption}**"),
            mo.hstack([scatter_widget, heatmap_plot], widths=[0.4, 0.6]),
            mo.md("### Multi-Dimensional NMF Proportions"),
            mo.md(
                "_Drag axis handles to rotate and explore the 24-dimensional NMF "
                "proportion space.  "
                "Hover over a point to see its cancer type and dominant component.  "
                "Selections stay linked with the scatter, heatmap, and metadata table._"
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
    return metadata_tables, metadata_tabs


if __name__ == "__main__":
    app.run()
