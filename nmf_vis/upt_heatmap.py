from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from nmf_vis.color_utils import distinct_palette, load_cancer_colors
from nmf_vis.data_utils import _get_prepared_data, resolve_analysis_cfg
from nmf_vis.heatmap import (
    _add_component_strip,
    _add_proportional_bar_chart,
    _load_component_colors,
    create_grandscatter_widget,
    get_grandscatter_initial_projection,
)
from nmf_vis.sort_utils import bar_sort_order, get_alphabetical_sort, get_cancer_type_sort


def _patient_id_from_sample_id(sample_id: str) -> str | None:
    parts = str(sample_id).split("-")
    if "TCGA" in parts:
        idx = parts.index("TCGA")
        if idx + 2 < len(parts):
            return "-".join(parts[idx : idx + 3])
    if len(parts) >= 4 and parts[1] == "TCGA":
        return "-".join(parts[1:4])
    if len(parts) >= 3 and parts[0] == "TCGA":
        return "-".join(parts[:3])
    return None


def _load_strip_metadata(cfg: dict) -> pd.DataFrame:
    metadata_path = Path(cfg["STRIP_METADATA_FILENAME"])
    metadata_df = pd.read_csv(metadata_path)
    id_column = cfg.get("STRIP_METADATA_ID_COLUMN", "submitter_id")
    return metadata_df.drop_duplicates(subset=[id_column]).copy()


def _unique_sorted_unknown_last(values: list[str]) -> list[str]:
    unique_values = sorted({str(value) for value in values})
    if "Unknown" in unique_values:
        unique_values = [value for value in unique_values if value != "Unknown"] + [
            "Unknown"
        ]
    return unique_values


def _palette_map(values: list[str], palette: list[str], unknown_color: str) -> dict[str, str]:
    unique_values = _unique_sorted_unknown_last(values)
    if not unique_values:
        return {}

    color_map: dict[str, str] = {}
    palette_size = max(1, len(palette))
    for index, value in enumerate(unique_values):
        if value == "Unknown":
            color_map[value] = unknown_color
        else:
            color_map[value] = palette[index % palette_size]
    return color_map


def _cohort_color_map(values: list[str], cancer_color_map: dict[str, str], unknown_color: str) -> dict[str, str]:
    unique_values = _unique_sorted_unknown_last(values)
    fallback_palette = distinct_palette(max(1, len(unique_values)))

    color_map: dict[str, str] = {}
    fallback_index = 0
    for value in unique_values:
        if value == "Unknown":
            color_map[value] = unknown_color
            continue

        preferred_keys = [value, f"{value}x", f"{value}xx"]
        color = None
        for key in preferred_keys:
            color = cancer_color_map.get(key)
            if color is not None:
                break
        if color is None:
            for key, candidate in cancer_color_map.items():
                if key.startswith(value):
                    color = candidate
                    break

        if color is None:
            color = fallback_palette[fallback_index % len(fallback_palette)]
            fallback_index += 1

        color_map[value] = color

    return color_map


def _resolve_strip_colors(
    strip_spec: dict,
    values: list[str],
    cancer_color_map: dict[str, str],
    unknown_color: str,
) -> tuple[list[str], dict[str, str]]:
    if strip_spec.get("palette_source") == "cancer_type_colors":
        color_map = _cohort_color_map(values, cancer_color_map, unknown_color)
    elif "color_map" in strip_spec:
        color_map = {str(key): str(value) for key, value in strip_spec["color_map"].items()}
        color_map.setdefault("Unknown", unknown_color)
    else:
        color_map = _palette_map(values, strip_spec.get("palette", []), unknown_color)

    return [color_map.get(value, unknown_color) for value in values], color_map


def _add_metadata_annotation_strip(
    fig: go.Figure,
    x_values: list[str] | np.ndarray,
    group_names: list[str],
    group_colors: list[str],
    label: str,
    submitter_ids: list[str],
    cohorts: list[str],
    winning_components: list[str],
    row: int,
    col: int,
) -> None:
    unique_groups = sorted(set(group_names))
    group_to_idx = {group: index for index, group in enumerate(unique_groups)}
    group_idx_arr = [group_to_idx[group] for group in group_names]

    unique_colors: dict[str, str] = {}
    for group_name, color in zip(group_names, group_colors):
        if group_name not in unique_colors:
            unique_colors[group_name] = color

    n_groups = len(unique_groups)
    if n_groups == 1:
        group_scale = [
            (0, unique_colors[unique_groups[0]]),
            (1, unique_colors[unique_groups[0]]),
        ]
    else:
        group_scale = [
            (index / (n_groups - 1), unique_colors[group])
            for index, group in enumerate(unique_groups)
        ]

    customdata = np.array(
        [[
            [group_name, submitter_id, cohort, winning_component]
            for group_name, submitter_id, cohort, winning_component in zip(
                group_names,
                submitter_ids,
                cohorts,
                winning_components,
            )
        ]],
        dtype=object,
    )

    fig.add_trace(
        go.Heatmap(
            x=x_values,
            z=[group_idx_arr],
            colorscale=group_scale,
            showscale=False,
            customdata=customdata,
            hovertemplate=(
                f"{label}: %{{customdata[0]}}"
                "<br>submitter_id: %{customdata[1]}"
                "<br>cohort: %{customdata[2]}"
                "<br>%{customdata[3]}<extra></extra>"
            ),
            showlegend=False,
        ),
        row=row,
        col=col,
    )


def _build_strip_values(sample_ids: list[str], cfg: dict) -> tuple[dict[str, list[str]], pd.DataFrame]:
    strip_specs = cfg.get("HEATMAP_STRIPS", [])
    metadata_df = _load_strip_metadata(cfg)
    id_column = cfg.get("STRIP_METADATA_ID_COLUMN", "submitter_id")

    strip_frame = pd.DataFrame(
        {
            "sample_id": sample_ids,
            "patient_id": [_patient_id_from_sample_id(sample_id) for sample_id in sample_ids],
        }
    )
    merged = strip_frame.merge(
        metadata_df,
        left_on="patient_id",
        right_on=id_column,
        how="left",
    )

    values: dict[str, list[str]] = {}
    for strip_spec in strip_specs:
        column = strip_spec["column"]
        if column in merged.columns:
            column_values = merged[column].fillna("Unknown").astype(str).tolist()
        else:
            column_values = ["Unknown"] * len(sample_ids)
        values[column] = column_values
    return values, merged


def _metadata_group_sort(H: np.ndarray, group_values: list[str]) -> np.ndarray:
    final_order: list[int] = []
    comp_order = np.argsort(-H.sum(axis=0))
    H_ord = H[:, comp_order]
    values = np.asarray(group_values)

    for group in _unique_sorted_unknown_last(group_values):
        sub_indices = np.where(values == group)[0]
        if len(sub_indices) == 0:
            continue
        H_subset = H_ord[sub_indices, :]
        sub_order = bar_sort_order(H_subset)
        final_order.extend(sub_indices[sub_order])

    return np.asarray(final_order, dtype=int)


def _get_sample_order(
    sort_method: str,
    H: np.ndarray,
    sample_ids: list[str],
    cancer_types: list[str],
    strip_values: dict[str, list[str]],
) -> np.ndarray:
    comp_order = np.argsort(-H.sum(axis=0))
    H_ord = H[:, comp_order]

    if sort_method == "component":
        return bar_sort_order(H_ord)
    if sort_method == "alphabetical":
        return get_alphabetical_sort(sample_ids)
    if sort_method == "cancer_type":
        return get_cancer_type_sort(H, cancer_types)
    if sort_method == "organ_system":
        organ_system_values = strip_values.get("organ_system")
        if organ_system_values:
            return _metadata_group_sort(H, organ_system_values)
    return bar_sort_order(H_ord)


def _configure_updated_layout(
    fig: go.Figure,
    n_comps: int,
    n_samples: int,
    comp_order: np.ndarray,
    x_labels: np.ndarray,
    x_labels_short: np.ndarray,
    total_rows: int,
    n_strip_rows: int,
) -> None:
    fig.update_yaxes(
        tickmode="array",
        tickvals=list(range(n_comps)),
        ticktext=[f"Comp {i}" for i in comp_order],
        autorange="reversed",
        row=1,
        col=1,
    )

    for row in range(1, total_rows):
        fig.update_xaxes(showticklabels=False, row=row, col=1)

    fig.update_xaxes(
        tickmode="array",
        tickvals=x_labels.tolist(),
        ticktext=x_labels_short,
        tickangle=90,
        row=total_rows,
        col=1,
    )

    for row in range(2, total_rows + 1):
        fig.update_yaxes(showticklabels=False, row=row, col=1)

    fig.update_layout(
        height=max(980, n_comps * 25 + 70 * n_strip_rows + 260),
        width=1400,
        autosize=True,
        margin=dict(l=80, r=80, t=60, b=100),
        barmode="stack",
        hovermode="x unified",
        selectdirection="h",
        dragmode="select",
        showlegend=False,
    )


def create_heatmap_figure(
    cfg_path: str | Path = "conf/upt_pub_nmf_config.json",
    sort_method: str = "component",
    selected_sample_ids: list[int] | None = None,
    analysis_name: str | None = None,
) -> go.Figure:
    cfg = resolve_analysis_cfg(cfg_path, analysis_name)
    heatmap_csv = Path(
        cfg.get(
            "HEATMAP_CSV_FILENAME",
            cfg.get("DEFAULT_CSV_FILENAME", "data/all_H_component_contributions_k16.csv"),
        )
    )
    metadata_path = (
        Path(cfg["ANALYSIS_METADATA_FILENAME"])
        if cfg.get("ANALYSIS_METADATA_FILENAME")
        else None
    )

    if selected_sample_ids is None:
        H, sample_ids_from_file, cancer_types = _get_prepared_data(
            heatmap_csv,
            metadata_path=metadata_path,
            metadata_sample_id_column=cfg.get("ANALYSIS_METADATA_SAMPLE_ID_COLUMN", "sample_id"),
            cancer_type_column=cfg.get("ANALYSIS_CANCER_TYPE_COLUMN", "cancer_type"),
        )
    else:
        H, sample_ids_from_file, cancer_types = _get_prepared_data(
            heatmap_csv,
            selection=selected_sample_ids,
            metadata_path=metadata_path,
            metadata_sample_id_column=cfg.get("ANALYSIS_METADATA_SAMPLE_ID_COLUMN", "sample_id"),
            cancer_type_column=cfg.get("ANALYSIS_CANCER_TYPE_COLUMN", "cancer_type"),
        )

    n_samples, n_comps = H.shape
    comp_order = np.argsort(-H.sum(axis=0))
    H_ord = H[:, comp_order]

    strip_specs = cfg.get("HEATMAP_STRIPS", [])
    strip_values, merged_strip_metadata = _build_strip_values(sample_ids_from_file, cfg)
    sample_order = _get_sample_order(
        sort_method,
        H,
        sample_ids_from_file,
        cancer_types,
        strip_values,
    )

    H_sorted = H_ord[sample_order]
    x_labels = np.asarray(sample_ids_from_file)[sample_order]
    ordered_indices = list(sample_order)
    x_labels_short = np.asarray([cancer_types[index] for index in ordered_indices])

    component_color_file = cfg.get(
        "JSON_FILENAME_COMPONENT_COLORS", "conf/nmf_component_color_map.json"
    )
    comp_colors = _load_component_colors(component_color_file, n_comps, comp_order)
    submitter_id_column = cfg.get("STRIP_METADATA_ID_COLUMN", "submitter_id")
    submitter_ids = (
        merged_strip_metadata.get(submitter_id_column, merged_strip_metadata["patient_id"])
        .fillna(merged_strip_metadata["patient_id"])
        .fillna("Unknown")
        .astype(str)
        .tolist()
    )
    cohorts = (
        merged_strip_metadata.get("cohort", pd.Series(["Unknown"] * len(sample_ids_from_file)))
        .fillna("Unknown")
        .astype(str)
        .tolist()
    )
    winning_components = [f"Comp {index}" for index in np.argmax(H, axis=1).tolist()]

    cancer_color_map = load_cancer_colors(cfg.get("JSON_FILENAME_CANCER_TYPE_COLORS"))
    unknown_color = cfg.get("STRIP_UNKNOWN_COLOR", "#CCCCCC")

    subplot_titles = (
        "NMF Component Activities",
        "Proportional NMF Activity",
        "Dominant Component",
        *[strip_spec["label"] for strip_spec in strip_specs],
    )
    row_heights = [0.43, 0.18, 0.05, *([0.04] * len(strip_specs))]
    total_rows = len(row_heights)

    fig = make_subplots(
        rows=total_rows,
        cols=1,
        shared_xaxes=True,
        row_heights=row_heights,
        vertical_spacing=0.03,
        subplot_titles=subplot_titles,
    )

    fig.add_trace(
        go.Heatmap(
            x=x_labels,
            y=[f"Comp {index}" for index in comp_order],
            z=H_sorted.T,
            colorscale="Turbo",
            colorbar=dict(title="Activity", x=1.02),
            showscale=False,
            hovertemplate="Sample: %{x}<br>Component: %{y}<br>Activity: %{z}<extra></extra>",
        ),
        row=1,
        col=1,
    )

    _add_proportional_bar_chart(
        fig,
        H_sorted,
        comp_colors,
        comp_order,
        x_values=x_labels,
    )
    _add_component_strip(
        fig,
        H_ord,
        sample_order,
        comp_colors,
        n_comps,
        comp_order,
        x_values=x_labels,
    )

    for offset, strip_spec in enumerate(strip_specs, start=4):
        column = strip_spec["column"]
        ordered_values = [strip_values[column][index] for index in ordered_indices]
        ordered_colors, _ = _resolve_strip_colors(
            strip_spec,
            ordered_values,
            cancer_color_map,
            unknown_color,
        )
        ordered_submitter_ids = [submitter_ids[index] for index in ordered_indices]
        ordered_cohorts = [cohorts[index] for index in ordered_indices]
        ordered_winning_components = [winning_components[index] for index in ordered_indices]
        _add_metadata_annotation_strip(
            fig,
            x_labels,
            ordered_values,
            ordered_colors,
            strip_spec["label"],
            ordered_submitter_ids,
            ordered_cohorts,
            ordered_winning_components,
            row=offset,
            col=1,
        )

    _configure_updated_layout(
        fig,
        n_comps,
        n_samples,
        comp_order,
        x_labels,
        x_labels_short,
        total_rows,
        len(strip_specs),
    )

    return fig