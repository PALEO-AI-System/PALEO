"""Ingest Path of Titans web pages into a local RAG corpus.

Builds `data/processed/wiki_pages.jsonl` from selected PoT wiki/resource URLs.
Then optionally rebuilds the local index used by `src/wiki_rag.py`.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable, List, Set
from urllib.parse import urlparse

import requests

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.wiki_rag import build_rag_index

URL_RE = re.compile(r"https?://[^\s`<>\)\]\"]+")
ALLOWED_HOST_KEYS = ("pathoftitans", "gsh-servers")


class _VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._skip = 0
        self._parts: List[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:  # type: ignore[override]
        if tag in {"script", "style", "noscript"}:
            self._skip += 1
        if tag in {"p", "li", "h1", "h2", "h3", "h4", "article", "section", "br"}:
            self._parts.append("\n")

    def handle_endtag(self, tag: str) -> None:  # type: ignore[override]
        if tag in {"script", "style", "noscript"} and self._skip > 0:
            self._skip -= 1
        if tag in {"p", "li", "h1", "h2", "h3", "h4", "article", "section"}:
            self._parts.append("\n")

    def handle_data(self, data: str) -> None:  # type: ignore[override]
        if self._skip:
            return
        s = " ".join(unescape(data).split())
        if s:
            self._parts.append(s + " ")

    def text(self) -> str:
        text = "".join(self._parts)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()


def _extract_urls(path: Path) -> List[str]:
    if not path.exists():
        return []
    raw = path.read_text(encoding="utf-8", errors="ignore")
    return URL_RE.findall(raw)


def _is_pot_url(url: str) -> bool:
    host = urlparse(url).netloc.lower()
    return any(k in host for k in ALLOWED_HOST_KEYS)


def discover_urls(input_files: Iterable[Path]) -> List[str]:
    seen: Set[str] = set()
    out: List[str] = []
    for p in input_files:
        for u in _extract_urls(p):
            clean = u.strip().rstrip(".,);")
            if not clean.startswith("http"):
                continue
            if not _is_pot_url(clean):
                continue
            if clean in seen:
                continue
            seen.add(clean)
            out.append(clean)
    return out


def fetch_page(session: requests.Session, url: str, timeout_sec: float) -> dict:
    try:
        r = session.get(url, timeout=timeout_sec)
        r.raise_for_status()
        html = r.text
        title_match = re.search(r"<title[^>]*>(.*?)</title>", html, flags=re.I | re.S)
        title = " ".join(unescape(title_match.group(1)).split()) if title_match else url
        parser = _VisibleTextParser()
        parser.feed(html)
        text = parser.text()
        return {
            "url": url,
            "title": title[:220],
            "text": text[:20000],
            "status": "ok",
            "http_status": r.status_code,
            "fetched_at": int(time.time()),
        }
    except Exception as e:  # broad on purpose: keep ingestion robust across sites
        return {
            "url": url,
            "title": url,
            "text": "",
            "status": "error",
            "error": str(e),
            "fetched_at": int(time.time()),
        }


def main() -> None:
    p = argparse.ArgumentParser(description="Ingest PoT web pages into local RAG corpus.")
    p.add_argument(
        "--input-files",
        nargs="*",
        default=[
            "docs/pot_web_resources.md",
            "docs/wiki_snippets.md",
            "docs/paleo_brainstorming.md",
        ],
        help="Markdown/text files to scan for URLs.",
    )
    p.add_argument(
        "--output",
        default="data/processed/wiki_pages.jsonl",
        help="Output JSONL corpus path.",
    )
    p.add_argument("--timeout-sec", type=float, default=12.0)
    p.add_argument("--rebuild-index", action="store_true", help="Rebuild wiki_rag index after ingestion.")
    args = p.parse_args()

    files = [PROJECT_ROOT / f for f in args.input_files]
    urls = discover_urls(files)
    if not urls:
        raise SystemExit("No PoT wiki URLs found in input files.")

    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "PALEO-RAG-Ingest/1.0 (+local-dev)",
            "Accept-Language": "en-US,en;q=0.8",
        }
    )

    records: List[dict] = []
    ok = 0
    for i, u in enumerate(urls, start=1):
        rec = fetch_page(session, u, timeout_sec=args.timeout_sec)
        if rec["status"] == "ok" and rec["text"]:
            ok += 1
        records.append(rec)
        print(f"[{i}/{len(urls)}] {rec['status']}: {u}")

    out_path = PROJECT_ROOT / args.output
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=True) + "\n")

    print(f"Wrote {len(records)} records to {out_path.as_posix()}")
    print(f"Successful pages with text: {ok}")

    if args.rebuild_index:
        idx = build_rag_index(save=True)
        print(f"Rebuilt wiki index with {len(idx.chunks)} chunks.")


if __name__ == "__main__":
    main()
