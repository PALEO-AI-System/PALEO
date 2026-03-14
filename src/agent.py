"""Agent loop stubs for per-dinosaur behavior.

These are purely structural placeholders for now; they do not call Letta
or control any real game process yet.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class AgentState:
    identity: str
    hunger: float
    threat_level: float
    recent_event: str


def default_agent_state(identity: str = "dino-001") -> AgentState:
    """Return a simple default agent state."""
    return AgentState(
        identity=identity,
        hunger=0.5,
        threat_level=0.2,
        recent_event="spawned_in_safe_area",
    )


def decide_action(state: AgentState, predictions: Dict[str, float] | None = None) -> str:
    """Return a dummy high-level action string."""
    # In the real system, predictions from the classifier would inform this.
    if state.hunger > 0.7:
        return "MOVE_TO_FOOD"
    if state.threat_level > 0.7:
        return "FLEE_TO_COVER"
    return "EXPLORE"


def format_thought_log(state: AgentState, action: str) -> str:
    """Return a short natural-language thought log."""
    return (
        f"[{state.identity}] Event={state.recent_event}; "
        f"hunger={state.hunger:.2f}, threat={state.threat_level:.2f} -> action={action}"
    )

