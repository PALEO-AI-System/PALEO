# PALEO Lexicon

## Core concepts

### Instinct Agent

A per-dinosaur control agent that:
- Perceives game and environment state (e.g., visual cues, classifier outputs, basic telemetry).
- Uses trained instinct models plus rules/RL-style policies to choose behavior.
- Outputs high-level actions or behavior modes (e.g., flee, forage, explore, idle) that the game loop translates into controls.

### Primal Mind

The structured memory inside an Instinct Agent, implemented as:
- Long-term, structured memory blocks (e.g., Letta memories for personality traits, identity, standing goals, and key past events).
- Short-term buffers for recent experiences and context needed for the next few decisions.

The Primal Mind captures who this dinosaur is, what it wants, and what it has recently experienced, so the Instinct Agent can make consistent, explainable decisions over time.

