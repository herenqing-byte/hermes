#!/usr/bin/env python3
"""Fetch recent AI blog posts and newsletters via RSS with Catclaw fallback.

For sources whose RSS feeds frequently fail (OpenAI, Anthropic, Meta AI,
The Batch, Cursor), we try RSS first, then fall back to Catclaw search.
"""

import json
import sys
import os
import re
import ssl
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime

# Blog/Newsletter RSS feeds
FEEDS = [
    # --- Individual Blogs ---
    ("Simon Willison", "https://simonwillison.net/atom/everything/", "blog"),
    ("Lilian Weng (OpenAI)", "https://lilianweng.github.io/index.xml", "blog"),
    ("Jay Alammar", "https://jalammar.github.io/feed.xml", "blog"),
    ("Sebastian Raschka", "https://magazine.sebastianraschka.com/feed", "blog"),
    ("Chip Huyen", "https://huyenchip.com/feed.xml", "blog"),
    ("Stratechery (Ben Thompson)", "https://stratechery.com/feed/", "blog"),
    ("Eugene Yan", "https://eugeneyan.com/rss/", "blog"),
    ("Interconnects (Nathan Lambert)", "https://www.interconnects.ai/feed", "blog"),
    ("LessWrong (Curated)", "https://www.lesswrong.com/feed.xml?view=curated-rss", "blog"),
    ("The Gradient", "https://thegradientpub.substack.com/feed", "blog"),
    ("Weights & Biases Blog", "https://wandb.ai/fully-connected/rss.xml", "blog"),
    ("Towards AI", "https://pub.towardsai.net/feed", "blog"),
    ("MIT Technology Review", "https://www.technologyreview.com/feed/", "blog"),

    # --- Company/Research Blogs (may fail, have fallback) ---
    ("OpenAI News", "https://openai.com/news/rss.xml", "company"),
    ("OpenAI Research", "", "company"),  # No dedicated RSS; covered via Catclaw fallback
    ("Anthropic Research", "", "company"),  # No working RSS; covered via Catclaw fallback
    ("Anthropic Engineering Blog", "", "company"),  # No RSS; covered via Catclaw fallback
    ("Google AI Blog", "https://blog.google/technology/ai/rss/", "company"),
    ("Google Research Blog", "https://research.google/blog/rss/", "company"),  # NEW: Google Research (covers DeepMind topics)
    ("Meta AI Blog", "", "company"),  # RSS blocked; covered via Catclaw fallback
    ("HuggingFace Blog", "https://huggingface.co/blog/feed.xml", "company"),

    # --- SOTA Model Company Blogs (Catclaw fallback only) ---
    ("Google DeepMind Blog", "", "company"),  # No public RSS; covered via Catclaw fallback
    ("xAI Blog", "", "company"),             # No public RSS; covered via Catclaw fallback
    ("Mistral AI News", "", "company"),       # No public RSS; covered via Catclaw fallback
    ("Cohere Blog", "", "company"),           # No public RSS; covered via Catclaw fallback
    ("DeepSeek Blog", "", "company"),         # No public RSS; covered via Catclaw fallback

    # --- Platform / Infrastructure Blogs (valid RSS) ---
    ("Microsoft AI Blog", "https://blogs.microsoft.com/ai/feed/", "company"),   # NEW
    ("AWS Machine Learning Blog", "https://aws.amazon.com/blogs/machine-learning/feed/", "company"),  # NEW
    ("NVIDIA AI Blog", "https://developer.nvidia.com/blog/feed/", "company"),  # NEW

    # --- Newsletters ---
    ("Import AI (Jack Clark)", "https://importai.substack.com/feed", "newsletter"),
    ("The Batch (Andrew Ng)", "https://www.deeplearning.ai/the-batch/feed/", "newsletter"),
    ("AI Supremacy", "https://aisupremacy.substack.com/feed", "newsletter"),
    ("Ahead of AI (Sebastian Raschka)", "https://magazine.sebastianraschka.com/feed", "newsletter"),
    ("Lenny's Newsletter", "https://www.lennysnewsletter.com/feed", "newsletter"),

    # --- AI Coding specific ---
    ("Cursor Blog", "", "coding"),           # No working RSS; covered via Catclaw fallback
    ("Sourcegraph Blog", "", "coding"),       # No working RSS; covered via Catclaw fallback
]

# Sources that frequently fail RSS — define Catclaw fallback queries
FALLBACK_SOURCES = {
    "OpenAI News": {
        "domain": "openai.com",
        "queries": ["site:openai.com/news 2026", "openai blog announcement site:openai.com"],
    },
    "OpenAI Research": {
        "domain": "openai.com",
        "queries": ["openai.com research latest March 2026", "site:openai.com/index research safety alignment 2026"],
    },
    "Anthropic Research": {
        "domain": "anthropic.com",
        "queries": ["anthropic.com research blog 2026", "anthropic research latest paper"],
    },
    "Anthropic Engineering Blog": {
        "domain": "anthropic.com",
        "queries": ["site:anthropic.com/engineering 2026", "anthropic engineering blog claude code latest"],
    },
    "Meta AI Blog": {
        "domain": "ai.meta.com",
        "queries": ["ai.meta.com blog 2026", "meta AI research blog latest"],
    },
    "The Batch (Andrew Ng)": {
        "domain": "deeplearning.ai",
        "queries": ["deeplearning.ai the batch Andrew Ng 2026", "the batch AI newsletter latest"],
    },
    "Cursor Blog": {
        "domain": "cursor.com",
        "queries": ["cursor.com blog 2026", "cursor AI editor blog latest"],
    },
    "Sourcegraph Blog": {
        "domain": "sourcegraph.com",
        "queries": ["about.sourcegraph.com blog 2026", "sourcegraph cody blog latest AI coding"],
    },
    # --- SOTA Model Company Blogs (no RSS) ---
    "Google DeepMind Blog": {
        "domain": "deepmind.google",
        "queries": ["deepmind.google blog 2026", "google deepmind research announcement 2026"],
    },
    "xAI Blog": {
        "domain": "x.ai",
        "queries": ["x.ai blog grok 2026", "xAI Grok latest announcement site:x.ai"],
    },
    "Mistral AI News": {
        "domain": "mistral.ai",
        "queries": ["mistral.ai news 2026", "mistral AI model release blog latest 2026"],
    },
    "Cohere Blog": {
        "domain": "cohere.com",
        "queries": ["cohere.com blog 2026", "cohere AI research blog latest"],
    },
    "DeepSeek Blog": {
        "domain": "deepseek.com",
        "queries": ["deepseek.com blog 2026", "deepseek AI model research announcement latest"],
    },
}

CATCLAW_URL = os.environ.get(
    "CATCLAW_SEARCH_URL",
    "https://mmc.sankuai.com/openclaw/v1/universal-search",
)

_ssl_ctx = ssl.create_default_context()
_ssl_ctx.check_hostname = False
_ssl_ctx.verify_mode = ssl.CERT_NONE

PROXY = os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy")

def build_opener():
    if PROXY:
        return urllib.request.build_opener(
            urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
        )
    return urllib.request.build_opener()

def fetch_url(url, opener, timeout=15):
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (compatible; AITrendBot/1.0)"
        })
        resp = opener.open(req, timeout=timeout)
        return resp.read().decode("utf-8")
    except Exception:
        return None

def parse_feed(xml_text, source_name, source_type):
    """Parse RSS or Atom feed."""
    entries = []
    try:
        root = ET.fromstring(xml_text)

        # Try Atom format
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        items = root.findall("atom:entry", ns)

        if not items:
            items = root.findall(".//item")

        if not items:
            items = root.findall("entry")

        for item in items[:5]:
            title = item.findtext("{http://www.w3.org/2005/Atom}title", "")
            if not title:
                title = item.findtext("title", "")

            published = (
                item.findtext("{http://www.w3.org/2005/Atom}published", "") or
                item.findtext("{http://www.w3.org/2005/Atom}updated", "") or
                item.findtext("pubDate", "") or
                item.findtext("dc:date", "")
            )

            link = ""
            link_elem = item.find("{http://www.w3.org/2005/Atom}link")
            if link_elem is not None:
                link = link_elem.get("href", "")
            if not link:
                link = item.findtext("link", "")
            if not link:
                link = item.findtext("{http://www.w3.org/2005/Atom}id", "")

            description = (
                item.findtext("{http://www.w3.org/2005/Atom}summary", "") or
                item.findtext("{http://www.w3.org/2005/Atom}content", "") or
                item.findtext("description", "") or
                ""
            )
            clean_desc = re.sub(r"<[^>]+>", "", description).strip()

            entries.append({
                "source": source_name,
                "type": source_type,
                "title": title.strip(),
                "description": clean_desc[:500],
                "published": published,
                "link": link,
            })
    except ET.ParseError:
        pass
    return entries


def _catclaw_search(query, num=5, timeout=12):
    """Catclaw search for blog fallback. Tries google-search first, then baidu."""
    engines = ["google-search", "baidu-search-v2", "bing"]
    for engine in engines:
        try:
            payload = {
                "query": query,
                "sources": [engine],
                "topK": num,
                "isFast": True,
                "timeout": timeout,
            }
            req = urllib.request.Request(
                CATCLAW_URL,
                json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"},
            )
            resp = urllib.request.urlopen(req, timeout=timeout + 5, context=_ssl_ctx)
            data = json.loads(resp.read())
            inner = data.get("data", {})
            results = inner.get("results", [])
            if results:
                return results
        except Exception:
            continue
    return []


def _fallback_fetch(source_name):
    """Fetch articles via Catclaw search for a failed RSS source."""
    info = FALLBACK_SOURCES.get(source_name)
    if not info:
        return []

    entries = []
    for query in info["queries"]:
        try:
            results = _catclaw_search(query, num=5)
            for r in results:
                title = re.sub(r'<[^>]+>', '', r.get("title", "")).strip()
                url = r.get("url", "")
                snippet = re.sub(r'<[^>]+>', '', r.get("snippet", "")).strip()
                pub = r.get("publish_time", "")

                # Filter to correct domain
                domain = info["domain"]
                if domain not in url:
                    continue

                if not title:
                    continue

                entries.append({
                    "source": source_name,
                    "type": "company",
                    "title": title[:200],
                    "description": snippet[:500],
                    "published": pub,
                    "link": url,
                    "fetched_via": "catclaw_fallback",
                })
            if entries:
                break  # Got results, stop trying more queries
        except Exception:
            continue

    # Dedup by title
    seen = set()
    unique = []
    for e in entries:
        k = e["title"][:50]
        if k not in seen:
            seen.add(k)
            unique.append(e)
    return unique[:5]


def fetch_all(days=7):
    """Fetch recent blog posts from all feeds, with fallback for failed sources."""
    opener = build_opener()
    all_entries = []
    errors = []
    fallback_used = []

    for name, url, ftype in FEEDS:
        xml_text = fetch_url(url, opener) if url else None
        if xml_text:
            entries = parse_feed(xml_text, name, ftype)
            if entries:
                all_entries.extend(entries)
                continue

        # RSS failed — try Catclaw fallback if available
        if name in FALLBACK_SOURCES:
            fb_entries = _fallback_fetch(name)
            if fb_entries:
                all_entries.extend(fb_entries)
                fallback_used.append(name)
                continue

        errors.append(name)

    return {
        "posts": all_entries,
        "fetched_at": datetime.utcnow().isoformat(),
        "total": len(all_entries),
        "sources": len(FEEDS),
        "errors": errors,
        "fallback_used": fallback_used,
    }

if __name__ == "__main__":
    result = fetch_all()
    print(json.dumps(result, ensure_ascii=False, indent=2))
