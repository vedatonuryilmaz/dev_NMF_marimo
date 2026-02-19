# tcga-nmf

Explore ATAC-seq data from 797 cancer samples.

This project uses [uv](https://docs.astral.sh/uv/getting-started/installation/) for environment and dependency management.

## Setup

```sh
git clone https://github.com/abdenlab/tcga-nmf.git
cd tcga-nmf
uv sync
```

## Run Marimo apps

### NMF explorer (ported from `nmf.ipynb`)

```sh
uv run marimo run nmf_marimo.py
```

### HiGlass explorer (ported from `higlass.ipynb`)

```sh
uv run marimo run higlass_marimo.py
```

## Optional: launch Jupyter

```sh
uv run jupyter lab
```
