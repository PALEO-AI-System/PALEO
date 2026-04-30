from __future__ import annotations

import unittest

from src.wiki_rag import build_rag_chunks, query_snippets


class TestWikiRag(unittest.TestCase):
    def test_build_chunks_non_empty(self) -> None:
        chunks = build_rag_chunks()
        self.assertGreater(len(chunks), 0)
        self.assertTrue(all(c.title for c in chunks))

    def test_query_returns_relevant_text(self) -> None:
        hits = query_snippets("bleed fracture stamina", top_k=2)
        self.assertGreaterEqual(len(hits), 1)
        joined = "\n".join(hits).lower()
        self.assertTrue(
            ("bleed" in joined)
            or ("fracture" in joined)
            or ("stamina" in joined)
        )


if __name__ == "__main__":
    unittest.main()
