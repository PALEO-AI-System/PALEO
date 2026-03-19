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

## Real dataset path (Snapshot Serengeti)

In this repo we build manifests from CSV metadata.

Dryad provides convenient CSVs for Snapshot Serengeti (the same underlying dataset); the main one we use right now is `consensus_data.csv`.

Use one of these approaches:

1. Start with synthetic manifest for development:
   - `python scripts/prepare_data.py`
2. Build manifest from your downloaded metadata CSV:
   - `python scripts/prepare_data.py --csv path/to/metadata.csv --max-records 500`

Expected manifest location:

- `data/manifests/serengeti_manifest.jsonl`

## Notes

- No absolute paths are required.
- Heavy training and PoT control loops are scaffolded to be expanded in later phases.
