"""Letta tool contracts and local stub implementations for PALEO."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List

from .agent import (
    PersonalityTraits,
    AgentState,
    AgentDecision,
    decide_action,
    decide_instinct_action,
    format_thought_log,
    policy_for_species,
)
from .config import LettaConfig, default_letta_config, default_pot_config
from .data import DatasetRecord
from .fast_facts import get_fast_facts
from .wiki_rag import query_snippets
from .kaggle_ingest import KAGGLE_PIPELINE_ROW_COUNT_MAX_FILE_BYTES, summarize_all_kaggle
from .letta_api import request_letta_decision


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
            name="get_kaggle_local_inventory",
            description=(
                "Inventory CSV files under data/raw/kaggle/ (columns + optional row counts; "
                "skips full row scan for very large files)."
            ),
            input_schema={"use_full_row_count": "bool"},
            output_schema={"csv_files": "int", "files": "list[dict]"},
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


def get_kaggle_local_inventory(use_full_row_count: bool = False) -> Dict[str, object]:
    """Tool: list local Kaggle CSVs (no download)."""
    threshold = None if use_full_row_count else KAGGLE_PIPELINE_ROW_COUNT_MAX_FILE_BYTES
    summaries = summarize_all_kaggle(row_count_max_file_bytes=threshold)
    files: List[Dict[str, object]] = []
    for s in summaries:
        files.append(
            {
                "path": s["path"],
                "name": Path(s["path"]).name,
                "num_columns": s["num_columns"],
                "num_rows": s["num_rows"],
                "row_count_skipped": s.get("row_count_skipped", False),
                "columns_head": s["columns"][:8],
            }
        )
    return {"csv_files": len(files), "files": files}


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


def decide_with_brain(
    *,
    brain: str,
    species: str,
    predator_probability: float,
    prey_density: float,
    health: float,
    stamina: float,
    hunger: float,
    thirst: float,
    recent_events: List[str] | None = None,
    model_predator_probability: float | None = None,
    letta_api_key: str | None = None,
    letta_base_url: str | None = None,
    letta_agent_id: str | None = None,
) -> Dict[str, str]:
    allowed_actions = set(default_pot_config().keymap.keys()) | set(default_pot_config().mouse_clickmap.keys())
    def _safe_action(raw: str) -> str:
        a = (raw or "").strip().upper()
        return a if a in allowed_actions else "HOLD_POSITION"

    """Perceive-think-remember-decide-act compatible decision helper.

    Supported brains:
    - ``simulate``: existing offline simulator path.
    - ``local-rules``: local Instinct policy over scalar observations.
    - ``local-model``: local Instinct policy using model-updated threat when provided.
    - ``letta-api``: placeholder integration mode; falls back to local-rules if no key.
    """
    brain = (brain or "simulate").strip().lower()
    if brain == "simulate":
        return simulate_instinct_decision(
            species=species,
            predator_probability=predator_probability,
            prey_density=prey_density,
            health=health,
            stamina=stamina,
            hunger=hunger,
            thirst=thirst,
        )

    recent = list(recent_events or [])
    obs_pred = float(predator_probability)
    if brain == "local-model" and model_predator_probability is not None:
        obs_pred = max(0.0, min(1.0, float(model_predator_probability)))

    # Robust offline perception fusion: prioritize worst-case signals and stabilize.
    pressure = max(
        obs_pred,
        min(1.0, hunger * 0.85 + thirst * 0.6),
        1.0 - max(0.0, min(1.0, health)),
    )

    from .agent import PrimalMind, Observation  # local import to avoid cycles

    state = AgentState(
        primal_mind=PrimalMind(
            identity="local-dino",
            species=species,
            life_stage="adult",
            current_goal="survive_and_progress",
            recent_events=recent[-8:],
        ),
        observation=Observation(
            predator_probability=max(obs_pred, pressure * 0.75),
            prey_density=prey_density,
            health=health,
            stamina=stamina,
            hunger=hunger,
            thirst=thirst,
            recent_event=recent[-1] if recent else "none",
        ),
    )
    policy = policy_for_species(species)
    decision: AgentDecision = decide_instinct_action(state, policy=policy)

    if pressure > 0.85 and health < 0.55:
        decision = AgentDecision(
            action="FLEE",
            rationale="Safety override: extreme pressure with vulnerable health.",
            confidence=0.9,
        )
    elif stamina < 0.2 and decision.action in {"HUNT", "EXPLORE"}:
        decision = AgentDecision(
            action="HOLD_POSITION",
            rationale="Low stamina override: hold to avoid forced overcommit.",
            confidence=max(0.6, decision.confidence),
        )

    key_present = bool(letta_api_key or os.getenv("LETTA_API_KEY"))
    letta_mode = "none"
    if brain == "letta-api":
        base_url = (letta_base_url or os.getenv("LETTA_BASE_URL") or "").strip()
        agent_id = (letta_agent_id or os.getenv("LETTA_AGENT_ID") or "").strip()
        if key_present and base_url and agent_id:
            try:
                letta_resp = request_letta_decision(
                    base_url=base_url,
                    api_key=letta_api_key or os.getenv("LETTA_API_KEY", ""),
                    agent_id=agent_id,
                    payload={
                        "species": species,
                        "observation": asdict(state.observation),
                        "recent_events": recent[-8:],
                        "suggested_local_decision": asdict(decision),
                    },
                )
                decision = AgentDecision(
                    action=_safe_action(str(letta_resp.get("action") or decision.action)),
                    rationale="Decision from Letta agent API.",
                    confidence=0.7,
                )
                letta_mode = f"api_ok:{letta_resp.get('endpoint','')}"
            except Exception as exc:
                letta_mode = f"api_error_fallback_local_rules:{exc}"
        else:
            letta_mode = "missing_key_or_base_or_agent_fallback_local_rules"
            brain = "local-rules"

    thought_payload = {
        "loop": {
            "perceive": {
                "species": species,
                "obs": asdict(state.observation),
                "model_predator_probability": model_predator_probability,
            },
            "think": {
                "brain": brain,
                "policy_id": policy.policy_id if policy else "",
                "letta_mode": letta_mode,
                "pressure": round(pressure, 4),
            },
            "remember": {
                "recent_events": recent[-8:],
                "memory_backend": "local_runtime",
            },
            "decide": asdict(decision),
            "act": {
                "action": decision.action,
                "integration_note": "Action maps via ActionMapper/SafeInputController in PoT loop.",
            },
        },
    }
    return {
        "action": _safe_action(decision.action),
        "thought_log": json.dumps(thought_payload, separators=(",", ":"), sort_keys=True),
    }


def letta_config_summary(config: LettaConfig | None = None) -> Dict[str, object]:
    cfg = config or default_letta_config()
    return asdict(cfg)
