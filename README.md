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

## Design notes

- `docs/vision_workflow.md`: target perceive → think → remember → act loop vs what is implemented now (including Letta/RAG/vision detail).

## Project layout

- `src/data.py`: ingestion, manifest generation, split logic
- `src/baselines.py`: OpenCV/ResNet baseline task specs and interfaces
- `src/training.py`: training config and metrics persistence
- `src/serengeti_image_paths.py` / `src/image_training.py`: map downloaded JPEGs to manifest rows; ResNet-18 disk fine-tuning
- `src/agent.py`: Instinct Agent + Primal Mind decision logic
- `src/pot.py`: PoT capture/control assumptions and keymap
- `src/letta_tools.py`: Letta tool schemas and stubs
- `src/pipeline.py`: end-to-end lightweight pipeline summary
- `scripts/prepare_data.py`: manifest build command
- `scripts/download_serengeti_images.py`: fetch a small subset of manifest image URLs locally
- `scripts/train_serengeti_images.py`: fine-tune ResNet-18 on local Serengeti JPEGs
- `scripts/evaluate_serengeti_images.py`: confusion matrix + class report for local checkpoint
- `scripts/kaggle_stats.py`: column + row counts for CSVs under `data/raw/kaggle/`
- `scripts/run_paleo_live.py`: one-command HUD launcher with optional live screen capture
- `scripts/run_paleo_control_loop.py`: safe advice/control loop with kill switch + optional snapshots
- `scripts/run_paleo_overlay.py`: transparent always-on-top overlay HUD
- `scripts/build_paleo_exe.py`: build `dist/PALEO.exe` with PyInstaller
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

For live screen-derived inputs (no Path of Titans API/mod hooks), run:

```bash
py -3 scripts/run_paleo_live.py
```

This starts `serve_companion.py --live-capture --full-screen` and opens the HUD; `/api/hud` then uses `mss` frame stats from your full primary monitor.
HUD now supports both options: live screen capture on/off toggle.
HUD debug view includes: live frame preview image, raw thought JSON string, Letta trace metadata, and keyboard/mouse control preview outputs.

### Safe control loop (V1, no game API)

You can test this on any screen (Cursor, desktop, browser) before trying with Path of Titans.

```bash
py -3 scripts/run_paleo_control_loop.py --input-source live --full-screen --mode advice --ticks 20 --snapshot-every 5
py -3 scripts/run_paleo_control_loop.py --input-source manual --manual-threat 0.8 --mode advice --ticks 5
```

For guarded keyboard control (still no game API):

```bash
py -3 scripts/run_paleo_control_loop.py --mode control --enable-control --fps 4
```

Emergency stop key: `f12` (configurable in `src/config.py`).

Short **in-game** checklist and next tasks: `TODO.md`.

### Transparent on-top overlay

```bash
py -3 scripts/run_paleo_overlay.py --mode advice
```

Close overlay with `Esc` or **Close**; drag the **gradient title bar**; **Workflow** explains PALEO.exe vs overlay vs control loop; **A−/A+** and **Detail** mirror `+/−` and `Tab`.

### Build PALEO.exe (Windows)

```bash
py -3 -m pip install pyinstaller
py -3 scripts/build_paleo_exe.py --target both
```

Output: `dist/PALEO.exe` (live HUD) and `dist/PALEOOverlay.exe` (transparent on-top overlay).

### Running the executables

- `dist/PALEO.exe`: starts local HUD server and opens browser companion HUD.
- `dist/PALEOOverlay.exe`: transparent always-on-top overlay (bordered UI, gradient header, toolbar buttons, wrapped status text, `+/-` / `Tab` still work).

**PALEO Profiles** (creature reference mini-site): use the **Profiles** tab from the main site on **GitHub Pages** — no need to run Python for that. Profiles load JSON + curve text via `fetch()`; avoid raw `file://`. Optionally open `http://127.0.0.1:8765/profiles/index.html` when already running `serve_companion.py` for the Companion HUD. (`serve_companion.py` is for HUD `/api/*`, not required for browsing Profiles.) For planning **distinct visuals per future creature** while sharing the same data model, see `docs/profiles_future_styles.md`.

**Chroma Strata** (PoT-style skin lab): open `pages/chroma-strata.html` from the site nav or `http://127.0.0.1:8765/chroma-strata.html` when `serve_companion.py` is running. Loads **`pages/skin-db/`** (see `pages/skin-db/README.md`): colors **1–6** (color **5** tints the selected **pattern**; **6** = eyes), constants **background / lineart / details / infoLayer** (top PNG), optional **`infoNotes`** `.md` for the sidebar only; optional **`canvasSize`**, **`tintComposite`** / **`constantsBlend`** (see `skin-db/README.md`), and in-page **preview** (fit to panel). **Randomize colors only** vs **colors + patterns** (**Shift+R** / **R**). Custom hex swatches per slot persist in **localStorage**; commit PNGs under `skin-db/<SkinId>/` (e.g. `skin-db/AsagiYang/`) so assets load automatically. **Download PNG** exports the canvas.

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

### Train on local JPEGs (requires working `torch` + `torchvision`)

Uses the **same filenames** as the download script and labels from the manifest (`predator_label`).

```bash
python scripts/download_serengeti_images.py --max-images 64 --split train
python scripts/train_serengeti_images.py --epochs 5 --batch-size 8
```

Artifacts: `results/experiments/serengeti_disk_resnet18/resnet18_serengeti_disk.pt` and `metrics.json`.

### Evaluate local JPEG baseline checkpoint

Save confusion matrix + precision/recall/F1 on local eval images:

```bash
py -3 scripts/evaluate_serengeti_images.py --checkpoint results/experiments/serengeti_disk_resnet18_e5_n256/resnet18_serengeti_disk.pt
```

Artifact: `results/experiments/.../eval/eval_metrics.json`.

## Notes

- No absolute paths are required.
- Heavy training and PoT control loops are scaffolded to be expanded in later phases.
