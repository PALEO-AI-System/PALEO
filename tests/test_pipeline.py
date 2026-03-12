"""Tests for the minimal pipeline scaffold."""

import unittest

from src.pipeline import run_pipeline


class TestPipeline(unittest.TestCase):
    def test_run_pipeline_returns_message(self) -> None:
        result = run_pipeline()
        self.assertIsInstance(result, str)
        self.assertIn("hello pipeline", result.lower())


if __name__ == "__main__":
    unittest.main()
