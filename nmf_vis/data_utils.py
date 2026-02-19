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
    
    # Load H matrix either from npy or from CSV
    if npy_path is not None:
        H = np.load(npy_path)
        if selection is not None:
            H = H[selection]
    else:
        component_columns = [
            c
            for c in df.columns
            if c != sample_id_column and pd.api.types.is_numeric_dtype(df[c])
        ]

        if not component_columns:
            raise ValueError(f"No numeric component columns found in {filepath}")

        H = df[component_columns].values

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
        One row per sample. Columns: ``Comp_0`` … ``Comp_15`` (proportional
        NMF activity) plus ``cancer_type`` (categorical label).
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

    n_comps = H_prop.shape[1]
    axis_fields = [f"Comp_{i}" for i in range(n_comps)]

    # Center each component axis by subtracting its column mean.
    # Proportions sum to 1 per row, which creates a degenerate linear
    # dependency (the 16th singular value ≈ 0).  Centering removes that
    # artificial constraint so all 15 remaining axes are independent and
    # the grand-tour projection fills 3-D space correctly.
    H_centered = (H_prop - H_prop.mean(axis=0)).astype(np.float32)

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
