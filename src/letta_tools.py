"""Letta tool contracts and local stub implementations for PALEO."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict, List

from .agent import PersonalityTraits
from .config import LettaConfig, default_letta_config
from .data import DatasetRecord


@dataclass
class ToolSpec:
    """Structured tool contract for Letta orchestration."""

    name: str
    description: str
    input_schema: Dict[str, str]
    output_schema: Dict[str, str]


def get_letta_tool_specs() -> List[ToolSpec]:
    """Return required PALEO tool surfaces for Letta."""
    return [
        ToolSpec(
            name="get_dataset_stats",
            description="Return dataset and split counts from manifest.",
            input_schema={"manifest_path": "str"},
            output_schema={
                "num_records": "int",
                "splits": "dict",
                "num_predator": "int",
            },
        ),
        ToolSpec(
            name="train_model",
            description="Launch baseline training with a config name.",
            input_schema={"model_name": "str", "epochs": "int"},
            output_schema={"run_id": "str", "metrics_path": "str"},
        ),
        ToolSpec(
            name="evaluate_model",
            description="Evaluate a trained run and return key metrics.",
            input_schema={"run_id": "str"},
            output_schema={"accuracy": "float", "macro_f1": "float"},
        ),
        ToolSpec(
            name="run_pot_agent",
            description="Run short PoT session in advisor or control mode.",
            input_schema={"duration_sec": "int", "mode": "str"},
            output_schema={"status": "str", "log_path": "str"},
        ),
        ToolSpec(
            name="query_pot_wiki",
            description="Retrieve local RAG snippets about PoT species/mechanics.",
            input_schema={"query": "str"},
            output_schema={"snippets": "list[str]"},
        ),
        ToolSpec(
            name="set_personality_traits",
            description="Set per-dinosaur Primal Mind traits.",
            input_schema={
                "dino_id": "str",
                "aggressiveness": "float",
                "friendliness": "float",
                "curiosity": "float",
                "bravery": "float",
                "morality": "float",
            },
            output_schema={"status": "str"},
        ),
    ]


def get_dataset_stats(records: List[DatasetRecord]) -> Dict[str, object]:
    """Tool stub: compute small dataset stats from loaded records."""
    splits: Dict[str, int] = {}
    predators = 0
    for rec in records:
        splits[rec.split] = splits.get(rec.split, 0) + 1
        predators += rec.predator_label
    return {
        "num_records": len(records),
        "splits": splits,
        "num_predator": predators,
    }


def query_pot_wiki(query: str) -> Dict[str, List[str]]:
    """Tool stub: replace with vector-RAG retrieval in a later phase."""
    lower = query.lower()
    snippets = []
    if "stamina" in lower:
        snippets.append("Stamina affects sprinting and combat disengage decisions.")
    if "juvenile" in lower:
        snippets.append("Juveniles should avoid high-threat zones and conserve stamina.")
    if not snippets:
        snippets.append("No indexed snippet yet; integrate local wiki RAG index.")
    return {"snippets": snippets}


def set_personality_traits(dino_id: str, traits: PersonalityTraits) -> Dict[str, str]:
    """Tool stub: in production this writes to Letta memory blocks."""
    _ = dino_id
    _ = traits
    return {"status": "ok"}


def letta_config_summary(config: LettaConfig | None = None) -> Dict[str, object]:
    cfg = config or default_letta_config()
    return asdict(cfg)
