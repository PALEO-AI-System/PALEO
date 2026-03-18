"""Instinct Agent and Primal Mind behavior primitives."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
from typing import Any, Dict, List


@dataclass
class PersonalityTraits:
    """Compact personality schema used by Instinct Agent."""

    aggressiveness: float = 0.5
    friendliness: float = 0.5
    curiosity: float = 0.5
    bravery: float = 0.5
    morality: float = 0.5


@dataclass
class PrimalMind:
    """Memory block bundle for one dinosaur identity."""

    identity: str
    species: str
    life_stage: str
    current_goal: str
    traits: PersonalityTraits = field(default_factory=PersonalityTraits)
    recent_events: List[str] = field(default_factory=list)


@dataclass
class Observation:
    """Unified observation input for agent decisions."""

    predator_probability: float
    prey_density: float
    health: float
    stamina: float
    hunger: float
    thirst: float
    recent_event: str = "none"


@dataclass
class AgentDecision:
    """Action + human-visible rationale payload."""

    action: str
    rationale: str
    confidence: float


@dataclass
class AgentState:
    """Compatibility wrapper around Primal Mind + latest observation."""

    primal_mind: PrimalMind
    observation: Observation

    @property
    def identity(self) -> str:
        return self.primal_mind.identity

    @property
    def hunger(self) -> float:
        return self.observation.hunger

    @property
    def threat_level(self) -> float:
        return self.observation.predator_probability

    @property
    def recent_event(self) -> str:
        return self.observation.recent_event


@dataclass
class InstinctPolicy:
    """Data-driven policy knobs for a specific species/build.

    This is intentionally lightweight: it provides thresholds and action biases
    so the Instinct Agent can behave species-appropriately without hard-coding
    everything into logic branches.
    """

    policy_id: str
    species_aliases: List[str]
    thresholds: Dict[str, float]
    traits_overrides: Dict[str, float] = field(default_factory=dict)
    action_bias: Dict[str, bool] = field(default_factory=dict)
    high_level_actions: Dict[str, str] = field(default_factory=dict)


def load_instinct_policy(path: str | Path) -> InstinctPolicy:
    """Load an InstinctPolicy JSON file."""
    p = Path(path)
    data: Dict[str, Any] = json.loads(p.read_text(encoding="utf-8"))
    return InstinctPolicy(
        policy_id=str(data.get("policy_id", p.stem)),
        species_aliases=list(data.get("species_aliases", [])),
        thresholds=dict(data.get("thresholds", {})),
        traits_overrides=dict(data.get("traits_overrides", {})),
        action_bias=dict(data.get("action_bias", {})),
        high_level_actions=dict(data.get("high_level_actions", {})),
    )


def default_instinct_policies() -> List[InstinctPolicy]:
    """Return built-in policies shipped with the repo."""
    project_root = Path(__file__).resolve().parents[1]
    cfg_path = project_root / "configs" / "instinct" / "kto_pachyrhinosaurus.json"
    policies: List[InstinctPolicy] = []
    if cfg_path.exists():
        policies.append(load_instinct_policy(cfg_path))
    return policies


def policy_for_species(species: str | None) -> InstinctPolicy | None:
    """Return the best matching policy for a species string."""
    if not species:
        return None
    normalized = species.strip().lower()
    for policy in default_instinct_policies():
        aliases = {a.strip().lower() for a in policy.species_aliases}
        if normalized in aliases:
            return policy
    return None


def default_agent_state(
    identity: str = "dino-001",
    *,
    species: str = "allosaurus",
    life_stage: str = "juvenile",
    current_goal: str = "find_water",
) -> AgentState:
    """Return default Instinct Agent state."""
    mind = PrimalMind(
        identity=identity,
        species=species,
        life_stage=life_stage,
        current_goal=current_goal,
        recent_events=["spawned_in_safe_area"],
    )
    obs = Observation(
        predator_probability=0.2,
        prey_density=0.4,
        health=0.95,
        stamina=0.8,
        hunger=0.5,
        thirst=0.6,
        recent_event="spawned_in_safe_area",
    )
    return AgentState(primal_mind=mind, observation=obs)


def _apply_policy_traits(state: AgentState, policy: InstinctPolicy | None) -> None:
    if not policy:
        return
    traits = state.primal_mind.traits
    for key, value in policy.traits_overrides.items():
        if hasattr(traits, key):
            setattr(traits, key, float(value))


def decide_instinct_action(state: AgentState, policy: InstinctPolicy | None = None) -> AgentDecision:
    """Choose a high-level action from observation + personality traits."""
    _apply_policy_traits(state, policy)
    obs = state.observation
    traits = state.primal_mind.traits

    # Optional policy-driven thresholds.
    thresholds = policy.thresholds if policy else {}
    critical_health = float(thresholds.get("critical_health", 0.3))
    low_health = float(thresholds.get("low_health", 0.6))
    low_stamina = float(thresholds.get("low_stamina", 0.3))
    high_threat = float(thresholds.get("high_threat", 0.7))
    medium_threat = float(thresholds.get("medium_threat", 0.5))
    high_thirst = float(thresholds.get("high_thirst", 0.75))
    high_hunger = float(thresholds.get("high_hunger", 0.7))

    actions = policy.high_level_actions if policy else {}
    action_flee = actions.get("fallback_flee", "FLEE")
    action_hold = actions.get("hold_ground", "HOLD_POSITION")
    action_seek_water = actions.get("seek_water", "SEEK_WATER")
    action_seek_food = actions.get("seek_food", "FORAGE")
    action_call_danger = actions.get("threaten_call", "CALL_DANGER")

    prefer_hold_ground = bool(policy.action_bias.get("prefer_hold_ground_when_healthy", False)) if policy else False
    prefer_call_for_help = bool(policy.action_bias.get("prefer_call_for_help_when_critical", False)) if policy else False
    avoid_chasing_low_stam = bool(policy.action_bias.get("avoid_chasing_when_low_stamina", False)) if policy else False

    if obs.predator_probability > high_threat and obs.health < low_health and traits.bravery < 0.6:
        return AgentDecision(
            action=action_flee,
            rationale="High threat + low health and low bravery.",
            confidence=0.86,
        )

    # Pachyrhino-like tank behavior: hold ground and warn more, flee later.
    if prefer_hold_ground and obs.predator_probability > medium_threat and obs.health > low_health and obs.stamina > low_stamina:
        return AgentDecision(
            action=action_hold,
            rationale="Medium threat but healthy; hold ground and deter rather than panic-flee.",
            confidence=0.7,
        )

    if prefer_call_for_help and obs.predator_probability > high_threat and obs.health <= critical_health:
        return AgentDecision(
            action=action_call_danger,
            rationale="Critical health under high threat; signal danger/help while repositioning.",
            confidence=0.74,
        )

    if obs.thirst > high_thirst:
        return AgentDecision(
            action=action_seek_water,
            rationale="Thirst is the dominant survival need.",
            confidence=0.78,
        )
    if obs.hunger > high_hunger:
        return AgentDecision(
            action=action_seek_food,
            rationale="Hunger is high; prioritize safe foraging.",
            confidence=0.7,
        )

    if obs.hunger > 0.7 and obs.prey_density > 0.45 and traits.aggressiveness > 0.45 and not avoid_chasing_low_stam:
        return AgentDecision(
            action="HUNT",
            rationale="Hunger is high, prey is available, aggressiveness allows pursuit.",
            confidence=0.74,
        )
    if traits.curiosity > 0.65:
        return AgentDecision(
            action="EXPLORE",
            rationale="No immediate survival pressure; curiosity drives exploration.",
            confidence=0.62,
        )
    return AgentDecision(
        action="HOLD_POSITION",
        rationale="No strong trigger; conserve stamina and observe.",
        confidence=0.58,
    )


def decide_action(state: AgentState, predictions: Dict[str, float] | None = None) -> str:
    """Compatibility adapter returning only action string."""
    if predictions:
        state.observation.predator_probability = predictions.get(
            "predator_probability", state.observation.predator_probability
        )
        state.observation.prey_density = predictions.get(
            "prey_density", state.observation.prey_density
        )
    policy = policy_for_species(state.primal_mind.species)
    return decide_instinct_action(state, policy=policy).action


def format_thought_log(state: AgentState, action: str) -> str:
    """Return JSON thought log with visible rationale fields."""
    policy = policy_for_species(state.primal_mind.species)
    decision = decide_instinct_action(state, policy=policy)
    if decision.action != action:
        decision = AgentDecision(
            action=action,
            rationale=decision.rationale,
            confidence=decision.confidence,
        )
    payload = {
        "identity": state.identity,
        "primal_mind": asdict(state.primal_mind),
        "observation": asdict(state.observation),
        "decision": asdict(decision),
    }
    return json.dumps(payload, separators=(",", ":"), sort_keys=True)

