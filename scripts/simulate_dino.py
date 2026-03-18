"""Quick CLI to sample Instinct Agent decisions for multiple species.

This uses the same functions that Letta tools will call (`simulate_instinct_decision`)
and prints a small grid of scenarios per species.
"""

from __future__ import annotations

import argparse
from typing import Iterable, List, Tuple

from src.letta_tools import get_species_fast_facts, simulate_instinct_decision


DEFAULT_SPECIES: Tuple[str, ...] = (
    "kto_pachyrhinosaurus",
    "kto_yangchuanosaurus",
    "allosaurus",
    "styracosaurus",
    "achillobator",
    "tylosaurus",
)


def sample_scenarios() -> List[dict]:
    """Return a small grid of scalar observation scenarios."""
    return [
        {
            "label": "calm_exploration",
            "predator_probability": 0.1,
            "prey_density": 0.2,
            "health": 0.95,
            "stamina": 0.9,
            "hunger": 0.3,
            "thirst": 0.3,
        },
        {
            "label": "thirsty_but_safe",
            "predator_probability": 0.1,
            "prey_density": 0.2,
            "health": 0.9,
            "stamina": 0.8,
            "hunger": 0.4,
            "thirst": 0.85,
        },
        {
            "label": "hungry_with_prey_nearby",
            "predator_probability": 0.2,
            "prey_density": 0.7,
            "health": 0.9,
            "stamina": 0.8,
            "hunger": 0.85,
            "thirst": 0.5,
        },
        {
            "label": "high_threat_healthy",
            "predator_probability": 0.8,
            "prey_density": 0.3,
            "health": 0.9,
            "stamina": 0.8,
            "hunger": 0.4,
            "thirst": 0.4,
        },
        {
            "label": "high_threat_low_health",
            "predator_probability": 0.85,
            "prey_density": 0.3,
            "health": 0.35,
            "stamina": 0.5,
            "hunger": 0.4,
            "thirst": 0.4,
        },
    ]


def run_for_species(species: str, scenarios: Iterable[dict]) -> None:
    """Print decisions for one species across a scenario grid."""
    facts = get_species_fast_facts(species)
    print(f"\n=== Species: {species} ===")
    if facts.get("diet"):
        print(
            f"  diet={facts['diet']} size_tier={facts['size_tier']} "
            f"threat_role={facts['threat_role']} env={facts['environment']}"
        )
    for sc in scenarios:
        result = simulate_instinct_decision(
            species=species,
            predator_probability=sc["predator_probability"],
            prey_density=sc["prey_density"],
            health=sc["health"],
            stamina=sc["stamina"],
            hunger=sc["hunger"],
            thirst=sc["thirst"],
        )
        action = result["action"]
        print(
            f"  - {sc['label']}: "
            f"pred={sc['predator_probability']:.2f} "
            f"health={sc['health']:.2f} "
            f"stam={sc['stamina']:.2f} "
            f"hunger={sc['hunger']:.2f} "
            f"thirst={sc['thirst']:.2f} -> action={action}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Simulate Instinct Agent decisions for multiple species."
    )
    parser.add_argument(
        "--species",
        nargs="*",
        default=list(DEFAULT_SPECIES),
        help="Species ids to simulate (default: a small curated set).",
    )
    args = parser.parse_args()

    scenarios = sample_scenarios()
    for sid in args.species:
        run_for_species(sid, scenarios)


if __name__ == "__main__":
    main()

