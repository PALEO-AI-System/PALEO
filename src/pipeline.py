"""PALEO baseline pipeline."""

from .config import default_data_config
from .data import prepare_datasets, sample_training_batch
from .baselines import (
    baseline_task_specs,
    describe_opencv_baseline,
    run_opencv_baseline,
    run_resnet18_baseline,
)
from .training import default_training_config, train_resnet18_classifier
from .agent import default_agent_state, decide_action, format_thought_log
from .pot import describe_pot_integration_assumptions, sample_action_mapping
from .letta_tools import get_letta_tool_specs, get_dataset_stats
from .kaggle_ingest import summarize_kaggle_for_pipeline


def run_pipeline() -> str:
    """Run a lightweight end-to-end summary pipeline."""
    config = default_data_config()
    datasets_summary = prepare_datasets(config)
    batch = sample_training_batch(config, split="train", batch_size=16)
    opencv_metrics = run_opencv_baseline(batch)
    baseline_desc = describe_opencv_baseline(batch)
    resnet_desc = run_resnet18_baseline(batch)
    train_cfg = default_training_config()
    history = train_resnet18_classifier(batch, train_cfg)
    last_epoch = history["epochs"][-1]
    last_train_loss = history["train_loss"][-1]
    last_val_loss = history["val_loss"][-1]
    dataset_stats = get_dataset_stats(batch)
    task_specs = baseline_task_specs()

    agent_state = default_agent_state()
    agent_action = decide_action(agent_state)
    thought_log = format_thought_log(agent_state, agent_action)
    pot_assumptions = describe_pot_integration_assumptions()
    action_keymap = sample_action_mapping(["FLEE", "GRAZE", "HOLD_POSITION"])
    letta_tools = get_letta_tool_specs()
    kaggle_line = summarize_kaggle_for_pipeline()

    msg_parts = [
        "PALEO pipeline is running.",
        f"data_root={datasets_summary['root_dir']}",
        f"splits={datasets_summary['splits']}",
        f"num_records={datasets_summary['num_records']}",
        f"batch_examples={len(batch)}",
        f"baseline={baseline_desc}",
        f"opencv_accuracy={opencv_metrics['accuracy']}",
        f"resnet={resnet_desc}",
        f"task_specs={list(task_specs.keys())}",
        f"training_epochs={last_epoch}",
        f"final_train_loss={last_train_loss:.3f}",
        f"final_val_loss={last_val_loss:.3f}",
        f"dataset_stats={dataset_stats}",
        f"agent_action={agent_action}",
        f"thought_log={thought_log}",
        f"pot_fps={pot_assumptions['target_fps']}",
        f"pot_emergency_key={pot_assumptions['emergency_stop_key']}",
        f"action_keymap={action_keymap}",
        f"letta_tools={len(letta_tools)}",
        f"{kaggle_line}",
    ]
    return " ".join(msg_parts)
