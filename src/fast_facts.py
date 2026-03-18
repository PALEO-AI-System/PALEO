"""Fast-facts lookup for dinosaur species roles.

This module stays purely logical and JSON-backed so it can be safely called
from Letta tools without any game APIs.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional


@dataclass
class SpeciesFastFacts:
  species_id: str
  diet: str
  size_tier: str
  threat_role: str
  environment: str
  notes: str


def _fast_facts_path() -> Path:
  return Path(__file__).resolve().parents[1] / "configs" / "fast_facts.json"


def _load_fast_facts() -> Dict[str, SpeciesFastFacts]:
  path = _fast_facts_path()
  if not path.exists():
    return {}
  data = json.loads(path.read_text(encoding="utf-8"))
  out: Dict[str, SpeciesFastFacts] = {}
  for sid, entry in data.items():
    out[sid] = SpeciesFastFacts(
      species_id=sid,
      diet=str(entry.get("diet", "")),
      size_tier=str(entry.get("size_tier", "")),
      threat_role=str(entry.get("threat_role", "")),
      environment=str(entry.get("environment", "")),
      notes=str(entry.get("notes", "")),
    )
  return out


_FAST_FACTS_CACHE: Dict[str, SpeciesFastFacts] = _load_fast_facts()


def get_fast_facts(species_id: str) -> Optional[SpeciesFastFacts]:
  """Return fast-facts for a normalized species id, if known."""
  key = species_id.strip().lower()
  return _FAST_FACTS_CACHE.get(key)


