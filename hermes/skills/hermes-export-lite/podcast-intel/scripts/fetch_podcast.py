#!/usr/bin/env python3
"""
fetch_podcast.py - Podcast content retrieval and segment extraction
Searches premium podcast sources and extracts relevant segments around keywords.

Usage:
    python3 fetch_podcast.py --query "AI agent" --top 5 --sources all
    python3 fetch_podcast.py -q "openclaw skills" -n 3 --sources latent_space,lex
"""

import argparse
import json
import re
import sys
import time
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Add scripts dir to path
import os
sys.path.insert(0, os.path.dirname(__file__))
from segment_extractor import extract_relevant_segments, format_segments
from _rss_parser import parse_rss, _strip_tags


# ─── Configuration ────────────────────────────────────────────────────────────

TIMEOUT = 15
MAX_RETRIES = 2
CONTENT_LIMIT = 200_000  # max bytes to read per page

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)


# ─── HTTP Utilities ────────────────────────────────────────────────────────────

def http_get(url: str, headers: Dict = None, timeout: int = TIMEOUT, max_bytes: int = CONTENT_LIMIT) -> Optional[str]:
    """Fetch URL with retries. Returns text content or None on failure."""
    req_headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml,application/json,*/*",
        "Accept-Language": "en-US,en;q=0.9",
    }
    if headers:
        req_headers.update(headers)
    
    for attempt in range(MAX_RETRIES + 1):
        try:
            req = urllib.request.Request(url, headers=req_headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                content_type = resp.headers.get("Content-Type", "utf-8")
                charset = "utf-8"
                if "charset=" in content_type:
                    charset = content_type.split("charset=")[-1].split(";")[0].strip()
                raw = resp.read(max_bytes)
                return raw.decode(charset, errors="replace")
        except urllib.error.HTTPError as e:
            if e.code in (403, 404, 410):
                print(f"  [http] {e.code} error for {url[:60]}", file=sys.stderr)
                return None
            if attempt < MAX_RETRIES:
                time.sleep(1.5 ** attempt)
        except Exception as e:
            if attempt < MAX_RETRIES:
                time.sleep(1.5 ** attempt)
            else:
                print(f"  [warn] Failed {url[:60]}: {type(e).__name__}: {e}", file=sys.stderr)
    return None


# ─── Data Model ───────────────────────────────────────────────────────────────

class ArticleMeta:
    def __init__(self, title: str, url: str, date: str, source: str,
                 description: str = "", content: str = ""):
        self.title = title
        self.url = url
        self.date = date
        self.source = source
        self.description = description
        self.content = content


# ─── Source Fetchers ───────────────────────────────────────────────────────────

def _score_articles(articles: List[ArticleMeta], keywords: List[str]) -> List[Tuple[float, ArticleMeta]]:
    """Score articles by keyword presence in title+description."""
    scored = []
    for art in articles:
        text = (art.title + " " + art.description).lower()
        score = sum(1 for kw in keywords if kw.lower() in text)
        # Bonus for keyword in title
        score += sum(1 for kw in keywords if kw.lower() in art.title.lower()) * 0.5
        scored.append((score, art))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored


def search_latent_space(query: str, top_n: int = 5) -> List[ArticleMeta]:
    """Search Latent Space via Substack API + RSS fallback."""
    keywords = [kw.strip() for kw in query.split() if len(kw.strip()) > 2]
    results = []
    
    # Try Substack search API first
    encoded_query = urllib.parse.quote(query)
    api_url = f"https://www.latent.space/api/v1/posts?search={encoded_query}&limit={top_n * 3}"
    
    print(f"  [latent_space] API: {api_url[:80]}", file=sys.stderr)
    content = http_get(api_url)
    
    if content:
        try:
            data = json.loads(content)
            posts = data if isinstance(data, list) else data.get("posts", data.get("data", []))
            
            for post in (posts or []):
                if not isinstance(post, dict):
                    continue
                title = post.get("title", "")
                slug = post.get("slug", "")
                post_date = (post.get("post_date") or post.get("published_at") or "")[:10]
                url = f"https://www.latent.space/p/{slug}" if slug else post.get("canonical_url", "")
                desc = (post.get("subtitle") or post.get("search_engine_description") or "")
                body_html = (post.get("body_html") or post.get("truncated_body_text") or "")
                body_text = _strip_tags(body_html) if body_html else desc
                
                if url and title:
                    results.append(ArticleMeta(
                        title=title, url=url, date=post_date,
                        source="Latent Space",
                        description=desc[:400],
                        content=body_text[:50000]
                    ))
            print(f"  API returned {len(results)} results", file=sys.stderr)
        except (json.JSONDecodeError, TypeError) as e:
            print(f"  [latent_space] API parse error: {e}, trying RSS", file=sys.stderr)
    
    # RSS fallback (always try if API gave < top_n)
    if len(results) < top_n:
        print("  [latent_space] Fetching RSS...", file=sys.stderr)
        rss_content = http_get("https://www.latent.space/feed")
        if rss_content:
            items = parse_rss(rss_content, "Latent Space", max_items=50)
            for item in items:
                # Avoid dupes
                if not any(a.url == item['url'] for a in results):
                    results.append(ArticleMeta(
                        title=item['title'], url=item['url'], date=item['date'],
                        source="Latent Space", description=item['description'],
                        content=item['content']
                    ))
    
    # Score and filter by query relevance
    if keywords:
        scored = _score_articles(results, keywords)
        results = [art for _, art in scored]
    
    return results[:top_n]


def search_lex_fridman(query: str, top_n: int = 5) -> List[ArticleMeta]:
    """Search Lex Fridman via RSS, try to fetch transcripts."""
    print(f"  [lex_fridman] Fetching RSS...", file=sys.stderr)
    keywords = [kw.lower() for kw in query.split() if len(kw) > 2]
    
    rss_content = http_get("https://lexfridman.com/feed/", max_bytes=5_000_000)
    if not rss_content:
        print("  [lex_fridman] RSS unavailable", file=sys.stderr)
        return []
    
    items = parse_rss(rss_content, "Lex Fridman Podcast", max_items=100)
    
    articles = [ArticleMeta(
        title=item['title'], url=item['url'], date=item['date'],
        source="Lex Fridman Podcast", description=item['description'],
        content=item['content']
    ) for item in items]
    
    # Score by keyword relevance
    scored = _score_articles(articles, keywords) if keywords else [(0, a) for a in articles]
    top_articles = [art for _, art in scored[:top_n]]
    
    # Try to fetch transcript pages for top results
    for art in top_articles:
        if art.content and len(art.content) > 1000:
            continue  # Already has content from RSS
        if not art.url:
            continue
        
        # Lex transcript URLs: slug-transcript
        slug = art.url.rstrip("/").split("/")[-1]
        # Remove common URL params
        slug = slug.split("?")[0].split("#")[0]
        
        # Skip non-episode URLs
        if not slug or slug in ('feed', 'podcast', ''):
            continue
        
        transcript_url = f"https://lexfridman.com/{slug}-transcript/"
        # Don't re-fetch if this IS a transcript page
        if "transcript" in slug:
            transcript_url = art.url
        
        print(f"  [lex_fridman] Fetching transcript: {transcript_url[:65]}", file=sys.stderr)
        trans_html = http_get(transcript_url, timeout=20)
        if trans_html and len(trans_html) > 2000:
            art.content = _strip_tags(trans_html)[:60000]
    
    return top_articles


def search_a16z(query: str, top_n: int = 5) -> List[ArticleMeta]:
    """Search a16z podcast via RSS."""
    print(f"  [a16z] Fetching RSS...", file=sys.stderr)
    keywords = [kw.lower() for kw in query.split() if len(kw) > 2]
    
    rss_urls = [
        "https://rss.a16z.com/a16z-podcast",
        "https://a16z.com/feed/podcast/",
        "https://a16z.simplecast.com/rss",
    ]
    
    for rss_url in rss_urls:
        content = http_get(rss_url)
        if not content:
            continue
        
        items = parse_rss(content, "a16z Podcast", max_items=100)
        if not items:
            continue
        
        articles = [ArticleMeta(
            title=item['title'], url=item['url'], date=item['date'],
            source="a16z Podcast", description=item['description'],
            content=item['content']
        ) for item in items]
        
        scored = _score_articles(articles, keywords) if keywords else [(0, a) for a in articles]
        return [art for _, art in scored[:top_n]]
    
    print("  [a16z] All RSS URLs failed", file=sys.stderr)
    return []


def search_web_fallback(query: str, top_n: int = 5) -> List[ArticleMeta]:
    """Last resort: search via Brave/DuckDuckGo HTML."""
    print(f"  [web_fallback] DuckDuckGo search for: {query}", file=sys.stderr)
    results = []
    
    target_domains = ['latent.space', 'lexfridman.com', 'a16z.com']
    
    for domain in target_domains[:2]:
        sq = f"site:{domain} {query}"
        encoded = urllib.parse.quote(sq)
        url = f"https://html.duckduckgo.com/html/?q={encoded}"
        
        content = http_get(url)
        if not content:
            continue
        
        # Extract result links from DDG HTML
        for m in re.finditer(
            r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>',
            content, re.DOTALL | re.IGNORECASE
        ):
            href = m.group(1)
            title = _strip_tags(m.group(2))
            if any(d in href for d in target_domains):
                results.append(ArticleMeta(
                    title=title, url=href, date="",
                    source=f"Web Search ({domain})",
                    description="", content=""
                ))
                if len(results) >= top_n:
                    break
        
        if len(results) >= top_n:
            break
    
    return results[:top_n]


# ─── Main Pipeline ─────────────────────────────────────────────────────────────

def run_search(query: str, sources: List[str], top_n: int) -> List[ArticleMeta]:
    """Run search across specified sources."""
    all_results = []
    
    source_map = {
        "latent_space": search_latent_space,
        "lex": search_lex_fridman,
        "a16z": search_a16z,
    }
    
    active_sources = list(source_map.keys()) if "all" in sources else [
        s for s in sources if s in source_map
    ]
    
    unknown = [s for s in sources if s not in source_map and s != "all"]
    if unknown:
        print(f"  [warn] Unknown sources: {unknown}", file=sys.stderr)
    
    for source_key in active_sources:
        print(f"\n[→] Searching {source_key}...", file=sys.stderr)
        try:
            results = source_map[source_key](query, top_n=top_n)
            print(f"  ✓ {len(results)} articles", file=sys.stderr)
            all_results.extend(results)
        except Exception as e:
            print(f"  ✗ {source_key} failed: {type(e).__name__}: {e}", file=sys.stderr)
    
    if not all_results:
        print("\n[→] Primary sources empty, trying web fallback...", file=sys.stderr)
        try:
            all_results = search_web_fallback(query, top_n=top_n)
            print(f"  ✓ {len(all_results)} fallback results", file=sys.stderr)
        except Exception as e:
            print(f"  ✗ Fallback failed: {e}", file=sys.stderr)
    
    return all_results


def fetch_article_content(article: ArticleMeta) -> str:
    """Fetch content if not already loaded."""
    if article.content and len(article.content) > 500:
        return article.content
    if not article.url:
        return article.description
    
    print(f"  [fetch] {article.url[:65]}...", file=sys.stderr)
    html = http_get(article.url, timeout=20)
    if not html:
        return article.description
    
    return _strip_tags(html)[:60000]


def process_articles(
    articles: List[ArticleMeta],
    keywords: List[str],
    context_chars: int,
    top_n: int
) -> List[Tuple[ArticleMeta, List[Tuple[str, float]]]]:
    """Fetch content and extract relevant segments."""
    results = []
    
    for article in articles:
        print(f"\n[→] Processing: {article.title[:55]}...", file=sys.stderr)
        
        content = fetch_article_content(article)
        article.content = content
        
        if not content:
            print(f"  ↳ No content", file=sys.stderr)
            continue
        
        segments = extract_relevant_segments(
            text=content,
            keywords=keywords,
            context_chars=context_chars,
            top_n=top_n,
            dedup_threshold=0.7
        )
        
        print(f"  ↳ {len(segments)} segments (from {len(content):,} chars)", file=sys.stderr)
        
        if segments or article.description:
            # If no keyword matches, include description as fallback segment
            if not segments and article.description:
                segments = [(article.description, 0.0)]
            results.append((article, segments))
    
    return results


def format_output(
    processed: List[Tuple[ArticleMeta, List[Tuple[str, float]]]],
    query: str,
    sources_used: List[str],
    total_chars_original: int,
    total_chars_extracted: int
) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    lines = [
        f"# 播客素材包：{query}",
        "",
        f"**生成时间**: {now}",
        f"**数据源**: {', '.join(sources_used) if sources_used else 'N/A'}",
        f"**找到文章数**: {len(processed)} 篇",
        f"**提取段落数**: {sum(len(segs) for _, segs in processed)} 段",
        "",
        "---",
        "",
    ]
    
    for i, (article, segments) in enumerate(processed, 1):
        lines.append(f"## 📻 来源 {i}: {article.source}")
        lines.append("")
        title_link = f"[{article.title}]({article.url})" if article.url else article.title
        lines.append(f"**文章/剧集**: {title_link}")
        if article.date:
            lines.append(f"**发布时间**: {article.date}")
        if article.url:
            lines.append(f"**原文链接**: {article.url}")
        if article.description:
            desc = article.description[:200]
            if len(article.description) > 200:
                desc += "..."
            lines.append(f"**简介**: {desc}")
        lines.append("")
        lines.append("### 相关段落")
        lines.append("")
        lines.append(format_segments(segments, source_name=article.source))
        lines.append("")
        lines.append("---")
        lines.append("")
    
    # Token savings
    if total_chars_original > 0:
        savings_pct = max(0, (1 - total_chars_extracted / total_chars_original) * 100)
        approx_tokens_orig = total_chars_original // 4
        approx_tokens_extracted = total_chars_extracted // 4
        
        lines.extend([
            "## 📊 Token 节省估算",
            "",
            "| 指标 | 数值 |",
            "|------|------|",
            f"| 原始内容总字符数 | ~{total_chars_original:,} chars |",
            f"| 提取段落字符数 | ~{total_chars_extracted:,} chars |",
            f"| **节省比例** | **{savings_pct:.0f}%** |",
            f"| 估算原始 Token | ~{approx_tokens_orig:,} |",
            f"| 估算提取 Token | ~{approx_tokens_extracted:,} |",
            "",
            f"> 💡 与直接让 LLM 分析全文相比，此次预处理节省了约 **{savings_pct:.0f}%** 的 token。",
        ])
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="podcast-intel: Efficient podcast content retrieval",
    )
    parser.add_argument("--query", "-q", required=True, help="Search query")
    parser.add_argument("--top", "-n", type=int, default=5, help="Max results (default: 5)")
    parser.add_argument("--sources", "-s", default="all",
                        help="Sources: latent_space,lex,a16z,all (default: all)")
    parser.add_argument("--context-chars", "-c", type=int, default=600,
                        help="Context chars per keyword (default: 600)")
    parser.add_argument("--output", "-o", help="Output file (default: stdout)")
    
    args = parser.parse_args()
    
    sources = [s.strip() for s in args.sources.split(",")]
    keywords = [kw.strip() for kw in args.query.split() if len(kw.strip()) > 2]
    if not keywords:
        keywords = [args.query.strip()]
    
    print(f"\n🎙️  podcast-intel", file=sys.stderr)
    print(f"   Query: {args.query}", file=sys.stderr)
    print(f"   Keywords: {keywords}", file=sys.stderr)
    print(f"   Sources: {sources}", file=sys.stderr)
    print(f"   Top N: {args.top}", file=sys.stderr)
    
    articles = run_search(args.query, sources, args.top)
    
    if not articles:
        print("\n⚠️  No articles found.", file=sys.stderr)
        sys.exit(0)
    
    print(f"\n✅ Total articles: {len(articles)}", file=sys.stderr)
    
    processed = process_articles(articles, keywords, args.context_chars, args.top)
    
    total_original = sum(len(art.content) for art, _ in processed)
    total_extracted = sum(sum(len(seg) for seg, _ in segs) for _, segs in processed)
    sources_used = list(dict.fromkeys(art.source for art, _ in processed))
    
    output = format_output(
        processed=processed,
        query=args.query,
        sources_used=sources_used,
        total_chars_original=total_original,
        total_chars_extracted=total_extracted
    )
    
    if args.output:
        try:
            os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output)
            print(f"\n✅ Saved to: {args.output}", file=sys.stderr)
        except Exception as e:
            print(f"\n[error] Write failed: {e}", file=sys.stderr)
            print(output)
    else:
        print(output)


if __name__ == "__main__":
    main()
