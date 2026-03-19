Animal behaviour (Kaggle) — local extract folder

Not the same as: animal-behavior-prediction (~16 GB, different Kaggle page — see sibling
folder README). This one is sttaseen/animal-behaviour only.

You only need big raw files while you run stats or train. After that, keep small outputs
(e.g. metrics, checkpoints in results/, processed snippets) and delete the Kaggle extract
to free disk; re-download later if you need to reproduce.

Dataset page:
  https://www.kaggle.com/datasets/sttaseen/animal-behaviour

Reproducible fetch (after Kaggle API token in ~/.kaggle/kaggle.json — see Kaggle Account > API):
  pip install kaggle
  kaggle datasets download -d sttaseen/animal-behaviour -p data/raw/kaggle/animal-behaviour
  (PowerShell) Expand-Archive -Path animal-behaviour.zip -DestinationPath .

Prefer keeping CSV/media here so tools see paths like:
  data/raw/kaggle/animal-behaviour/<files from zip>

Do not commit large archives; run: python scripts/kaggle_stats.py
