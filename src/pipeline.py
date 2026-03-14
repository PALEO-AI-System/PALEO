"""Minimal pipeline scaffold.

No model logic is implemented yet. This module only provides a
runnable placeholder pipeline to validate repository structure.
"""

from .config import default_data_config
from .data import prepare_datasets, sample_training_batch
from .baselines import run_opencv_baseline
from .training import default_training_config, run_training_loop
from .agent import default_agent_state, decide_action, format_thought_log


def run_pipeline() -> str:
    """Run the placeholder pipeline and return a status message."""
    config = default_data_config()
    datasets_summary = prepare_datasets(config)
    batch = sample_training_batch()
    baseline_desc = run_opencv_baseline(batch)
    train_cfg = default_training_config()
    history = run_training_loop(train_cfg)
    last_epoch = history["epochs"][-1]
    last_train_loss = history["train_loss"][-1]
    last_val_loss = history["val_loss"][-1]

    agent_state = default_agent_state()
    agent_action = decide_action(agent_state)
    thought_log = format_thought_log(agent_state, agent_action)

    msg_parts = [
        "PALEO hello pipeline is running.",
        f"data_root={datasets_summary['root_dir']}",
        f"splits={datasets_summary['splits']}",
        f"batch_examples={len(batch)}",
        f"baseline={baseline_desc}",
        f"training_epochs={last_epoch}",
        f"final_train_loss={last_train_loss:.3f}",
        f"final_val_loss={last_val_loss:.3f}",
        f"agent_action={agent_action}",
        f"thought_log={thought_log}",
    ]
    return " ".join(msg_parts)

