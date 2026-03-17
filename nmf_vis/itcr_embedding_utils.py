from __future__ import annotations

import html
import json
import re
from pathlib import Path

import jscatter
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

CLINICAL_METADATA_PATH = Path(
    "data/unified_clinical_metadata_tcga_corces_unified_clinical_metadata_final.csv"
)
METADATA_DICTIONARY_PATH = Path(
    "data/unified_clinical_metadata_data_dictionary_final.csv"
)
CANCER_COLOR_PATH = Path("conf/cancer_type_color_map.json")
COMPONENT_COLOR_PATH = Path("conf/nmf_component_color_map.json")
ORGAN_SYSTEM_PATH = Path("conf/tissue_source_tcga.json")
EMBRYONIC_LAYER_PATH = Path("conf/emb.json")

_METADATA_GROUPS = {
    "Overview": [
        "selection_index",
        "Sample ID",
        "patient_id",
        "Cancer Type",
        "Color Label",
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
        "Cancer Type",
        "Color Label",
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
        "Cancer Type",
        "Color Label",
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

_BASE_TOOLTIPS = {
    "selection_index": "Row index in the linked embedding views used for synchronized selections.",
    "Sample ID": "ATAC-seq sample barcode used across the linked 2D scatters, heatmaps, grandscatter views, and metadata tables.",
    "Cancer Type": "Four-letter TCGA cancer type prefix derived from the sample barcode.",
    "Color Label": "Current metadata value used to color the linked embedding views.",
    "sample_count": "Number of assay rows currently linked to the same patient_id.",
    "sample_ids": "Semicolon-delimited sample barcodes linked to this patient in the current view.",
    "cancer_types": "Cancer type labels represented by the repeated assay rows.",
}

_WRAPPED_COLUMNS = [
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

_FORMAT_MAPPING = {
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

_FLAG_COLUMNS = [
    "os_event",
    "received_surgery",
    "received_chemotherapy",
    "received_radiation",
    "received_hormone_therapy",
    "received_immunotherapy",
    "subtype_available",
]

_COLOR_FIELD_CANDIDATES = [
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


for _column in _FLAG_COLUMNS:
    _FORMAT_MAPPING[_column] = lambda value, _formatter=None: format_flag(value)


def resolve_existing_path(*candidates: str | Path) -> Path:
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return path
    joined = ", ".join(str(Path(candidate)) for candidate in candidates)
    raise FileNotFoundError(f"None of the candidate paths exist: {joined}")


def patient_id_from_sample_id(sample_id: str) -> str | None:
    parts = str(sample_id).split("-")
    if len(parts) >= 4 and parts[1] == "TCGA":
        return "-".join(parts[1:4])
    if len(parts) >= 3 and parts[0] == "TCGA":
        return "-".join(parts[:3])
    return None


def cancer_type_from_sample_id(sample_id: str) -> str:
    return str(sample_id)[:4]


def summarize_cancer_types(cancer_types) -> str:
    unique_types = sorted({str(value) for value in cancer_types if pd.notna(value)})
    if len(unique_types) <= 6:
        return ", ".join(unique_types)
    return f"{', '.join(unique_types[:6])} + {len(unique_types) - 6} more"


def format_flag(value):
    if pd.isna(value):
        return None
    normalized = str(value).strip().lower()
    if normalized in {"true", "1", "yes"}:
        return "Yes"
    if normalized in {"false", "0", "no"}:
        return "No"
    return value


def load_clinical_metadata(path: str | Path = CLINICAL_METADATA_PATH) -> pd.DataFrame:
    return pd.read_csv(path)


def load_metadata_tooltips(path: str | Path = METADATA_DICTIONARY_PATH) -> dict[str, str]:
    return (
        pd.read_csv(path)
        .dropna(subset=["description"])
        .drop_duplicates(subset=["column"])
        .set_index("column")["description"]
        .to_dict()
    )


def load_cancer_color_map(path: str | Path = CANCER_COLOR_PATH) -> dict[str, str]:
    json_path = Path(path)
    if not json_path.exists():
        return {}
    return json.loads(json_path.read_text())


def distinct_palette(n: int) -> list[str]:
    base = px.colors.qualitative.Alphabet
    if n <= len(base):
        return base[:n]
    return [base[index % len(base)] for index in range(n)]


def get_feature_columns(df: pd.DataFrame) -> list[str]:
    pattern = re.compile(r"^(NMF|PC)(\d+)$")
    feature_columns = [column for column in df.columns if pattern.match(str(column))]
    return sorted(
        feature_columns,
        key=lambda column: (
            pattern.match(str(column)).group(1),
            int(pattern.match(str(column)).group(2)),
        ),
    )


def load_embedding_sample_frame(path: str | Path) -> pd.DataFrame:
    df = pd.read_parquet(path).copy()
    if "sample" not in df.columns:
        raise ValueError(f"Expected a 'sample' column in {path}")
    df = df.rename(columns={"sample": "Sample ID"})
    df["patient_id"] = df["Sample ID"].map(patient_id_from_sample_id)
    df["Cancer Type"] = df["Sample ID"].map(cancer_type_from_sample_id)
    return df


def align_embedding_frames(*embedding_dfs: pd.DataFrame) -> tuple[pd.DataFrame, ...]:
    if not embedding_dfs:
        return tuple()

    common_sample_ids = set(embedding_dfs[0]["Sample ID"])
    for embedding_df in embedding_dfs[1:]:
        common_sample_ids &= set(embedding_df["Sample ID"])

    ordered_sample_ids = [
        sample_id for sample_id in embedding_dfs[0]["Sample ID"] if sample_id in common_sample_ids
    ]

    aligned_frames = []
    for embedding_df in embedding_dfs:
        aligned_frames.append(
            embedding_df.set_index("Sample ID").loc[ordered_sample_ids].reset_index()
        )
    return tuple(aligned_frames)


def default_axis_fields(feature_columns: list[str]) -> tuple[str, str]:
    if not feature_columns:
        raise ValueError("No feature columns found for the selected embedding")
    if len(feature_columns) == 1:
        return feature_columns[0], feature_columns[0]
    return feature_columns[0], feature_columns[1]


def available_color_fields(clinical_df: pd.DataFrame) -> list[str]:
    return [
        field for field in _COLOR_FIELD_CANDIDATES if field == "Cancer Type" or field in clinical_df.columns
    ]


def _build_label_colors(
    display_df: pd.DataFrame,
    color_by: str,
    cancer_color_map: dict[str, str] | None = None,
) -> dict[str, str]:
    cancer_color_map = cancer_color_map or {}
    categories = sorted(display_df["Color Label"].astype(str).unique())

    if color_by == "Cancer Type":
        auto_palette = distinct_palette(len(categories))
        colors = {
            category: cancer_color_map.get(category, auto_palette[index])
            for index, category in enumerate(categories)
        }
    elif color_by == "cancer_type_full":
        color_lookup = (
            display_df[["Color Label", "Cancer Type"]]
            .dropna(subset=["Color Label", "Cancer Type"])
            .drop_duplicates(subset=["Color Label"])
            .set_index("Color Label")["Cancer Type"]
            .to_dict()
        )
        auto_palette = distinct_palette(len(categories))
        colors = {
            category: cancer_color_map.get(color_lookup.get(category), auto_palette[index])
            for index, category in enumerate(categories)
        }
    else:
        auto_palette = distinct_palette(len(categories))
        colors = {category: auto_palette[index] for index, category in enumerate(categories)}

    if "Unknown" in colors:
        colors["Unknown"] = "#9CA3AF"
    return colors


def prepare_embedding_for_display(
    embedding_df: pd.DataFrame,
    clinical_df: pd.DataFrame,
    color_by: str,
    cancer_color_map: dict[str, str] | None = None,
) -> tuple[pd.DataFrame, dict[str, str]]:
    display_df = embedding_df.merge(
        clinical_df,
        on="patient_id",
        how="left",
        suffixes=("", "_metadata"),
    )

    if "cancer_type" in display_df.columns:
        resolved_cancer_type = (
            display_df["cancer_type"]
            .fillna(display_df.get("Cancer Type"))
            .fillna("Unknown")
            .astype(str)
        )
        display_df["Cancer Type"] = resolved_cancer_type
    elif "Cancer Type" in display_df.columns:
        display_df["Cancer Type"] = display_df["Cancer Type"].fillna("Unknown").astype(str)
    else:
        display_df["Cancer Type"] = "Unknown"

    if color_by == "Cancer Type":
        color_values = display_df["Cancer Type"]
    else:
        if color_by not in display_df.columns:
            raise ValueError(f"Unknown metadata color field: {color_by}")
        color_values = display_df[color_by]

    if color_by in _FLAG_COLUMNS:
        color_values = color_values.map(format_flag)

    display_df["Color Label"] = color_values.fillna("Unknown").astype(str)
    label_colors = _build_label_colors(display_df, color_by, cancer_color_map)
    return display_df, label_colors


def sample_ids_from_indices(embedding_df: pd.DataFrame, selected_indices: list[int]) -> list[str]:
    sample_ids = embedding_df["Sample ID"].tolist()
    return [sample_ids[index] for index in selected_indices if 0 <= index < len(sample_ids)]


def sample_ids_to_indices(embedding_df: pd.DataFrame, selected_sample_ids: list[str]) -> list[int]:
    if not selected_sample_ids:
        return []
    index_lookup = {
        sample_id: index for index, sample_id in enumerate(embedding_df["Sample ID"].tolist())
    }
    return [index_lookup[sample_id] for sample_id in selected_sample_ids if sample_id in index_lookup]


def subset_by_sample_ids(
    embedding_df: pd.DataFrame,
    selected_sample_ids: list[str] | None,
) -> pd.DataFrame:
    if not selected_sample_ids:
        return embedding_df.copy()
    sample_id_set = set(selected_sample_ids)
    return embedding_df[embedding_df["Sample ID"].isin(sample_id_set)].copy().reset_index(drop=True)


def create_embedding_scatter(
    embedding_df: pd.DataFrame,
    x_feature: str,
    y_feature: str,
    embedding_label: str,
    color_by: str,
    label_colors: dict[str, str],
):
    plot_df = embedding_df[
        ["Sample ID", "Cancer Type", "Color Label", x_feature, y_feature]
    ].copy()
    scatter_plot = jscatter.Scatter(
        data=plot_df,
        x=x_feature,
        y=y_feature,
        color_by="Color Label",
        color_map=label_colors,
        height=520,
        width=520,
        lasso_callback=True,
        selection_mode="lasso",
    )
    scatter_plot.tooltip(
        enable=True,
        properties=["Sample ID", "Cancer Type", "Color Label", x_feature, y_feature],
    )
    scatter_plot.size(default=5)
    scatter_plot.options(
        {
            "aspectRatio": 1.0,
            "regl_scatterplot_options": {
                "showLegend": True,
                "xAxis": {"showGrid": True, "title": x_feature},
                "yAxis": {"showGrid": True, "title": y_feature},
                "title": f"{embedding_label} (colored by {color_by})",
            },
        }
    )
    return scatter_plot


def create_grandscatter_widget(
    embedding_df: pd.DataFrame,
    feature_columns: list[str],
    label_colors: dict[str, str],
):
    from grandscatter import Scatter

    if not feature_columns:
        raise ValueError("No feature columns available for grandscatter")

    plot_df = embedding_df[[*feature_columns, "Color Label"]].copy()
    plot_df["Color Label"] = plot_df["Color Label"].astype("category")
    return Scatter(
        plot_df,
        axis_fields=feature_columns,
        label_field="Color Label",
        label_colors=label_colors,
        base_point_size=6,
    )


def dominant_feature_metadata(
    embedding_df: pd.DataFrame,
    feature_columns: list[str],
) -> tuple[np.ndarray, list[str], np.ndarray]:
    if not feature_columns:
        raise ValueError("No feature columns available for dominant-feature metadata")

    feature_matrix = embedding_df[feature_columns].to_numpy(dtype=float)
    magnitude_matrix = np.abs(feature_matrix) if feature_columns[0].startswith("PC") else feature_matrix
    dominant_idx = np.argmax(magnitude_matrix, axis=1)
    dominant_values = magnitude_matrix[np.arange(len(embedding_df)), dominant_idx]
    dominant_labels = [feature_columns[index] for index in dominant_idx]
    return dominant_idx, dominant_labels, dominant_values


def bar_sort_order(mat: np.ndarray) -> np.ndarray:
    winners = np.argmax(mat, axis=1)
    order = []
    for comp in range(mat.shape[1]):
        idx = np.argsort(-mat[:, comp])
        order.extend(idx[winners[idx] == comp])
    return np.asarray(order, dtype=int)


def _canonical_cancer_code(value: str) -> str:
    label = str(value).strip()
    if not label or label == "Unknown":
        return "Unknown"

    alias_map = {
        "ACC": "ACCx",
        "GBM": "GBMx",
        "LGG": "LGGx",
        "OV": "OVxx",
        "UCS": "UCSx",
        "UVM": "UVMx",
    }
    if label in alias_map.values():
        return label
    return alias_map.get(label, label[:4])


def _load_group_lookup(path: str | Path) -> tuple[dict[str, str], dict[str, str]]:
    try:
        grouping_payload = json.loads(Path(path).read_text()).get("organ_system_groupings", [])
    except Exception:
        return {}, {}

    code_to_group: dict[str, str] = {}
    code_to_color: dict[str, str] = {}
    for group in grouping_payload:
        group_name = group["group_name"]
        group_color = group["color"]
        for cancer_code in group["cancer_codes"]:
            normalized_code = _canonical_cancer_code(cancer_code)
            code_to_group[cancer_code] = group_name
            code_to_group[normalized_code] = group_name
            code_to_color[cancer_code] = group_color
            code_to_color[normalized_code] = group_color
    return code_to_group, code_to_color


def _partitioned_sort(feature_matrix: np.ndarray, group_labels: list[str]) -> np.ndarray:
    final_order: list[int] = []
    comp_order = np.argsort(-feature_matrix.sum(axis=0))
    ordered_matrix = feature_matrix[:, comp_order]
    label_array = np.asarray(group_labels, dtype=object)

    for label in sorted({str(value) for value in label_array}):
        sub_indices = np.where(label_array == label)[0]
        if len(sub_indices) == 0:
            continue
        sub_order = bar_sort_order(ordered_matrix[sub_indices, :])
        final_order.extend(sub_indices[sub_order])

    return np.asarray(final_order, dtype=int)


def sort_embedding_samples(
    embedding_df: pd.DataFrame,
    feature_columns: list[str],
    sort_method: str,
) -> pd.DataFrame:
    if embedding_df.empty:
        return embedding_df.copy().reset_index(drop=True)

    feature_matrix = embedding_df[feature_columns].to_numpy(dtype=float)
    comp_order = np.argsort(-feature_matrix.sum(axis=0))
    ordered_matrix = feature_matrix[:, comp_order]

    if sort_method == "component":
        order = bar_sort_order(ordered_matrix)
        return embedding_df.iloc[order].reset_index(drop=True)

    if sort_method == "alphabetical":
        return embedding_df.sort_values(["Sample ID"]).reset_index(drop=True)

    if sort_method == "cancer_type":
        order = _partitioned_sort(
            feature_matrix,
            embedding_df["Cancer Type"].fillna("Unknown").astype(str).tolist(),
        )
        return embedding_df.iloc[order].reset_index(drop=True)

    if sort_method == "organ_system":
        code_to_group, _ = _load_group_lookup(ORGAN_SYSTEM_PATH)
        organ_systems = [
            code_to_group.get(_canonical_cancer_code(value), "Unknown")
            for value in embedding_df["Cancer Type"].fillna("Unknown").astype(str)
        ]
        order = _partitioned_sort(feature_matrix, organ_systems)
        return embedding_df.iloc[order].reset_index(drop=True)

    order = bar_sort_order(ordered_matrix)
    return embedding_df.iloc[order].reset_index(drop=True)


def _categorical_color_lookup(
    values: list[str],
    preferred_colors: dict[str, str] | None = None,
) -> dict[str, str]:
    preferred_colors = preferred_colors or {}
    unique_values = sorted({str(value) for value in values if pd.notna(value)})
    auto_palette = distinct_palette(len(unique_values))
    lookup = {
        value: preferred_colors.get(value, auto_palette[index])
        for index, value in enumerate(unique_values)
    }
    if "Unknown" in {str(value) for value in values}:
        lookup.setdefault("Unknown", "#9CA3AF")
    return lookup


def _color_to_hiplot(color: str) -> str:
    color = str(color).strip()
    if color.startswith(("rgb(", "rgba(", "hsl(", "hsla(")):
        return color.replace("rgba(", "rgb(").replace("hsla(", "hsl(")
    if color.startswith("#"):
        hex_color = color[1:]
        if len(hex_color) == 3:
            hex_color = "".join(channel * 2 for channel in hex_color)
        if len(hex_color) == 6:
            red = int(hex_color[0:2], 16)
            green = int(hex_color[2:4], 16)
            blue = int(hex_color[4:6], 16)
            return f"rgb({red}, {green}, {blue})"
    return color


def _categorical_colorscale(colors: list[str]) -> list[list[float | str]]:
    if not colors:
        return [[0.0, "#9CA3AF"], [1.0, "#9CA3AF"]]
    if len(colors) == 1:
        return [[0.0, colors[0]], [1.0, colors[0]]]
    return [[index / (len(colors) - 1), color] for index, color in enumerate(colors)]


def create_embedding_heatmap(
    embedding_df: pd.DataFrame,
    feature_columns: list[str],
    embedding_label: str,
    selected_sample_ids: list[str] | None,
    sort_method: str,
    cancer_color_map: dict[str, str] | None = None,
    active_color_field: str = "Cancer Type",
    active_label_colors: dict[str, str] | None = None,
) -> go.Figure:
    from plotly.subplots import make_subplots

    working_df = subset_by_sample_ids(embedding_df, selected_sample_ids)
    working_df = sort_embedding_samples(working_df, feature_columns, sort_method)
    if working_df.empty:
        return go.Figure()

    feature_matrix = working_df[feature_columns].to_numpy(dtype=float)
    n_samples, n_comps = feature_matrix.shape
    comp_order = np.argsort(-feature_matrix.sum(axis=0))
    ordered_matrix = feature_matrix[:, comp_order]

    sample_labels = working_df["Sample ID"].astype(str).tolist()
    cancer_types = working_df["Cancer Type"].fillna("Unknown").astype(str).tolist()
    cancer_codes = [_canonical_cancer_code(value) for value in cancer_types]
    x_positions = list(range(n_samples))

    component_colors_raw = load_cancer_color_map(COMPONENT_COLOR_PATH)
    auto_component_colors = distinct_palette(n_comps)
    component_colors = [
        component_colors_raw.get(f"Comp_{comp_idx}", auto_component_colors[position])
        for position, comp_idx in enumerate(comp_order)
    ]

    cancer_color_map = cancer_color_map or {}
    unique_cancer_types = sorted(set(cancer_types))
    auto_cancer_palette = distinct_palette(len(unique_cancer_types))
    cancer_colors: dict[str, str] = {}
    for index, cancer_type in enumerate(unique_cancer_types):
        cancer_colors[cancer_type] = (
            cancer_color_map.get(cancer_type)
            or cancer_color_map.get(_canonical_cancer_code(cancer_type))
            or auto_cancer_palette[index]
        )

    organ_lookup, organ_colors_lookup = _load_group_lookup(ORGAN_SYSTEM_PATH)
    embry_lookup, embry_colors_lookup = _load_group_lookup(EMBRYONIC_LAYER_PATH)
    organ_systems = [organ_lookup.get(code, "Unknown") for code in cancer_codes]
    organ_system_colors = [organ_colors_lookup.get(code, "#CCCCCC") for code in cancer_codes]
    embryonic_layers = [embry_lookup.get(code, "Unknown") for code in cancer_codes]
    embryonic_layer_colors = [embry_colors_lookup.get(code, "#CCCCCC") for code in cancer_codes]

    fig = make_subplots(
        rows=5,
        cols=1,
        shared_xaxes=True,
        row_heights=[0.72, 0.07, 0.07, 0.07, 0.07],
        vertical_spacing=0.03,
        subplot_titles=(
            "NMF Component Activities",
            "Dominant Component",
            "Cancer Type",
            "Organ System",
            "Embryonic Layer",
        ),
    )

    fig.add_trace(
        go.Heatmap(
            z=ordered_matrix.T,
            x=x_positions,
            colorscale="Turbo",
            colorbar=dict(title="Activity", x=1.02),
            showscale=False,
            customdata=np.array([sample_labels] * n_comps),
            hovertemplate="Sample: %{customdata}<br>Component: %{y}<br>Activity: %{z}<extra></extra>",
        ),
        row=1,
        col=1,
    )

    winning_comp_indices = np.argmax(ordered_matrix, axis=1)
    winning_comp_numbers = np.array([comp_order[index] for index in winning_comp_indices])
    if n_comps == 1:
        component_scale = [(0.0, component_colors[0]), (1.0, component_colors[0])]
    else:
        component_scale = [(0.0, component_colors[0])]
        for index in range(1, n_comps):
            component_scale.append(((index - 0.5) / (n_comps - 1), component_colors[index - 1]))
            component_scale.append((index / (n_comps - 1), component_colors[index]))
        component_scale.append((1.0, component_colors[-1]))

    fig.add_trace(
        go.Heatmap(
            z=[winning_comp_indices],
            x=x_positions,
            colorscale=component_scale,
            showscale=False,
            customdata=[winning_comp_numbers],
            text=[sample_labels],
            hovertemplate="Sample: %{text}<br>Dominant Component: Comp %{customdata}<extra></extra>",
        ),
        row=2,
        col=1,
    )

    cancer_to_index = {cancer_type: index for index, cancer_type in enumerate(unique_cancer_types)}
    cancer_strip_values = [cancer_to_index[cancer_type] for cancer_type in cancer_types]
    if len(unique_cancer_types) == 1:
        cancer_scale = [
            (0.0, cancer_colors[unique_cancer_types[0]]),
            (1.0, cancer_colors[unique_cancer_types[0]]),
        ]
    else:
        cancer_scale = [
            (index / (len(unique_cancer_types) - 1), cancer_colors[cancer_type])
            for index, cancer_type in enumerate(unique_cancer_types)
        ]

    fig.add_trace(
        go.Heatmap(
            z=[cancer_strip_values],
            x=x_positions,
            colorscale=cancer_scale,
            showscale=False,
            customdata=[cancer_types],
            text=[sample_labels],
            hovertemplate="Sample: %{text}<br>Cancer Type: %{customdata}<extra></extra>",
        ),
        row=3,
        col=1,
    )

    for row_index, label, values, colors in [
        (4, "Organ System", organ_systems, organ_system_colors),
        (5, "Embryonic Layer", embryonic_layers, embryonic_layer_colors),
    ]:
        unique_values = sorted(set(values))
        value_to_index = {value: index for index, value in enumerate(unique_values)}
        unique_colors = {}
        for value, color in zip(values, colors):
            unique_colors.setdefault(value, color)

        if len(unique_values) == 1:
            strip_scale = [
                (0.0, unique_colors[unique_values[0]]),
                (1.0, unique_colors[unique_values[0]]),
            ]
        else:
            strip_scale = [
                (index / (len(unique_values) - 1), unique_colors[value])
                for index, value in enumerate(unique_values)
            ]

        fig.add_trace(
            go.Heatmap(
                z=[[value_to_index[value] for value in values]],
                x=x_positions,
                colorscale=strip_scale,
                showscale=False,
                customdata=[values],
                text=[sample_labels],
                hovertemplate=f"Sample: %{{text}}<br>{label}: %{{customdata}}<extra></extra>",
            ),
            row=row_index,
            col=1,
        )

    fig.update_yaxes(
        tickmode="array",
        tickvals=list(range(n_comps)),
        ticktext=[f"Comp {comp_idx}" for comp_idx in comp_order],
        autorange="reversed",
        row=1,
        col=1,
    )

    for row_index in range(1, 5):
        fig.update_xaxes(showticklabels=False, row=row_index, col=1)

    tick_step = max(n_samples // 40, 1)
    tick_positions = x_positions[::tick_step]
    tick_labels = cancer_types[::tick_step]
    fig.update_xaxes(
        tickmode="array",
        tickvals=tick_positions,
        ticktext=tick_labels,
        tickangle=90,
        title_text="Samples",
        row=5,
        col=1,
    )

    for row_index in range(2, 6):
        fig.update_yaxes(showticklabels=False, row=row_index, col=1)

    fig.update_layout(
        height=max(980, n_comps * 34 + 320),
        margin=dict(l=90, r=80, t=80, b=110),
    )

    return fig


def default_visible_features(
    feature_columns: list[str],
    limit: int = 10,
) -> list[str]:
    return feature_columns[: min(limit, len(feature_columns))]


def coerce_visible_features(
    feature_columns: list[str],
    selected_features: list[str] | None,
    limit: int = 10,
) -> list[str]:
    if not selected_features:
        return default_visible_features(feature_columns, limit=limit)

    feature_set = set(feature_columns)
    ordered = [feature for feature in selected_features if feature in feature_set]
    return ordered or default_visible_features(feature_columns, limit=limit)


def create_hiplot_iframe_html(
    embedding_df: pd.DataFrame,
    visible_columns: list[str],
    selected_sample_ids: list[str] | None,
    height: int = 740,
    colorby_column: str = "Color Label",
    label_colors: dict[str, str] | None = None,
    cancer_color_map: dict[str, str] | None = None,
    selection_message_type: str = "itcr-hiplot-selection",
) -> str:
    import hiplot as hip

    working_df = subset_by_sample_ids(embedding_df, selected_sample_ids)
    working_df = working_df.copy()
    working_df["Sample / Cancer Type"] = (
        working_df["Sample ID"].astype(str)
        + " | "
        + working_df["Cancer Type"].fillna("Unknown").astype(str)
    )

    all_plot_columns = [
        "Sample ID",
        "Sample / Cancer Type",
        "patient_id",
        "Cancer Type",
        "Color Label",
        "tissue_or_organ_of_origin",
        "primary_diagnosis",
        "molecular_subtype",
        *get_feature_columns(working_df),
    ]
    available_columns = [column for column in all_plot_columns if column in working_df.columns]
    plot_df = working_df[available_columns].copy()
    plot_df.insert(0, "uid", working_df["Sample ID"].astype(str))

    records = plot_df.where(pd.notna(plot_df), None).to_dict(orient="records")
    experiment = hip.Experiment.from_iterable(records)
    experiment.enabledDisplays = [hip.Displays.PARALLEL_PLOT]

    ordered_visible_columns = [
        "Cancer Type",
        *[column for column in visible_columns if column != "Cancer Type"],
    ]
    ordered_visible_columns = [
        column for column in ordered_visible_columns if column in plot_df.columns
    ]
    hidden_columns = [
        column for column in plot_df.columns if column not in ordered_visible_columns
    ]
    experiment.display_data(hip.Displays.PARALLEL_PLOT).update(
        {
            "order": ordered_visible_columns,
            "hide": hidden_columns,
        }
    )

    if colorby_column in plot_df.columns:
        experiment.colorby = colorby_column
    elif "Color Label" in plot_df.columns:
        experiment.colorby = "Color Label"
    elif "Cancer Type" in plot_df.columns:
        experiment.colorby = "Cancer Type"

    if "Color Label" in plot_df.columns and label_colors:
        experiment.parameters_definition["Color Label"] = hip.ValueDef(
            value_type=hip.ValueType.CATEGORICAL,
            colors={
                label: _color_to_hiplot(color)
                for label, color in label_colors.items()
            },
        )
    if "Cancer Type" in plot_df.columns:
        cancer_lookup = _categorical_color_lookup(
            plot_df["Cancer Type"].fillna("Unknown").astype(str).tolist(),
            preferred_colors=cancer_color_map,
        )
        experiment.parameters_definition["Cancer Type"] = hip.ValueDef(
            value_type=hip.ValueType.CATEGORICAL,
            colors={
                label: _color_to_hiplot(color)
                for label, color in cancer_lookup.items()
            },
        )
    if colorby_column in experiment.parameters_definition:
        experiment.parameters_definition[colorby_column].type = hip.ValueType.CATEGORICAL
    experiment.parameters_definition["Sample ID"].label_html = "Sample ID"
    experiment.parameters_definition["Sample / Cancer Type"].label_html = "Sample | Cancer Type"

    hiplot_html = experiment.to_html()
    selection_bridge_script = f"""/*ON_LOAD_SCRIPT_INJECT*/
        function sendSelection(type, data) {{
            window.parent.postMessage({{
                type: {json.dumps(selection_message_type)},
                eventType: type,
                selected_uids: Array.isArray(data) ? data : [],
            }}, "*");
        }}
        Object.assign(options, {{
            onChange: {{
                selected_uids: sendSelection,
            }},
        }});
    """
    hiplot_html = hiplot_html.replace("/*ON_LOAD_SCRIPT_INJECT*/", selection_bridge_script)
    return (
        '<iframe '
        'style="width: 100%; border: 1px solid #d1d5db; border-radius: 10px; '
        f'height: {height}px; background: white;" '
        'sandbox="allow-scripts allow-same-origin" '
        f'srcdoc="{html.escape(hiplot_html, quote=True)}"></iframe>'
    )


def build_metadata_views(
    display_df: pd.DataFrame,
    selected_sample_ids: list[str] | None,
):
    assay_df = subset_by_sample_ids(display_df, selected_sample_ids)
    is_filtered = bool(selected_sample_ids)

    assay_df = assay_df.reset_index().rename(columns={"index": "selection_index"})

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

    matched_column = "case_uuid" if "case_uuid" in assay_df.columns else None
    matched_sample_count = int(assay_df[matched_column].notna().sum()) if matched_column else int(len(assay_df))
    summary = {
        "is_filtered": is_filtered,
        "sample_count": int(len(assay_df)),
        "unique_patient_count": int(assay_df["patient_id"].nunique(dropna=True)),
        "matched_sample_count": matched_sample_count,
        "duplicate_patient_count": int(len(duplicate_patients)),
        "cancer_type_count": int(assay_df["Cancer Type"].nunique(dropna=True)),
        "cancer_types_label": summarize_cancer_types(assay_df["Cancer Type"]),
    }
    return assay_df, duplicate_patients, summary


def metadata_presentation() -> tuple[dict[str, list[str]], dict[str, str], list[str], dict[str, object]]:
    return _METADATA_GROUPS, _BASE_TOOLTIPS, _WRAPPED_COLUMNS, _FORMAT_MAPPING
