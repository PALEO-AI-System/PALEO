"""Letta tool contracts and local stub implementations for PALEO."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict, List

from .agent import PersonalityTraits, AgentState, decide_action, format_thought_log
from .config import LettaConfig, default_letta_config
from .data import DatasetRecord
from .fast_facts import get_fast_facts
from .wiki_rag import query_snippets


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
        ToolSpec(
            name="get_species_fast_facts",
            description="Return fast-facts (diet, size, threat role) for a species id.",
            input_schema={"species_id": "str"},
            output_schema={
                "diet": "str",
                "size_tier": "str",
                "threat_role": "str",
                "environment": "str",
                "notes": "str",
            },
        ),
        ToolSpec(
            name="simulate_instinct_decision",
            description="Run a single instinct decision for a species given scalar observation inputs.",
            input_schema={
                "species": "str",
                "predator_probability": "float",
                "prey_density": "float",
                "health": "float",
                "stamina": "float",
                "hunger": "float",
                "thirst": "float",
            },
            output_schema={
                "action": "str",
                "thought_log": "str",
            },
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
    """Tool: local wiki-snippet lookup over curated docs/wiki_snippets.md."""
    snippets = query_snippets(query, top_k=3)
    return {"snippets": snippets}


def set_personality_traits(dino_id: str, traits: PersonalityTraits) -> Dict[str, str]:
    """Tool stub: in production this writes to Letta memory blocks."""
    _ = dino_id
    _ = traits
    return {"status": "ok"}


def get_species_fast_facts(species_id: str) -> Dict[str, str]:
    """Tool: surface fast-facts for Letta or other callers."""
    ff = get_fast_facts(species_id)
    if not ff:
        return {
            "diet": "",
            "size_tier": "",
            "threat_role": "",
            "environment": "",
            "notes": "",
        }
    return {
        "diet": ff.diet,
        "size_tier": ff.size_tier,
        "threat_role": ff.threat_role,
        "environment": ff.environment,
        "notes": ff.notes,
    }


def simulate_instinct_decision(
    species: str,
    predator_probability: float,
    prey_density: float,
    health: float,
    stamina: float,
    hunger: float,
    thirst: float,
) -> Dict[str, str]:
    """Tool: offline 'what would this dino do?' single-step sim.

    Purely logical: constructs an AgentState in memory and returns the chosen
    high-level action plus a JSON thought log, suitable for Letta tools.
    """
    state = AgentState(
        primal_mind=PersonalityTraits().__class__(  # reuse class, but identity/species separate
        ),  # placeholder; overridden below
        observation=None,  # type: ignore[arg-type]
    )
    # Rebuild PrimalMind/Observation explicitly to keep dependencies minimal.
    from .agent import PrimalMind, Observation  # local import to avoid cycles

    state.primal_mind = PrimalMind(
        identity="sim-dino",
        species=species,
        life_stage="adult",
        current_goal="unspecified",
    )
    state.observation = Observation(
        predator_probability=predator_probability,
        prey_density=prey_density,
        health=health,
        stamina=stamina,
        hunger=hunger,
        thirst=thirst,
        recent_event="simulated",
    )
    action = decide_action(state)
    thought = format_thought_log(state, action)
    return {"action": action, "thought_log": thought}


def letta_config_summary(config: LettaConfig | None = None) -> Dict[str, object]:
    cfg = config or default_letta_config()
    return asdict(cfg)
