"""Tests for the minimal pipeline scaffold."""

import unittest

from src.pipeline import run_pipeline


class TestPipeline(unittest.TestCase):
    def test_run_pipeline_returns_message(self) -> None:
        result = run_pipeline()
        self.assertIsInstance(result, str)
        self.assertIn("pipeline is running", result.lower())
        self.assertIn("data_root=", result)
        self.assertIn("splits=", result)
        self.assertIn("num_records=", result)
        self.assertIn("batch_examples=", result)
        self.assertIn("baseline=", result)
        self.assertIn("opencv_accuracy=", result)
        self.assertIn("resnet=", result)
        self.assertIn("task_specs=", result)
        self.assertIn("training_epochs=", result)
        self.assertIn("final_train_loss=", result)
        self.assertIn("final_val_loss=", result)
        self.assertIn("dataset_stats=", result)
        self.assertIn("agent_action=", result)
        self.assertIn("thought_log=", result)
        self.assertIn("pot_fps=", result)
        self.assertIn("pot_emergency_key=", result)
        self.assertIn("action_keymap=", result)
        self.assertIn("letta_tools=", result)
        self.assertIn("kaggle_local=", result)


if __name__ == "__main__":
    unittest.main()
