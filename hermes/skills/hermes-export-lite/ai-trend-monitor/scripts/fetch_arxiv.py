#!/usr/bin/env python3
"""Fetch recent AI papers from arXiv API with multi-fallback.

Fallback chain:
  1. export.arxiv.org (direct)
  2. export.arxiv.org via HTTP proxy 127.0.0.1:3128
  3. Semantic Scholar API (api.semanticscholar.org)
"""

import json
import sys
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

ARXIV_API = "http://export.arxiv.org/api/query"
SEMANTIC_SCHOLAR_API = "https://api.semanticscholar.org/graph/v1/paper/search"
PROXY_URL = "http://127.0.0.1:3128"
TIMEOUT = 20

# AI-related categories
CATEGORIES = ["cs.AI", "cs.CL", "cs.LG", "cs.CV", "cs.MA"]


def _parse_arxiv_xml(xml_text):
    """Parse Atom feed from arXiv API."""
    ns = {
        "atom": "http://www.w3.org/2005/Atom",
        "arxiv": "http://arxiv.org/schemas/atom",
    }
    root = ET.fromstring(xml_text)
    papers = []
    for entry in root.findall("atom:entry", ns):
        title = entry.findtext("atom:title", "", ns).strip().replace("\n", " ")
        summary = entry.findtext("atom:summary", "", ns).strip().replace("\n", " ")
        published = entry.findtext("atom:published", "", ns)

        authors = []
        for author in entry.findall("atom:author", ns):
            name = author.findtext("atom:name", "", ns)
            if name:
                authors.append(name)

        categories = []
        for cat in entry.findall("atom:category", ns):
            term = cat.get("term", "")
            if term:
                categories.append(term)

        link = ""
        for l in entry.findall("atom:link", ns):
            if l.get("type") == "text/html":
                link = l.get("href", "")
                break
        if not link:
            arxiv_id = entry.findtext("atom:id", "", ns)
            link = arxiv_id

        papers.append({
            "title": title,
            "authors": authors[:5],
            "summary": summary[:400],
            "categories": categories,
            "published": published,
            "link": link,
        })
    return papers


def _fetch_arxiv_direct(max_results=50):
    """Fallback 1: Direct request to export.arxiv.org."""
    cat_query = " OR ".join(f"cat:{c}" for c in CATEGORIES)
    query = f"({cat_query})"
    params = {
        "search_query": query,
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    url = f"{ARXIV_API}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={
        "User-Agent": "AITrendMonitor/1.0"
    })
    resp = urllib.request.urlopen(req, timeout=TIMEOUT)
    xml_text = resp.read().decode("utf-8")
    return _parse_arxiv_xml(xml_text)


def _fetch_arxiv_proxy(max_results=50):
    """Fallback 2: Via HTTP proxy 127.0.0.1:3128."""
    cat_query = " OR ".join(f"cat:{c}" for c in CATEGORIES)
    query = f"({cat_query})"
    params = {
        "search_query": query,
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    url = f"{ARXIV_API}?{urllib.parse.urlencode(params)}"
    proxy_handler = urllib.request.ProxyHandler({
        "http": PROXY_URL,
        "https": PROXY_URL,
    })
    opener = urllib.request.build_opener(proxy_handler)
    req = urllib.request.Request(url, headers={
        "User-Agent": "AITrendMonitor/1.0"
    })
    resp = opener.open(req, timeout=TIMEOUT)
    xml_text = resp.read().decode("utf-8")
    return _parse_arxiv_xml(xml_text)


def _fetch_semantic_scholar(max_results=50):
    """Fallback 3: Semantic Scholar API for recent AI papers."""
    queries = [
        "large language model",
        "artificial intelligence agent",
        "machine learning",
        "deep learning transformer",
        "AI reasoning",
    ]
    all_papers = []
    seen_titles = set()

    year = datetime.utcnow().year

    for q in queries:
        if len(all_papers) >= max_results:
            break
        params = {
            "query": q,
            "limit": min(20, max_results - len(all_papers)),
            "fields": "title,authors,abstract,year,externalIds,publicationDate,url",
            "year": f"{year}-",
            "sort": "publicationDate:desc",
        }
        url = f"{SEMANTIC_SCHOLAR_API}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers={
            "User-Agent": "AITrendMonitor/1.0"
        })
        try:
            resp = urllib.request.urlopen(req, timeout=TIMEOUT)
            data = json.loads(resp.read().decode("utf-8"))
            for paper in data.get("data", []):
                title = (paper.get("title") or "").strip()
                if not title or title.lower() in seen_titles:
                    continue
                seen_titles.add(title.lower())

                authors = [a.get("name", "") for a in (paper.get("authors") or [])[:5]]
                abstract = (paper.get("abstract") or "")[:400]
                pub_date = paper.get("publicationDate") or ""

                ext_ids = paper.get("externalIds") or {}
                arxiv_id = ext_ids.get("ArXiv")
                if arxiv_id:
                    link = f"https://arxiv.org/abs/{arxiv_id}"
                elif paper.get("url"):
                    link = paper["url"]
                else:
                    link = f"https://api.semanticscholar.org/graph/v1/paper/{paper.get('paperId', '')}"

                all_papers.append({
                    "title": title,
                    "authors": authors,
                    "summary": abstract,
                    "categories": [],
                    "published": pub_date,
                    "link": link,
                })
        except Exception:
            continue

    return all_papers[:max_results]


def fetch_arxiv(categories=None, max_results=50, days=1):
    """Fetch recent papers with multi-fallback."""
    methods = [
        ("arxiv_direct", _fetch_arxiv_direct),
        ("arxiv_proxy", _fetch_arxiv_proxy),
        ("semantic_scholar", _fetch_semantic_scholar),
    ]

    last_error = None
    for method_name, method_fn in methods:
        try:
            papers = method_fn(max_results=max_results)
            if papers:
                return {
                    "papers": papers,
                    "fetched_at": datetime.utcnow().isoformat(),
                    "total": len(papers),
                    "source": method_name,
                }
        except Exception as e:
            last_error = f"{method_name}: {e}"
            print(f"  ⚠ {method_name} failed: {e}", file=sys.stderr, flush=True)
            continue

    return {
        "papers": [],
        "fetched_at": datetime.utcnow().isoformat(),
        "total": 0,
        "source": "none",
        "error": f"All methods failed. Last: {last_error}",
    }


if __name__ == "__main__":
    max_results = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    result = fetch_arxiv(max_results=max_results)
    print(json.dumps(result, ensure_ascii=False, indent=2))
