"""Tests for Serengeti local path naming (must match download script)."""

from __future__ import annotations

import unittest
from pathlib import Path

from src.data import DatasetRecord
from src.serengeti_image_paths import list_records_with_local_files, local_image_path, serengeti_local_filename


class TestSerengetiImagePaths(unittest.TestCase):
    def test_filename_deterministic(self) -> None:
        name = serengeti_local_filename("ASG0001", "https://example.com/a/b/c/file.JPEG")
        self.assertTrue(name.endswith(".jpeg"))
        again = serengeti_local_filename("ASG0001", "https://example.com/a/b/c/file.JPEG")
        self.assertEqual(name, again)

    def test_list_records_filters_http_and_existing_files(self) -> None:
        root = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "fake_serengeti_cache"
        root.mkdir(parents=True, exist_ok=True)
        url = "https://snapshotserengeti.example/S1/test.jpg"
        rec = DatasetRecord(
            sample_id="SAMPLE1",
            image_path=url,
            species="zebra",
            predator_label=0,
            split="train",
            source="test",
        )
        fname = serengeti_local_filename(rec.sample_id, rec.image_path)
        fake_img = root / fname
        fake_img.write_bytes(b"\xff\xd8\xff\xdb")  # minimal JPEG-like header
        try:
            found = list_records_with_local_files([rec], root)
            self.assertEqual(len(found), 1)
            self.assertEqual(local_image_path(rec, root), fake_img)
        finally:
            if fake_img.exists():
                fake_img.unlink()
            try:
                root.rmdir()
            except OSError:
                pass


if __name__ == "__main__":
    unittest.main()
