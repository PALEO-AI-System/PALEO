"""Tests for Kaggle CSV inventory helpers."""

from __future__ import annotations

import unittest
from pathlib import Path

from src.kaggle_ingest import csv_quick_stats, iter_kaggle_csv_paths


class TestKaggleIngest(unittest.TestCase):
    def test_csv_quick_stats_counts_rows(self) -> None:
        root = Path(__file__).resolve().parents[1]
        sample = root / "tests" / "fixtures" / "kaggle_sample.csv"
        stats = csv_quick_stats(sample, max_preview_rows=1)
        self.assertEqual(stats["num_rows"], 2)
        self.assertEqual(stats["columns"], ["a", "b"])
        self.assertEqual(len(stats["preview_rows"]), 1)

    def test_iter_paths_empty_when_missing(self) -> None:
        paths = iter_kaggle_csv_paths(Path("/nonexistent/kaggle"))
        self.assertEqual(paths, [])


if __name__ == "__main__":
    unittest.main()
