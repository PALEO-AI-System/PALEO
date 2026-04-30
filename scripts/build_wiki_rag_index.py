"""Build local wiki RAG index for PALEO."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.wiki_rag import build_rag_chunks, build_rag_index


def main() -> None:
    p = argparse.ArgumentParser(description="Build local TF-IDF wiki RAG index.")
    p.add_argument("--max-chars", type=int, default=480, help="Max chars per chunk.")
    p.add_argument("--overlap-chars", type=int, default=100, help="Chunk overlap chars.")
    args = p.parse_args()

    chunks = build_rag_chunks(max_chunk_chars=args.max_chars, overlap_chars=args.overlap_chars)
    build_rag_index(
        save=True,
        max_chunk_chars=args.max_chars,
        overlap_chars=args.overlap_chars,
    )
    print(f"Built wiki RAG index with {len(chunks)} chunks.")
    print("Saved to data/processed/wiki_rag_index.pkl")


if __name__ == "__main__":
    main()
