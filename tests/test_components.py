"""Component tests for data, agent, pot, and Letta modules."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.agent import default_agent_state, decide_action, format_thought_log
from src.config import DataConfig
from src.data import create_synthetic_manifest, sample_training_batch
from src.letta_tools import get_letta_tool_specs
from src.pot import describe_pot_integration_assumptions


class TestComponents(unittest.TestCase):
    def test_synthetic_manifest_and_batch(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cfg = DataConfig(
                root_dir=root,
                raw_dir=root / "raw",
                processed_dir=root / "processed",
                manifests_dir=root / "manifests",
                snapshot_serengeti_metadata_url="https://example.com",
                snapshot_serengeti_license_url="https://example.com/license",
                predator_species=("lion", "hyena_spotted"),
                train_split=0.6,
                val_split=0.2,
                test_split=0.2,
                split_seed=7,
                max_records=24,
            )
            cfg.validate_splits()
            records = create_synthetic_manifest(cfg, num_records=24)
            self.assertEqual(len(records), 24)
            batch = sample_training_batch(cfg, split="train", batch_size=5)
            self.assertGreaterEqual(len(batch), 1)
            self.assertLessEqual(len(batch), 5)

    def test_agent_action_and_thought_log(self) -> None:
        state = default_agent_state("dino-test")
        action = decide_action(state)
        self.assertIsInstance(action, str)
        thought = format_thought_log(state, action)
        self.assertIn("primal_mind", thought)
        self.assertIn("decision", thought)

    def test_pot_assumptions_shape(self) -> None:
        assumptions = describe_pot_integration_assumptions()
        self.assertIn("capture_region", assumptions)
        self.assertIn("target_fps", assumptions)
        self.assertIn("emergency_stop_key", assumptions)

    def test_letta_tool_specs(self) -> None:
        specs = get_letta_tool_specs()
        names = {spec.name for spec in specs}
        required = {
            "get_dataset_stats",
            "get_kaggle_local_inventory",
            "train_model",
            "evaluate_model",
            "run_pot_agent",
            "query_pot_wiki",
            "set_personality_traits",
        }
        self.assertTrue(required.issubset(names))


if __name__ == "__main__":
    unittest.main()
