"""Tiny local RAG-style lookup over curated wiki snippets.

This does *not* scrape the web. It only reads docs/wiki_snippets.md and
performs simple keyword scoring to pick relevant snippets.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple


@dataclass
class WikiSnippet:
    title: str
    lines: List[str]


def _snippets_path() -> Path:
    return Path(__file__).resolve().parents[1] / "docs" / "wiki_snippets.md"


def _load_snippets() -> List[WikiSnippet]:
    path = _snippets_path()
    if not path.exists():
        return []
    raw = path.read_text(encoding="utf-8").splitlines()
    snippets: List[WikiSnippet] = []
    current_title = ""
    current_lines: List[str] = []
    for line in raw:
        if line.startswith("### "):
            # flush previous
            if current_title:
                snippets.append(WikiSnippet(title=current_title, lines=current_lines))
            current_title = line[4:].strip()
            current_lines = []
        elif current_title:
            current_lines.append(line)
    if current_title:
        snippets.append(WikiSnippet(title=current_title, lines=current_lines))
    return snippets


_SNIPPETS: List[WikiSnippet] = _load_snippets()


def query_snippets(query: str, top_k: int = 3) -> List[str]:
    """Return up to top_k snippet texts ranked by simple keyword overlap."""
    if not _SNIPPETS:
        return ["No wiki snippets loaded yet. Populate docs/wiki_snippets.md first."]
    q = query.lower()
    q_terms = {t for t in q.replace(",", " ").split() if t}
    scored: List[Tuple[float, WikiSnippet]] = []
    for sn in _SNIPPETS:
        text = (sn.title + " " + " ".join(sn.lines)).lower()
        score = sum(1.0 for t in q_terms if t in text)
        if score > 0:
            scored.append((score, sn))
    if not scored:
        return ["No matching snippet yet; extend docs/wiki_snippets.md for better coverage."]
    scored.sort(key=lambda x: x[0], reverse=True)
    out: List[str] = []
    for _, sn in scored[:top_k]:
        out.append(sn.title + "\n" + "\n".join(sn.lines))
    return out


