"""Local RAG retrieval over curated wiki snippets.

This module builds a lightweight vector index from ``docs/wiki_snippets.md``
using chunked markdown sections + TF-IDF embeddings + cosine ranking.
"""

from __future__ import annotations

import pickle
import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


@dataclass
class WikiSnippet:
    title: str
    lines: List[str]


@dataclass
class WikiChunk:
    chunk_id: str
    title: str
    text: str
    source: str


@dataclass
class WikiRagIndex:
    chunks: List[WikiChunk]
    vectorizer: TfidfVectorizer
    matrix: object

_INDEX_CACHE: WikiRagIndex | None = None


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _snippets_path() -> Path:
    return Path(__file__).resolve().parents[1] / "docs" / "wiki_snippets.md"


def _index_path() -> Path:
    return _repo_root() / "data" / "processed" / "wiki_rag_index.pkl"


def _pages_corpus_path() -> Path:
    return _repo_root() / "data" / "processed" / "wiki_pages.jsonl"


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


def _clean_lines(lines: Sequence[str]) -> List[str]:
    out: List[str] = []
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        if line.startswith("- "):
            line = line[2:].strip()
        out.append(line)
    return out


def _load_web_docs() -> List[WikiChunk]:
    path = _pages_corpus_path()
    if not path.exists():
        return []
    out: List[WikiChunk] = []
    for idx, raw in enumerate(path.read_text(encoding="utf-8").splitlines()):
        line = raw.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        title = str(rec.get("title", "")).strip()
        text = str(rec.get("text", "")).strip()
        source = str(rec.get("url", rec.get("source", "web"))).strip()
        if not title or not text:
            continue
        out.append(
            WikiChunk(
                chunk_id=f"web-{idx}",
                title=title,
                text=text,
                source=source,
            )
        )
    return out


def _chunk_text(text: str, max_chars: int = 480, overlap_chars: int = 100) -> List[str]:
    if len(text) <= max_chars:
        return [text]
    chunks: List[str] = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        if end < len(text):
            cut = text.rfind(". ", start, end)
            if cut > start + 80:
                end = cut + 1
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        next_start = max(0, end - overlap_chars)
        if next_start <= start:
            # Ensure forward progress even when sentence-aware cuts are short.
            next_start = min(len(text), start + max(1, max_chars - overlap_chars))
        start = next_start
    return chunks


def build_rag_chunks(max_chunk_chars: int = 480, overlap_chars: int = 100) -> List[WikiChunk]:
    snippets = _load_snippets()
    chunks: List[WikiChunk] = []
    for sn_idx, snippet in enumerate(snippets):
        body_lines = _clean_lines(snippet.lines)
        if not body_lines:
            continue
        merged = "\n".join(body_lines)
        parts = _chunk_text(merged, max_chars=max_chunk_chars, overlap_chars=overlap_chars)
        for part_idx, part in enumerate(parts):
            chunks.append(
                WikiChunk(
                    chunk_id=f"{sn_idx}-{part_idx}",
                    title=snippet.title,
                    text=part,
                    source="docs/wiki_snippets.md",
                )
            )
    for doc_idx, web_doc in enumerate(_load_web_docs()):
        parts = _chunk_text(web_doc.text, max_chars=max_chunk_chars, overlap_chars=overlap_chars)
        for part_idx, part in enumerate(parts):
            chunks.append(
                WikiChunk(
                    chunk_id=f"{web_doc.chunk_id}-{doc_idx}-{part_idx}",
                    title=web_doc.title,
                    text=part,
                    source=web_doc.source,
                )
            )
    return chunks


def build_rag_index(
    *,
    save: bool = True,
    max_chunk_chars: int = 480,
    overlap_chars: int = 100,
) -> WikiRagIndex:
    chunks = build_rag_chunks(max_chunk_chars=max_chunk_chars, overlap_chars=overlap_chars)
    docs = [f"{c.title}\n{c.text}" for c in chunks] or ["placeholder"]
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), lowercase=True, min_df=1)
    matrix = vectorizer.fit_transform(docs)
    idx = WikiRagIndex(chunks=chunks, vectorizer=vectorizer, matrix=matrix)
    if save:
        out = _index_path()
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("wb") as f:
            pickle.dump(idx, f)
    return idx


def load_rag_index() -> WikiRagIndex:
    global _INDEX_CACHE
    if _INDEX_CACHE is not None:
        return _INDEX_CACHE
    p = _index_path()
    if p.exists():
        with p.open("rb") as f:
            _INDEX_CACHE = pickle.load(f)
            return _INDEX_CACHE
    _INDEX_CACHE = build_rag_index(save=False)
    return _INDEX_CACHE


def _render_chunk(chunk: WikiChunk, score: float) -> str:
    pct = int(round(max(0.0, min(1.0, float(score))) * 100.0))
    return f"{chunk.title} (score={pct}%)\n{chunk.text}\n[source: {chunk.source}]"


def query_snippets(query: str, top_k: int = 3) -> List[str]:
    """Return up to top_k snippet chunks ranked by vector similarity."""
    if not query.strip():
        return ["Empty query; provide species/mechanic terms."]
    idx = load_rag_index()
    if not idx.chunks:
        return ["No wiki snippets loaded yet. Populate docs/wiki_snippets.md first."]
    q_vec = idx.vectorizer.transform([query])
    sims = cosine_similarity(q_vec, idx.matrix).ravel()
    if sims.size == 0:
        return ["No matching snippet yet; extend docs/wiki_snippets.md for better coverage."]
    order = np.argsort(-sims)
    out: List[str] = []
    for i in order[: max(1, top_k)]:
        if float(sims[i]) <= 0:
            continue
        out.append(_render_chunk(idx.chunks[int(i)], float(sims[i])))
    if not out:
        return ["No matching snippet yet; extend docs/wiki_snippets.md for better coverage."]
    return out
