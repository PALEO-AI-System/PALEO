"""Instinct Agent and Primal Mind behavior primitives."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from typing import Dict, List


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


def default_agent_state(identity: str = "dino-001") -> AgentState:
    """Return default Instinct Agent state."""
    mind = PrimalMind(
        identity=identity,
        species="allosaurus",
        life_stage="juvenile",
        current_goal="find_water",
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


def decide_instinct_action(state: AgentState) -> AgentDecision:
    """Choose a high-level action from observation + personality traits."""
    obs = state.observation
    traits = state.primal_mind.traits

    if obs.predator_probability > 0.7 and obs.health < 0.6 and traits.bravery < 0.6:
        return AgentDecision(
            action="FLEE",
            rationale="High threat + low health and low bravery.",
            confidence=0.86,
        )
    if obs.thirst > 0.75:
        return AgentDecision(
            action="SEEK_WATER",
            rationale="Thirst is the dominant survival need.",
            confidence=0.78,
        )
    if obs.hunger > 0.7 and obs.prey_density > 0.45 and traits.aggressiveness > 0.45:
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
    return decide_instinct_action(state).action


def format_thought_log(state: AgentState, action: str) -> str:
    """Return JSON thought log with visible rationale fields."""
    decision = decide_instinct_action(state)
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

