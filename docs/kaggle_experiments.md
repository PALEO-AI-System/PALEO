# Running PALEO Experiments on Kaggle

PALEO can run its current image experiments on Kaggle with a GPU notebook.
The existing experiment runner trains ResNet-18 on locally available Snapshot
Serengeti JPEGs and writes metrics under `results/experiments/`.

## What works today

- `scripts/prepare_data.py`: builds `data/manifests/serengeti_manifest.jsonl`.
- `scripts/download_serengeti_images.py`: downloads a capped image subset from HTTP URLs in the manifest.
- `scripts/run_experiments.py`: runs the heuristic baseline and ResNet-18 sweep.
- `scripts/make_figures.py`: regenerates report figures from experiment histories.

The Kaggle `animal-behavior-prediction/abp_accel.csv` file is time-series
accelerometer data, not image data. It is useful for a future behavior
classification experiment, but it does not feed the current ResNet image
training script directly.

## Kaggle Notebook Setup

Create a Kaggle notebook with GPU enabled, then either upload this repo as a
Kaggle dataset or clone it into the notebook.

If cloning:

```bash
git clone https://github.com/PALEO-AI-System/PALEO.git
cd PALEO
```

Install dependencies that Kaggle may not already include:

```bash
pip install -q -r requirements.txt
pip install -q kaleido
```

## Download About 1k Images From Kaggle

For Kaggle API access, create/download your Kaggle token from
**Kaggle > Account > Create New API Token** and make sure `kaggle.json` is
available to the notebook or local shell.

First inspect what the dataset exposes:

```bash
python scripts/download_kaggle_image_sample.py --dataset obulikarthikeyan/animal-behavior-prediction --list-only
python scripts/download_kaggle_image_sample.py --dataset sttaseen/animal-behaviour --list-only
```

If a dataset exposes image files directly, download up to 1,000:

```bash
python scripts/download_kaggle_image_sample.py --dataset obulikarthikeyan/animal-behavior-prediction --max-images 1000
```

The `sttaseen/animal-behaviour` dataset metadata lists videos rather than
standalone images, so create a 1,000-image sample by extracting JPEG frames:

```bash
python scripts/download_kaggle_image_sample.py --dataset sttaseen/animal-behaviour --max-images 1000 --include-video-frames
```

Outputs are written by default to:

```text
data/processed/kaggle_image_samples/<owner>__<dataset>/
```

Use `--frame-step 60` to sample fewer nearby video frames, or `--frame-step 10`
to sample more densely.

## Option A: Run With Snapshot Serengeti CSVs

Add the Snapshot Serengeti/Dryad CSV files to the notebook input and place them
where the repo expects them:

```bash
mkdir -p data/raw/dryad
cp /kaggle/input/<your-dataset>/consensus_data.csv data/raw/dryad/consensus_data.csv
cp /kaggle/input/<your-dataset>/all_images.csv data/raw/dryad/all_images.csv
```

Build a manifest:

```bash
python scripts/prepare_data.py --csv data/raw/dryad/consensus_data.csv --max-records 5000
```

Download a small reproducible image subset. Increase `--max-images` if the GPU
runtime has enough time:

```bash
python scripts/download_serengeti_images.py --max-images 256
```

Run the experiment sweep:

```bash
python scripts/run_experiments.py
```

Generate figures:

```bash
python scripts/make_figures.py
```

Expected outputs:

- `results/experiments/comparison_table.json`
- `results/experiments/all_histories.json`
- `results/experiments/*/resnet18_serengeti_disk.pt`
- `output/figures/convergence_curves.png`
- `output/figures/lr_sensitivity.png`
- `output/figures/final_comparison.png`

## Option B: Quick Smoke Test

Use fewer records and images to verify the notebook environment:

```bash
python scripts/prepare_data.py --csv data/raw/dryad/consensus_data.csv --max-records 500
python scripts/download_serengeti_images.py --max-images 32
python scripts/run_experiments.py
```

## Download Outputs From Kaggle

After the run, zip the artifacts:

```bash
zip -r paleo-kaggle-results.zip results output/figures data/manifests
```

Then download `paleo-kaggle-results.zip` from the Kaggle notebook output panel.

## Notes

- Enable GPU in Notebook Settings before running `scripts/run_experiments.py`.
- If internet is disabled, pre-package the JPEGs as a Kaggle dataset instead of
  using `download_serengeti_images.py`.
- Keep big image folders/checkpoints out of git. Commit only small metrics,
  figures, and docs that should be shared.
