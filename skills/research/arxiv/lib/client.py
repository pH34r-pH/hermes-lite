"""ArXiv API client with defensive parsing.

Uses ``requests`` for transport and ``feedparser`` for Atom/XML parsing,
falling back to ``xml.etree.ElementTree`` when feedparser is unavailable.
"""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

try:
    import feedparser

    _HAS_FEEDPARSER = True
except Exception:  # pragma: no cover
    _HAS_FEEDPARSER = False
    import xml.etree.ElementTree as _etree  # type: ignore[import-untyped]

from .rate_limiter import ArxivRateLimiter
from .query_cache import ArxivQueryCache

logger = logging.getLogger(__name__)

_ARXIV_API_URL = "http://export.arxiv.org/api/query"


class ArxivClient:
    """Thin, defensive arXiv API client.

    Integrates rate limiting, caching, and offline-aware return paths.
    """

    def __init__(
        self,
        rate_limiter: Optional[ArxivRateLimiter] = None,
        query_cache: Optional[ArxivQueryCache] = None,
        max_retries: int = 3,
    ) -> None:
        self._rl = rate_limiter or ArxivRateLimiter()
        self._cache = query_cache or ArxivQueryCache()
        self._max_retries = max_retries
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": self._rl.user_agent()})

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def search(
        self, query: str, max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """Search arXiv and return a list of paper dicts.

        Each dict contains:
        ``arxiv_id, title, authors, abstract, categories, published,
        updated, pdf_url``.

        If the daily cap is reached, returns cached results only (may be
        empty).  On network failure, returns stale cache if available.
        """
        # 1) Check cache
        cached, stale = self._cache.get(query, max_results)
        if cached and not stale:
            return self._parse_feed(cached)

        # 2) Daily cap guard
        if self._rl.cap_reached():
            logger.warning("ArXiv daily cap reached; serving cached data only.")
            if cached:
                return self._parse_feed(cached)
            return []

        # 3) Network request with rate limiting + retries
        self._rl.wait_if_needed()
        params: Dict[str, Any] = {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": max_results,
            "sortBy": "relevance",
            "sortOrder": "descending",
        }

        last_err: Optional[Exception] = None
        for attempt in range(self._max_retries):
            try:
                resp = self._session.get(
                    _ARXIV_API_URL, params=params, timeout=30
                )
                resp.raise_for_status()
                feed_xml = resp.text
                self._cache.set(query, max_results, feed_xml)
                self._rl.record_results(max_results)
                return self._parse_feed(feed_xml)
            except requests.exceptions.HTTPError as exc:
                status = exc.response.status_code if exc.response else 0
                if status in (503, 502, 500):
                    last_err = exc
                    self._rl.backoff(attempt)
                else:
                    raise
            except (requests.exceptions.RequestException, OSError) as exc:
                last_err = exc
                self._rl.backoff(attempt)

        # 4) All retries exhausted — log malformed payload path for review
        self._log_malformed(query, params, last_err)
        if cached:
            return self._parse_feed(cached)
        return []

    # ------------------------------------------------------------------ #
    # Parsing
    # ------------------------------------------------------------------ #

    def _parse_feed(self, feed_xml: str) -> List[Dict[str, Any]]:
        if _HAS_FEEDPARSER:
            return self._parse_with_feedparser(feed_xml)
        return self._parse_with_etree(feed_xml)

    def _parse_with_feedparser(self, feed_xml: str) -> List[Dict[str, Any]]:
        parsed = feedparser.parse(feed_xml)
        results: List[Dict[str, Any]] = []
        for entry in parsed.entries:
            arxiv_id = entry.get("id", "").split("/")[-1].split("v")[0]
            pdf_url = ""
            for link in entry.get("links", []):
                if link.get("type") == "application/pdf":
                    pdf_url = link.get("href", "")
                    break
            results.append(
                {
                    "arxiv_id": arxiv_id,
                    "title": entry.get("title", "").replace("\n", " "),
                    "authors": [
                        a.get("name", "") for a in entry.get("authors", [])
                    ],
                    "abstract": entry.get("summary", "").replace("\n", " "),
                    "categories": [t.get("term", "") for t in entry.get("tags", [])],
                    "published": entry.get("published", ""),
                    "updated": entry.get("updated", ""),
                    "pdf_url": pdf_url,
                }
            )
        return results

    def _parse_with_etree(self, feed_xml: str) -> List[Dict[str, Any]]:
        ns = {
            "atom": "http://www.w3.org/2005/Atom",
            "arxiv": "http://arxiv.org/schemas/atom",
        }
        try:
            root = _etree.fromstring(feed_xml.encode("utf-8"))
        except _etree.ParseError as exc:
            logger.error("Malformed arXiv XML: %s", exc)
            return []

        results: List[Dict[str, Any]] = []
        for entry in root.findall("atom:entry", ns):
            arxiv_id_el = entry.find("atom:id", ns)
            arxiv_id = (
                (arxiv_id_el.text or "").split("/")[-1].split("v")[0]
                if arxiv_id_el is not None
                else ""
            )
            title_el = entry.find("atom:title", ns)
            title = (title_el.text or "").replace("\n", " ") if title_el is not None else ""
            summary_el = entry.find("atom:summary", ns)
            abstract = (
                (summary_el.text or "").replace("\n", " ")
                if summary_el is not None
                else ""
            )
            published_el = entry.find("atom:published", ns)
            updated_el = entry.find("atom:updated", ns)
            authors = [
                (a.find("atom:name", ns).text or "")
                for a in entry.findall("atom:author", ns)
                if a.find("atom:name", ns) is not None
            ]
            categories = [
                c.get("term", "") for c in entry.findall("atom:category", ns)
            ]
            pdf_url = ""
            for link in entry.findall("atom:link", ns):
                if link.get("type") == "application/pdf":
                    pdf_url = link.get("href", "")
                    break

            results.append(
                {
                    "arxiv_id": arxiv_id,
                    "title": title,
                    "authors": authors,
                    "abstract": abstract,
                    "categories": categories,
                    "published": published_el.text if published_el is not None else "",
                    "updated": updated_el.text if updated_el is not None else "",
                    "pdf_url": pdf_url,
                }
            )
        return results

    # ------------------------------------------------------------------ #
    # Diagnostics
    # ------------------------------------------------------------------ #

    def _log_malformed(
        self,
        query: str,
        params: Dict[str, Any],
        error: Optional[Exception],
    ) -> None:
        bad_dir = Path(
            os.path.expanduser("~/.hermes-lite/cache/arxiv/malformed")
        )
        bad_dir.mkdir(parents=True, exist_ok=True)
        stamp = time.strftime("%Y%m%d_%H%M%S")
        path = bad_dir / f"malformed_{stamp}.json"
        try:
            with path.open("w", encoding="utf-8") as fh:
                payload = {
                    "query": query,
                    "params": params,
                    "error": str(error),
                    "time": stamp,
                }
                import json

                json.dump(payload, fh, indent=2)
        except OSError:
            pass


# Re-export for type-checking convenience
__all__ = ["ArxivClient"]
