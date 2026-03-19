# Deferred large downloads (TODO later)

PALEO can run on **Dryad Snapshot Serengeti CSVs**, local **camera-trap image subsets**, and small on-disk Kaggle CSVs (e.g. dinosaur tactical). The items below are **intentionally postponed** until you have **disk space** and **bandwidth**; nothing in the core pipeline requires them on day one.

| Source | Why deferred | Where to fetch / local path |
|--------|----------------|-----------------------------|
| **Kaggle — animal-behavior-prediction** | Very large (~16 GB+); heavy on laptop storage | [Dataset page](https://www.kaggle.com/datasets/obulikarthikeyan/animal-behavior-prediction) → unzip under `data/raw/kaggle/animal-behavior-prediction/` (see `README.txt` there) |
| **Kaggle — animal-behaviour (sttaseen)** | Can be multi-GB depending on bundle; optional secondary behavior data | [Dataset page](https://www.kaggle.com/datasets/sttaseen/animal-behaviour) → `data/raw/kaggle/animal-behaviour/` (see `README.txt` there) |

When you pull them: run `python scripts/kaggle_stats.py`, keep small exports in `results/` / `data/processed/`, then **delete raw extracts** to reclaim space if needed.
