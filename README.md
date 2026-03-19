# PALEO

PALEO is an AI system for instinct-driven dinosaur agents in Path of Titans.
It combines wildlife-derived ML baselines with an `Instinct Agent` that uses
`Primal Mind` memory blocks (personality, goals, recent experiences) to decide
high-level actions.

## What is implemented now

- Dataset ingestion scaffolding with deterministic manifest format (JSONL)
- Real split handling (train/val/test) and predator/prey label mapping
- Baseline interfaces:
  - OpenCV-style rule baseline (deterministic lightweight implementation)
  - ResNet-18 baseline contract + model builder (when torch is installed)
- Training loop scaffold with saved metrics for reproducibility
- Instinct Agent + Primal Mind state and structured thought logs
- Path of Titans integration assumptions and action key mapping
- Letta tool surface definitions and local stubs

## Project layout

- `src/data.py`: ingestion, manifest generation, split logic
- `src/baselines.py`: OpenCV/ResNet baseline task specs and interfaces
- `src/training.py`: training config and metrics persistence
- `src/agent.py`: Instinct Agent + Primal Mind decision logic
- `src/pot.py`: PoT capture/control assumptions and keymap
- `src/letta_tools.py`: Letta tool schemas and stubs
- `src/pipeline.py`: end-to-end lightweight pipeline summary
- `scripts/prepare_data.py`: manifest build command
- `scripts/download_serengeti_images.py`: fetch a small subset of manifest image URLs locally
- `scripts/kaggle_stats.py`: column + row counts for CSVs under `data/raw/kaggle/`
- `scripts/show_letta_tools.py`: print Letta tool schemas
- `scripts/run_pipeline.py`: run integrated summary pipeline

## Environment setup (reproducible)

### 1) Create virtual environment

Windows PowerShell:

```bash
python -m venv .venv
.venv\Scripts\activate
```

macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

### 2) Install dependencies

```bash
pip install -r requirements.txt
```

## Run commands

From repository root:

```bash
python scripts/prepare_data.py
python scripts/run_pipeline.py
python scripts/show_letta_tools.py
python -m unittest discover -s tests -p "test_*.py"
```

### Local PoT-style Companion HUD (no game install)

Runs a tiny local server that serves `pages/` and JSON endpoints used by `pages/companion-hud.html` (Instinct Agent tick, Primal Mind snapshot, optional training metrics). Use this beside Path of Titans on a second monitor or Alt+Tab — it does not modify game files.

```bash
python scripts/serve_companion.py
```

Then open `http://127.0.0.1:8765/companion-hud.html` (avoid `file://`, which cannot reach `/api/*`).

**GitHub Pages:** you can open `companion-hud.html` from the site nav, but Pages only serves static files — there is no `/api/*`. The page falls back to an **offline preview** (browser-only heuristic). For the real **Instinct Agent** output matching the Python code, use `serve_companion.py` locally.

## Real dataset path (Dryad CSV exports of Snapshot Serengeti)

In this repo we build manifests from CSV metadata.

Dryad provides convenient CSV exports of Snapshot Serengeti (same underlying dataset). In this repo the current manifest builder ingests:
- `data/raw/dryad/consensus_data.csv` (labels/species/behavior columns)
- `data/raw/dryad/all_images.csv` (image URL fragments), joined on `CaptureEventID` to populate `image_path`

Use one of these approaches:

1. Start with synthetic manifest for development:
   - `python scripts/prepare_data.py`
2. Build manifest from your downloaded metadata CSV:
   - `python scripts/prepare_data.py --csv path/to/metadata.csv --max-records 500`

For this project specifically, a good starting command is:

```bash
python scripts/prepare_data.py --csv data/raw/dryad/consensus_data.csv --max-records 5000
```

Expected manifest location:

- `data/manifests/serengeti_manifest.jsonl`

### Kaggle CSVs (local extracts)

**Multi-GB Kaggle bundles:** deferred on purpose — see `docs/deferred_large_datasets.md`.

Place downloads under `data/raw/kaggle/<dataset>/` (see per-folder `README.txt`). Inventory CSVs (streaming row counts, no load-all):

```bash
python scripts/kaggle_stats.py
python scripts/kaggle_stats.py --quick
python scripts/kaggle_stats.py --json
```

### Optional: download a few real camera-trap images

Requires a manifest with `image_path` set to `https://...` (Dryad consensus + `all_images` join from `prepare_data`):

```bash
python scripts/download_serengeti_images.py --max-images 16 --split train
```

Images are written under `data/processed/serengeti_images/` (gitignored).

## Notes

- No absolute paths are required.
- Heavy training and PoT control loops are scaffolded to be expanded in later phases.
