import marimo

__generated_with = "0.20.2"
app = marimo.App(width="full")


@app.cell
def _():
    import importlib
    import importlib.util
    import os
    import shutil
    import subprocess
    import sys
    import urllib.error
    import urllib.request
    from pathlib import Path

    default_base_url = (
        "https://raw.githubusercontent.com/vedatonuryilmaz/dev_NMF_marimo/mvp0313"
    )
    pub_base_url = os.environ.get("PUB_ITCR_PCA_BASE_URL", default_base_url).rstrip("/")

    required_packages = {
        "anywidget": "anywidget>=0.9.18",
        "numpy": "numpy>=2,<3",
        "pandas": "pandas>=2.2",
        "pyarrow": "pyarrow>=17",
        "plotly": "plotly>=6",
        "hiplot": "hiplot>=0.1.33",
    }

    def ensure_runtime_packages() -> None:
        missing_specs = [
            spec
            for module, spec in required_packages.items()
            if importlib.util.find_spec(module) is None
        ]
        if not missing_specs:
            return

        uv = shutil.which("uv")
        installers = []
        if uv is not None:
            installers.extend(
                [
                    [uv, "pip", "install", "--python", sys.executable, *missing_specs],
                    [
                        uv,
                        "pip",
                        "install",
                        "--python",
                        sys.executable,
                        "--system",
                        *missing_specs,
                    ],
                ]
            )
        installers.append([sys.executable, "-m", "pip", "install", *missing_specs])

        last_error = None
        for command in installers:
            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode == 0:
                importlib.invalidate_caches()
                return
            last_error = RuntimeError(
                "Failed to install publication runtime dependencies.\n"
                f"Command: {' '.join(command)}\n"
                f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
            )
        raise last_error

    def ensure_jscatter_stub() -> None:
        if importlib.util.find_spec("jscatter") is not None:
            return

        stub_path = Path("jscatter.py")
        if stub_path.exists():
            return

        stub_path.write_text(
            "class Scatter:\n"
            "    def __init__(self, *args, **kwargs):\n"
            "        raise RuntimeError(\n"
            "            'jscatter is not available in the Molab publication runtime. '\n"
            "            'This publication notebook does not use jscatter-backed views.'\n"
            "        )\n",
            encoding="utf-8",
        )

    def download_file(relative_path: str, required: bool = True) -> Path | None:
        destination = Path(relative_path)
        if destination.exists():
            return destination

        destination.parent.mkdir(parents=True, exist_ok=True)
        source_url = f"{pub_base_url}/{relative_path}"
        try:
            urllib.request.urlretrieve(source_url, destination.as_posix())
        except urllib.error.HTTPError:
            if required:
                raise
            return None
        return destination

    ensure_runtime_packages()
    ensure_jscatter_stub()

    module_files = [
        "nmf_vis/itcr_embedding_utils.py",
    ]
    asset_files = [
        "conf/cancer_type_color_map.json",
        "conf/upt_pub_nmf_config.json",
        "data/0302_corces_submitter_metadata_expanded_v2.csv",
        "data/unified_clinical_metadata_tcga_corces_unified_clinical_metadata_final.csv",
        "data/unified_clinical_metadata_data_dictionary_final.csv",
    ]

    for relative_path in [*module_files, *asset_files]:
        download_file(relative_path, required=True)

    package_init = Path("nmf_vis/__init__.py")
    if not package_init.exists():
        package_init.write_text("", encoding="utf-8")

    pca_result_specs = [
        ("Canonical PCA", "data/tcga.atac.pca.sample.pq"),
        ("CN-aware adjusted PCA", "data/adjusted.pca.sample.pq"),
        ("CN-aware confounded PCA", "data/confounded.pca.sample.pq"),
    ]
    pca_result_options = {}
    for label, relative_path in pca_result_specs:
        downloaded_path = download_file(relative_path, required=False)
        if downloaded_path is not None:
            pca_result_options[label] = str(downloaded_path)

    if not pca_result_options:
        raise FileNotFoundError(
            "No published PCA parquet files were available from the configured base URL: "
            f"{pub_base_url}"
        )

    return Path, pca_result_options, pub_base_url


@app.cell
def _():
    import anywidget
    import html
    import json
    import marimo as mo
    import pandas as pd
    import traitlets
    from importlib import import_module

    itcr_embedding_utils = import_module("nmf_vis.itcr_embedding_utils")

    from nmf_vis.itcr_embedding_utils import (
        available_color_fields,
        build_metadata_views,
        coerce_visible_features,
        default_visible_features,
        get_feature_columns,
        load_cancer_color_map,
        load_clinical_metadata,
        load_embedding_sample_frame,
        load_metadata_tooltips,
        metadata_presentation,
        prepare_embedding_for_display,
    )

    return (
        available_color_fields,
        build_metadata_views,
        coerce_visible_features,
        default_visible_features,
        get_feature_columns,
        anywidget,
        html,
        itcr_embedding_utils,
        json,
        load_cancer_color_map,
        load_clinical_metadata,
        load_embedding_sample_frame,
        load_metadata_tooltips,
        metadata_presentation,
        mo,
        pd,
        prepare_embedding_for_display,
        traitlets,
    )


@app.cell
def _(Path, json, pd):
    strip_cfg = json.loads(Path("conf/upt_pub_nmf_config.json").read_text())
    strip_specs = strip_cfg.get("HEATMAP_STRIPS", [])
    strip_label_to_column = {
        spec.get("label", spec["column"]): spec["column"] for spec in strip_specs
    }
    strip_spec_by_column = {spec["column"]: spec for spec in strip_specs}
    strip_id_column = strip_cfg.get("STRIP_METADATA_ID_COLUMN", "submitter_id")
    strip_metadata = (
        pd.read_csv(strip_cfg["STRIP_METADATA_FILENAME"])
        .drop_duplicates(subset=[strip_id_column])
        .rename(columns={strip_id_column: "patient_id"})
    )
    strip_unknown_color = strip_cfg.get("STRIP_UNKNOWN_COLOR", "#CCCCCC")
    return strip_label_to_column, strip_metadata, strip_spec_by_column, strip_unknown_color


@app.cell
def _(pd):
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

    def build_strip_color_lookup(
        values,
        selected_color_column,
        strip_spec_by_column,
        cancer_color_map,
        unknown_color,
    ):
        strip_spec = strip_spec_by_column.get(selected_color_column)
        if strip_spec is None:
            return {}

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

    return (build_strip_color_lookup,)


@app.cell
def _(html, itcr_embedding_utils, json, pd):
    selection_message_type = "pub-itcr-hiplot-selection"

    def create_published_hiplot_iframe_html(
        embedding_df: pd.DataFrame,
        visible_columns: list[str],
        selected_sample_ids: list[str] | None,
        height: int = 740,
        colorby_column: str = "Color Label",
        label_colors: dict[str, str] | None = None,
        cancer_color_map: dict[str, str] | None = None,
        selection_message_type_override: str = selection_message_type,
    ) -> str:
        import hiplot as hip

        working_df = itcr_embedding_utils.subset_by_sample_ids(
            embedding_df, selected_sample_ids
        )
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
            *itcr_embedding_utils.get_feature_columns(working_df),
        ]
        available_columns = [
            column for column in all_plot_columns if column in working_df.columns
        ]
        plot_df = working_df[available_columns].copy()
        plot_df.insert(0, "uid", working_df["Sample ID"].astype(str))

        records = plot_df.where(pd.notna(plot_df), None).to_dict(orient="records")
        experiment = hip.Experiment.from_iterable(records)
        experiment.enabledDisplays = [hip.Displays.PARALLEL_PLOT]

        left_to_right_axis_order = [
            "Cancer Type",
            *[column for column in visible_columns if column != "Cancer Type"],
        ]
        left_to_right_axis_order = [
            column for column in left_to_right_axis_order if column in plot_df.columns
        ]
        hidden_columns = [
            column for column in plot_df.columns if column not in left_to_right_axis_order
        ]
        # HiPlot renders the configured order from right to left in the plot area.
        hiplot_render_order = list(reversed(left_to_right_axis_order))
        experiment.display_data(hip.Displays.PARALLEL_PLOT).update(
            {
                "order": hiplot_render_order,
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
                    label: itcr_embedding_utils._color_to_hiplot(color)
                    for label, color in label_colors.items()
                },
            )
        if "Cancer Type" in plot_df.columns:
            cancer_lookup = itcr_embedding_utils._categorical_color_lookup(
                plot_df["Cancer Type"].fillna("Unknown").astype(str).tolist(),
                preferred_colors=cancer_color_map,
            )
            experiment.parameters_definition["Cancer Type"] = hip.ValueDef(
                value_type=hip.ValueType.CATEGORICAL,
                colors={
                    label: itcr_embedding_utils._color_to_hiplot(color)
                    for label, color in cancer_lookup.items()
                },
            )
        if colorby_column in experiment.parameters_definition:
            experiment.parameters_definition[colorby_column].type = hip.ValueType.CATEGORICAL
        experiment.parameters_definition["Sample ID"].label_html = "Sample ID"
        experiment.parameters_definition["Sample / Cancer Type"].label_html = (
            "Sample | Cancer Type"
        )

        hiplot_html = experiment.to_html()
        selection_bridge_script = f"""/*ON_LOAD_SCRIPT_INJECT*/
        const selectionMessageType = {json.dumps(selection_message_type_override)};
        const bridgeState = {{
            selected_uids: [],
            filtered_uids: [],
        }};
        const normalizeSelectionPayload = (...args) => {{
            for (const arg of args) {{
                if (Array.isArray(arg)) {{
                    return arg.map((value) => String(value));
                }}
            }}
            return [];
        }};
        const normalizeEventType = (fallback, ...args) => {{
            for (const arg of args) {{
                if (typeof arg === "string") {{
                    return arg;
                }}
            }}
            return fallback;
        }};
        const getController = () => {{
            const root = document.querySelector(".hip_thm--light, .hip_thm--dark");
            if (!root) {{
                return null;
            }}
            const fiberKey = Object.keys(root).find((key) =>
                key.startsWith("__reactFiber$")
            );
            return fiberKey ? root[fiberKey]?.return?.stateNode ?? null : null;
        }};
        const normalizeBridgeSampleIds = (sampleIds) => {{
            const controller = getController();
            const totalRowCount = controller?.state?.rows_all_unfiltered?.length ?? 0;
            if (totalRowCount > 0 && sampleIds.length >= totalRowCount) {{
                return [];
            }}
            return sampleIds;
        }};

        function publishSelection(fallback, ...args) {{
            const eventType = normalizeEventType(fallback, ...args);
            const sampleIds = normalizeBridgeSampleIds(
                normalizeSelectionPayload(...args)
            );
            if (eventType === "filtered_uids") {{
                bridgeState.filtered_uids = sampleIds;
            }} else {{
                bridgeState.selected_uids = sampleIds;
            }}
            window.parent.postMessage({{
                type: selectionMessageType,
                bridge_state: {{
                    selected_uids: [...bridgeState.selected_uids],
                    filtered_uids: [...bridgeState.filtered_uids],
                }},
            }}, "*");
        }}
        Object.assign(options, {{
            onChange: {{
                selected_uids: (...args) => publishSelection("selected_uids", ...args),
                filtered_uids: (...args) => publishSelection("filtered_uids", ...args),
            }},
        }});
    """
        toolbar_polish_script = """/*AFTER_SETUP_SCRIPT_INJECT*/
        (() => {
            const toolbarId = "molab-hiplot-toolbar";
            const stateChipId = "molab-hiplot-state-chip";
            const styleId = "molab-hiplot-style";
            const rootSelector = ".hip_thm--light, .hip_thm--dark";

            function ensureStyles() {
                if (document.getElementById(styleId)) {
                    return;
                }
                const style = document.createElement("style");
                style.id = styleId;
                style.textContent = `
                    body {
                        margin: 0;
                        background: linear-gradient(180deg, #f8fafc 0%, #eef2ff 100%);
                    }
                    #hiplot_element_id {
                        background: transparent;
                    }
                    ${rootSelector} .container-fluid {
                        padding: 14px 18px 0 18px;
                    }
                    ${rootSelector} .d-flex.flex-wrap {
                        align-items: center;
                        gap: 12px;
                    }
                    ${rootSelector} .d-flex.flex-wrap > img {
                        height: 30px;
                        width: auto;
                    }
                    ${rootSelector} .d-flex.flex-wrap > div:last-child {
                        margin-left: auto;
                        padding: 6px 12px;
                        border-radius: 999px;
                        background: rgba(37, 99, 235, 0.08);
                        color: #1d4ed8;
                        font-weight: 600;
                    }
                    ${rootSelector} .container-fluid._27zXkTqskweooVZri-rve2 {
                        padding-bottom: 6px;
                    }
                    #${toolbarId} {
                        display: flex;
                        flex-wrap: wrap;
                        align-items: center;
                        gap: 10px;
                        margin-right: 12px;
                    }
                    #${toolbarId} button {
                        appearance: none;
                        border: 1px solid #cbd5e1;
                        border-radius: 999px;
                        padding: 8px 14px;
                        background: #ffffff;
                        color: #0f172a;
                        box-shadow: 0 8px 20px rgba(15, 23, 42, 0.08);
                        font-size: 13px;
                        font-weight: 600;
                        line-height: 1;
                        transition:
                            background 120ms ease,
                            color 120ms ease,
                            border-color 120ms ease,
                            opacity 120ms ease;
                    }
                    #${toolbarId} button:hover:not(:disabled) {
                        border-color: #0f172a;
                        background: #f8fafc;
                    }
                    #${toolbarId} button[data-variant="primary"] {
                        background: #0f172a;
                        border-color: #0f172a;
                        color: #ffffff;
                    }
                    #${toolbarId} button[data-variant="primary"]:hover:not(:disabled) {
                        background: #1e293b;
                        border-color: #1e293b;
                    }
                    #${toolbarId} button:disabled {
                        opacity: 0.45;
                        box-shadow: none;
                        cursor: not-allowed;
                    }
                    #${stateChipId} {
                        display: inline-flex;
                        align-items: center;
                        min-height: 32px;
                        padding: 0 12px;
                        border-radius: 999px;
                        background: rgba(15, 23, 42, 0.06);
                        color: #334155;
                        font-size: 12px;
                        font-weight: 600;
                        letter-spacing: 0.01em;
                    }
                `;
                document.head.appendChild(style);
            }

            function getController() {
                const root = document.querySelector(rootSelector);
                if (!root) {
                    return null;
                }
                const fiberKey = Object.keys(root).find((key) =>
                    key.startsWith("__reactFiber$")
                );
                return fiberKey ? root[fiberKey]?.return?.stateNode ?? null : null;
            }

            function getDefaultToolbar() {
                const restoreButton = [...document.querySelectorAll("button")].find(
                    (button) => button.textContent.trim() === "Restore"
                );
                return restoreButton?.parentElement ?? null;
            }

            function syncToolbar() {
                ensureStyles();
                const controller = getController();
                const defaultToolbar = getDefaultToolbar();
                if (!controller || !defaultToolbar) {
                    return false;
                }

                defaultToolbar.style.display = "none";
                const headerRow = defaultToolbar.parentElement;
                const selectionPill = [...headerRow.children].find(
                    (child) => child !== defaultToolbar && child.textContent.includes("Selected:")
                );

                let toolbar = document.getElementById(toolbarId);
                if (!toolbar) {
                    toolbar = document.createElement("div");
                    toolbar.id = toolbarId;

                    const selectionButton = document.createElement("button");
                    selectionButton.type = "button";
                    selectionButton.dataset.action = "toggle-selection";
                    selectionButton.dataset.variant = "secondary";

                    const filterButton = document.createElement("button");
                    filterButton.type = "button";
                    filterButton.dataset.action = "toggle-filter";
                    filterButton.dataset.variant = "primary";

                    const stateChip = document.createElement("span");
                    stateChip.id = stateChipId;

                    toolbar.append(selectionButton, filterButton, stateChip);
                    headerRow.insertBefore(toolbar, selectionPill ?? defaultToolbar.nextSibling);
                }

                const rowsAll = controller.state.rows_all_unfiltered.length;
                const rowsFiltered = controller.state.rows_filtered.length;
                const rowsSelected = controller.state.rows_selected.length;
                const hasActiveFilter = rowsFiltered < rowsAll;
                const canIsolate = rowsSelected > 0 && rowsSelected < rowsFiltered;

                const selectionButton = toolbar.querySelector(
                    '[data-action="toggle-selection"]'
                );
                const filterButton = toolbar.querySelector('[data-action="toggle-filter"]');
                const stateChip = toolbar.querySelector(`#${stateChipId}`);

                selectionButton.textContent = rowsSelected === 0 ? "Select all" : "Unselect";
                selectionButton.disabled = rowsFiltered === 0;
                selectionButton.onclick = () => {
                    const liveController = getController();
                    if (!liveController) {
                        return;
                    }
                    if (liveController.state.rows_selected.length === 0) {
                        liveController.setSelected([...liveController.state.rows_filtered], null);
                    } else {
                        liveController.setSelected([], null);
                    }
                };

                filterButton.textContent = hasActiveFilter ? "Reset" : "Isolate";
                filterButton.disabled = !hasActiveFilter && !canIsolate;
                filterButton.onclick = () => {
                    const liveController = getController();
                    if (!liveController) {
                        return;
                    }
                    if (
                        liveController.state.rows_filtered.length <
                        liveController.state.rows_all_unfiltered.length
                    ) {
                        liveController.restoreAllRows();
                    } else if (
                        liveController.state.rows_selected.length > 0 &&
                        liveController.state.rows_selected.length <
                        liveController.state.rows_filtered.length
                    ) {
                        liveController.filterRows(true);
                    }
                };

                stateChip.textContent = hasActiveFilter
                    ? `${rowsFiltered} isolated`
                    : rowsSelected === 0
                      ? "No active selection"
                      : `${rowsSelected} selected`;

                return true;
            }

            function patchController() {
                const controller = getController();
                if (!controller) {
                    return false;
                }

                if (!controller.__molabToolbarPatched) {
                    controller.__molabToolbarPatched = true;
                    ["restoreAllRows", "filterRows", "setSelected"].forEach((methodName) => {
                        const original = controller[methodName].bind(controller);
                        controller[methodName] = (...args) => {
                            const result = original(...args);
                            window.requestAnimationFrame(() =>
                                window.requestAnimationFrame(syncToolbar)
                            );
                            return result;
                        };
                    });
                }

                return syncToolbar();
            }

            let attempts = 0;
            function initializeToolbar() {
                attempts += 1;
                if (patchController()) {
                    return;
                }
                if (attempts < 40) {
                    window.setTimeout(initializeToolbar, 100);
                }
            }

            initializeToolbar();
        })();
        """
        hiplot_html = hiplot_html.replace(
            "/*ON_LOAD_SCRIPT_INJECT*/", selection_bridge_script
        )
        hiplot_html = hiplot_html.replace(
            "/*AFTER_SETUP_SCRIPT_INJECT*/", toolbar_polish_script
        )
        return (
            '<iframe '
            'style="width: 100%; border: 1px solid #dbe4f0; border-radius: 18px; '
            'box-shadow: 0 18px 40px rgba(15, 23, 42, 0.08); '
            f'height: {height}px; background: white;" '
            'sandbox="allow-scripts" '
            f'srcdoc="{html.escape(hiplot_html, quote=True)}"></iframe>'
        )

    return create_published_hiplot_iframe_html, selection_message_type


@app.cell
def _(mo):
    mo.md("# Explore published ITCR PCA outcomes in HiPlot")
    return


@app.cell
def _(Path, pca_result_options):
    pca_result_labels = list(pca_result_options)
    return (pca_result_labels,)


@app.cell
def _(
    load_cancer_color_map,
    load_clinical_metadata,
    load_metadata_tooltips,
    metadata_presentation,
    strip_metadata,
):
    cancer_color_map = load_cancer_color_map()
    clinical_metadata = load_clinical_metadata().merge(
        strip_metadata,
        on="patient_id",
        how="left",
    )
    metadata_tooltips = load_metadata_tooltips()
    metadata_groups, base_tooltips, wrapped_columns, format_mapping = (
        metadata_presentation()
    )
    return (
        base_tooltips,
        cancer_color_map,
        clinical_metadata,
        format_mapping,
        metadata_groups,
        metadata_tooltips,
        wrapped_columns,
    )


@app.cell
def _(available_color_fields, clinical_metadata, strip_label_to_column):
    base_fields = available_color_fields(clinical_metadata)
    color_field_options = []
    for option in [
        "Cancer Type",
        *[field for field in base_fields if field != "Cancer Type"],
        *strip_label_to_column.keys(),
    ]:
        if option not in color_field_options:
            color_field_options.append(option)
    color_field_to_column = {field: field for field in base_fields} | strip_label_to_column
    return color_field_options, color_field_to_column


@app.cell
def _(color_field_options, mo, pca_result_labels):
    pca_result_dropdown = mo.ui.dropdown(
        options=pca_result_labels,
        value=pca_result_labels[0],
        label="PCA result set:",
    )
    color_by_dropdown = mo.ui.dropdown(
        options=color_field_options,
        value="Cancer Type",
        label="Color samples by:",
    )
    return color_by_dropdown, pca_result_dropdown


@app.cell
def _(load_embedding_sample_frame, pca_result_dropdown, pca_result_options):
    pca_embedding_df = load_embedding_sample_frame(
        pca_result_options[pca_result_dropdown.value]
    )
    return (pca_embedding_df,)


@app.cell
def _(
    build_strip_color_lookup,
    cancer_color_map,
    clinical_metadata,
    color_by_dropdown,
    color_field_to_column,
    pca_embedding_df,
    prepare_embedding_for_display,
    strip_spec_by_column,
    strip_unknown_color,
):
    selected_color_column = color_field_to_column[color_by_dropdown.value]
    pca_display_df, pca_label_colors = prepare_embedding_for_display(
        pca_embedding_df,
        clinical_metadata,
        selected_color_column,
        cancer_color_map,
    )
    if selected_color_column in strip_spec_by_column:
        pca_label_colors = build_strip_color_lookup(
            pca_display_df["Color Label"].tolist(),
            selected_color_column,
            strip_spec_by_column,
            cancer_color_map,
            strip_unknown_color,
        )
    return pca_display_df, pca_label_colors


@app.cell
def _(default_visible_features, get_feature_columns, pca_display_df):
    pca_feature_columns = get_feature_columns(pca_display_df)
    default_features = default_visible_features(pca_feature_columns, limit=10)
    optional_metadata_columns = [
        column
        for column in [
            "tissue_or_organ_of_origin",
            "primary_diagnosis",
            "molecular_subtype",
            "patient_id",
        ]
        if column in pca_display_df.columns
    ]
    hiplot_column_options = [*pca_feature_columns, *optional_metadata_columns]
    return default_features, hiplot_column_options


@app.cell
def _(default_features, hiplot_column_options, mo):
    hiplot_feature_picker = mo.ui.multiselect(
        options=hiplot_column_options,
        value=default_features,
        label="Visible HiPlot columns:",
    )
    return (hiplot_feature_picker,)


@app.cell
def _(coerce_visible_features, hiplot_column_options, hiplot_feature_picker):
    active_hiplot_features = coerce_visible_features(
        hiplot_column_options,
        list(hiplot_feature_picker.value),
        limit=10,
    )
    return (active_hiplot_features,)


@app.cell
def _(anywidget, json, selection_message_type, traitlets):
    empty_hiplot_selection_state = json.dumps(
        {"selected_uids": [], "filtered_uids": []},
        separators=(",", ":"),
    )

    class HiplotSelectionBridge(anywidget.AnyWidget):
        selection_state = traitlets.Unicode(empty_hiplot_selection_state).tag(sync=True)
        message_type = traitlets.Unicode(selection_message_type).tag(sync=True)
        _esm = """
        function normalizeState(rawState) {
          const state =
            rawState && typeof rawState === "object" ? rawState : {};
          const normalizeList = (value) =>
            Array.isArray(value) ? value.map((item) => String(item)) : [];
          return {
            selected_uids: normalizeList(state.selected_uids),
            filtered_uids: normalizeList(state.filtered_uids),
          };
        }

        function render({ model, el }) {
          el.style.display = "none";
          el.style.width = "0";
          el.style.height = "0";

          const handleMessage = (event) => {
            const data = event?.data;
            if (!data || data.type !== model.get("message_type")) {
              return;
            }

            const nextValue = JSON.stringify(
              normalizeState(data.bridge_state)
            );
            if (model.get("selection_state") === nextValue) {
              return;
            }

            model.set("selection_state", nextValue);
            model.save_changes();
          };

          window.addEventListener("message", handleMessage);
          return () => window.removeEventListener("message", handleMessage);
        }

        export default { render };
        """

    return HiplotSelectionBridge, empty_hiplot_selection_state


@app.cell
def _(HiplotSelectionBridge, empty_hiplot_selection_state, mo):
    hiplot_selection_bridge = HiplotSelectionBridge(
        selection_state=empty_hiplot_selection_state
    )
    get_hiplot_selection_state, set_hiplot_selection_state = mo.state(
        hiplot_selection_bridge.selection_state
    )
    hiplot_selection_bridge.observe(
        lambda _: set_hiplot_selection_state(
            hiplot_selection_bridge.selection_state
        ),
        names=["selection_state"],
    )
    return get_hiplot_selection_state, hiplot_selection_bridge


@app.cell
def _(
    active_hiplot_features,
    cancer_color_map,
    create_published_hiplot_iframe_html,
    mo,
    pca_display_df,
    pca_label_colors,
):
    hiplot_iframe = mo.Html(
        create_published_hiplot_iframe_html(
            embedding_df=pca_display_df,
            visible_columns=active_hiplot_features,
            selected_sample_ids=None,
            height=820,
            colorby_column="Color Label",
            label_colors=pca_label_colors,
            cancer_color_map=cancer_color_map,
        )
    )
    return (hiplot_iframe,)


@app.cell
def _(get_hiplot_selection_state, json, pca_display_df):
    try:
        raw_selection_state = json.loads(get_hiplot_selection_state() or "{}")
    except json.JSONDecodeError:
        raw_selection_state = {}

    if not isinstance(raw_selection_state, dict):
        raw_selection_state = {}

    valid_sample_ids = set(pca_display_df["Sample ID"].astype(str))
    total_sample_count = len(valid_sample_ids)

    def normalize_sample_ids(values):
        if not isinstance(values, list):
            return []
        return [
            sample_id
            for sample_id in values
            if isinstance(sample_id, str) and sample_id in valid_sample_ids
        ]

    selected_sample_ids = normalize_sample_ids(
        raw_selection_state.get("selected_uids", [])
    )
    filtered_sample_ids = normalize_sample_ids(
        raw_selection_state.get("filtered_uids", [])
    )

    if filtered_sample_ids and len(filtered_sample_ids) < total_sample_count:
        selected_hiplot_sample_ids = filtered_sample_ids
    elif selected_sample_ids and len(selected_sample_ids) < total_sample_count:
        selected_hiplot_sample_ids = selected_sample_ids
    else:
        selected_hiplot_sample_ids = []

    hiplot_selection_summary = {
        "selected_count": len(selected_sample_ids),
        "filtered_count": (
            len(filtered_sample_ids) if filtered_sample_ids else total_sample_count
        ),
        "is_filtered": bool(filtered_sample_ids)
        and len(filtered_sample_ids) < total_sample_count,
    }
    return hiplot_selection_summary, selected_hiplot_sample_ids


@app.cell
def _(build_metadata_views, pca_display_df, selected_hiplot_sample_ids):
    filtered_metadata_df, duplicate_patients_df, metadata_summary = build_metadata_views(
        pca_display_df,
        selected_hiplot_sample_ids,
    )
    return duplicate_patients_df, filtered_metadata_df, metadata_summary


@app.cell
def _(
    hiplot_selection_bridge,
    mo,
    pca_result_dropdown,
    color_by_dropdown,
    hiplot_feature_picker,
    hiplot_iframe,
):
    controls = mo.hstack([pca_result_dropdown, color_by_dropdown], widths=[1, 1])

    mo.vstack(
        [
            mo.md("## Published PCA HiPlot explorer"),
            controls,
            mo.md(
                "_This Molab-ready copy fetches its PCA parquet, helper module, and metadata assets from GitHub raw URLs at runtime._"
            ),
            mo.md(
                "_Use the dropdown to switch between PCA result sets. The HiPlot axes now read left to right, the embedded controls are reduced to Select/Unselect and Isolate/Reset, and the metadata table below stays linked to the active HiPlot state._"
            ),
            hiplot_feature_picker,
            hiplot_selection_bridge,
            hiplot_iframe,
        ]
    )
    return


@app.cell
def _(
    base_tooltips,
    filtered_metadata_df,
    format_mapping,
    hiplot_selection_summary,
    metadata_groups,
    metadata_summary,
    metadata_tooltips,
    mo,
    selected_hiplot_sample_ids,
    wrapped_columns,
):
    header_tooltips = {**metadata_tooltips, **base_tooltips}

    def make_table(dataframe, columns, label, page_size=14, max_height=360):
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
                for column in ["Sample ID", "patient_id"]
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
            name: make_table(filtered_metadata_df, columns, f"{name} metadata")
            for name, columns in metadata_groups.items()
        }
        | {
            "All metadata": make_table(
                filtered_metadata_df,
                list(filtered_metadata_df.columns),
                "All PCA metadata",
                page_size=10,
                max_height=460,
            )
        }
    )

    mo.vstack(
        [
            mo.md("### Expanded metadata table"),
            mo.md(
                "Showing all samples in the current PCA result."
                if not selected_hiplot_sample_ids
                else (
                    f"Showing {len(selected_hiplot_sample_ids)} isolated samples from HiPlot."
                    if hiplot_selection_summary["is_filtered"]
                    else f"Showing {len(selected_hiplot_sample_ids)} selected samples from HiPlot."
                )
            ),
            mo.hstack(
                [
                    mo.stat(
                        metadata_summary["sample_count"],
                        label="Samples shown",
                        caption="Rows currently visible in the metadata table.",
                        bordered=True,
                    ),
                    mo.stat(
                        metadata_summary["unique_patient_count"],
                        label="Unique patients shown",
                        caption="Distinct `patient_id` values in the current metadata selection.",
                        bordered=True,
                    ),
                    mo.stat(
                        metadata_summary["cancer_type_count"],
                        label="Cancer types shown",
                        caption="Distinct cancer labels represented in the current metadata selection.",
                        bordered=True,
                    ),
                ],
                widths=[1, 1, 1],
            ),
            metadata_tabs,
        ]
    )
    return


if __name__ == "__main__":
    app.run()
