import json
import glob
import re
from pathlib import Path
from typing import Final, List, Tuple, Dict

import numpy as np
import pandas as pd

from nmf_vis.sort_utils import get_sample_order
from nmf_vis.color_utils import load_cancer_colors, component_palette


cache: Final[dict[Path, pd.DataFrame]] = {}


def load_cfg(path: str | Path = "config.json") -> dict:
    return json.load(open(path, "r"))


def _get_dataframe(filepath: Path) -> pd.DataFrame:
    if filepath not in cache:
        cache[filepath] = pd.read_csv(filepath)
    return cache[filepath]


def _component_index(column_name: str) -> int | None:
    """Extract numeric component id from names like Comp_14 / comp14 / Component 14."""
    match = re.match(r"(?i)^comp(?:onent)?[_\s-]*(\d+)$", column_name.strip())
    if not match:
        return None
    return int(match.group(1))


def _extract_component_columns(
    df: pd.DataFrame, sample_id_column: str = "sample_id"
) -> list[str]:
    """Return component columns, preferring explicit component-like names."""
    component_like = [
        c for c in df.columns if c != sample_id_column and _component_index(c) is not None
    ]
    if component_like:
        return component_like

    # Fallback for datasets without explicit component naming.
    return [
        c
        for c in df.columns
        if c != sample_id_column and pd.api.types.is_numeric_dtype(df[c])
    ]


def _canonicalize_component_columns(
    component_columns: list[str],
) -> tuple[list[str], np.ndarray | None]:
    """Sort by numeric component id when possible; return reorder index for raw -> sorted."""
    indexed = [(_component_index(col), col, i) for i, col in enumerate(component_columns)]
    component_ids = [idx for idx, _, _ in indexed]

    if any(idx is None for idx in component_ids):
        return component_columns, None
    if len(set(component_ids)) != len(component_ids):
        return component_columns, None

    indexed_non_null = [(int(idx), col, i) for idx, col, i in indexed]
    sorted_indexed = sorted(indexed_non_null, key=lambda x: x[0])
    sorted_columns = [col for _, col, _ in sorted_indexed]
    reorder = np.asarray([i for _, _, i in sorted_indexed], dtype=int)
    return sorted_columns, reorder


def _get_prepared_data(
    filepath: Path,
    sample_id_column: str = "sample_id",
    selection: list[int] | None = None,
    npy_path: Path | None = None,
) -> Tuple[np.ndarray, List[str], List[str]]:
    """
    Get H matrix, sample IDs, and cancer types, ready for visualization.
    
    If npy_path is provided, load H from the npy file and sample IDs from filepath CSV.
    Otherwise, load everything from the CSV filepath.
    """

    # Load sample IDs and metadata from CSV
    df = _get_dataframe(filepath)

    if selection is not None:
        df = df.iloc[selection]

    sample_ids = df[sample_id_column].tolist()
    
    component_columns = _extract_component_columns(df, sample_id_column)
    sorted_component_columns, reorder = _canonicalize_component_columns(component_columns)

    # Load H matrix either from npy or from CSV
    if npy_path is not None:
        H = np.load(npy_path)
        if selection is not None:
            H = H[selection]
        if len(component_columns) == H.shape[1] and reorder is not None:
            H = H[:, reorder]
    else:
        if not component_columns:
            raise ValueError(f"No numeric component columns found in {filepath}")

        H = df[sorted_component_columns].values

    cancer_types = [i[:4] for i in sample_ids]

    return H, sample_ids, cancer_types


def _load_component_colors(path, n_components, component_order):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            f"Comp_{i}": color
            for i, color in zip(component_order, component_palette(n_components))
        }


def prepare_grandscatter_data(
    cfg_path: str | Path = "conf/config.json",
    selection: list[int] | None = None,
) -> tuple[pd.DataFrame, list[str], dict[str, str]]:
    """Build a DataFrame suitable for ``grandscatter.Scatter``.

    Returns
    -------
    df : pd.DataFrame
        One row per sample. Columns are component fields aligned to the source
        metadata names (numerically canonicalized when parseable) plus
        ``cancer_type`` (categorical label).
    axis_fields : list[str]
        The 16 component column names to use as projection axes.
    label_colors : dict[str, str]
        Mapping from cancer-type code to hex colour.
    """
    cfg = load_cfg(cfg_path)

    csv_path = Path(
        cfg.get("DEFAULT_CSV_FILENAME", "data/all_H_component_contributions_k16.csv")
    )
    npy_path = Path(
        cfg.get("NPY_PROPORTIONS_FILENAME", "data/tcga_bulk_k16_H_proportions.npy")
    )

    # -- load H proportions and sample metadata --------------------------
    meta_df = _get_dataframe(csv_path)
    H_prop = np.load(npy_path)

    if selection is not None:
        meta_df = meta_df.iloc[selection].reset_index(drop=True)
        H_prop = H_prop[selection]

    component_columns = _extract_component_columns(meta_df, sample_id_column="sample_id")
    if not component_columns:
        raise ValueError(
            f"No component columns found in metadata CSV: {csv_path}"
        )
    if len(component_columns) != H_prop.shape[1]:
        raise ValueError(
            "Component count mismatch between metadata CSV and NPY matrix: "
            f"{len(component_columns)} columns vs {H_prop.shape[1]} matrix components"
        )

    axis_fields, reorder = _canonicalize_component_columns(component_columns)
    if reorder is not None:
        H_prop = H_prop[:, reorder]

    # Use raw proportions. Do NOT center the data.
    # Centering (subtracting mean) shifts the origin, which makes the
    # component axes point in directions relative to the "average sample"
    # rather than "pure component". For NMF, users expect axes to radiate
    # from zero abundance.
    H_centered = H_prop.astype(np.float32)

    df = pd.DataFrame(H_centered, columns=axis_fields)
    df["cancer_type"] = [sid[:4] for sid in meta_df["sample_id"]]

    # -- colours ---------------------------------------------------------
    cancer_color_map = load_cancer_colors(
        cfg.get("JSON_FILENAME_CANCER_TYPE_COLORS")
    )
    uniq = sorted(df["cancer_type"].unique())
    from nmf_vis.color_utils import distinct_palette

    auto = distinct_palette(len(uniq))
    label_colors = {
        ct: cancer_color_map.get(ct, auto[i]) for i, ct in enumerate(uniq)
    }

    return df, axis_fields, label_colors


def load_all_data(cfg_path, sort_method):
    """Loads and prepares all data needed for the visualization."""
    cfg = load_cfg(cfg_path)
    H, sample_ids, cancer_types = _get_prepared_data(
        Path(cfg.get("DEFAULT_CSV_FILENAME", "data/all_H_component_contributions.csv"))
    )
    n_samples, n_components = H.shape

    component_order = np.argsort(-H.sum(axis=0))
    H_ord = H[:, component_order]

    sample_order = get_sample_order(sort_method, H, sample_ids, cancer_types, cfg_path)

    H_sorted = H_ord[sample_order]
    x_labels_short = np.array(
        [label[:4] for label in np.array(sample_ids)[sample_order]]
    )

    component_colors = _load_component_colors(
        cfg.get("JSON_FILENAME_COMPONENT_COLORS", "nmf_component_color_map.json"),
        n_components,
        component_order,
    )
    cancer_color_map = load_cancer_colors(cfg.get("JSON_FILENAME_CANCER_TYPE_COLORS"))

    umap_df = pd.read_parquet(cfg.get("UMAP_FILENAME"))

    # These would be loaded similarly from the other JSON files
    organ_systems = []
    organ_system_colors = {}
    embryonic_layers = []
    embryonic_layer_colors = {}

    return (
        H,
        sample_ids,
        cancer_types,
        component_colors,
        cancer_color_map,
        organ_systems,
        organ_system_colors,
        embryonic_layers,
        embryonic_layer_colors,
        H_sorted,
        x_labels_short,
        component_order,
        umap_df,
    )
