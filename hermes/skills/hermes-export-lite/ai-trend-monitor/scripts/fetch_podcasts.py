#!/usr/bin/env python3
"""Fetch recent AI podcast episodes via podcast RSS feeds + YouTube RSS.

New in v2:
  - Additional high-quality podcast sources
  - youtube_url field for YouTube-sourced episodes
  - has_transcript indicator
  - --with-transcript flag to download subtitles for recent episodes
  - Integrates with get_transcript.py for subtitle extraction
"""

import argparse
import json
import sys
import os
import re
import subprocess
from datetime import datetime, timedelta, timezone
import urllib.request
import xml.etree.ElementTree as ET

# Podcast RSS feeds (more reliable than YouTube RSS which gets blocked)
PODCASTS = [
    # --- Direct podcast RSS (most reliable) ---
    ("Lex Fridman Podcast", "podcast", "https://lexfridman.com/feed/podcast/"),
    ("Dwarkesh Podcast", "podcast", "https://apple.dwarkesh-podcast.workers.dev/feed.rss"),
    # Latent Space 已移至 follow-builders skill，避免重复
    # ("Latent Space", "podcast", "https://api.substack.com/feed/podcast/1084089/s/74880.rss"),
    # No Priors 已移至 follow-builders skill，避免重复
    # ("No Priors (Sarah Guo)", "podcast", "https://feeds.transistor.fm/no-priors-ai-machine-learning-technology"),
    ("Cognitive Revolution", "podcast", "https://feeds.buzzsprout.com/2024896.rss"),
    ("Practical AI", "podcast", "https://changelog.com/practicalai/feed"),
    ("Gradient Dissent", "podcast", "https://feeds.soundcloud.com/users/soundcloud:users:283620555/sounds.rss"),
    ("This Day in AI", "podcast", "https://anchor.fm/s/f0a8a4b0/podcast/rss"),

    # --- New: additional high-quality sources ---
    ("80,000 Hours Podcast", "podcast", "https://feeds.transistor.fm/80000-hours-podcast"),
    ("The Logan Bartlett Show", "podcast", "https://rss2.flightcast.com/jlx9l0yn04wt3r710o051jtm.xml"),
    ("Acquired", "podcast", "https://feeds.transistor.fm/acquired"),
    ("Last Week in AI", "podcast", "https://lastweekin.ai/feed"),
    ("Eye on AI", "podcast", "https://aneyeonai.libsyn.com/rss"),
    ("The AI Podcast (NVIDIA)", "podcast", "https://feeds.megaphone.fm/nvidiaaipodcast"),
    ("Lenny's Podcast", "podcast", "https://api.substack.com/feed/podcast/10845.rss"),
    ("MAD Podcast (Matt Turck)", "podcast", "https://anchor.fm/s/f2ee4948/podcast/rss"),
    ("The Pragmatic Engineer Podcast", "podcast", "https://api.substack.com/feed/podcast/458709.rss"),
    ("Lightcone Podcast (YC)", "podcast", "https://anchor.fm/s/f58d3330/podcast/rss"),
    ("Possible (Reid Hoffman)", "podcast", "https://feeds.megaphone.fm/possible"),

    # --- YouTube channels as backup ---
    ("AI Explained", "youtube", "UCNJ1Ymd5yFuUPtn21xtRbbw"),
    ("Machine Learning Street Talk", "youtube", "UCMLtBahI5DMrt0NPvDSoIRQ"),

    # --- 中文播客 ---
    # 跨国串门儿计划 (小宇宙/Xiaoyuzhou) — 英文科技播客中文精译，47000+订阅
    # RSS via iTunes: https://feed.xyzfm.space/r8t44lmvu99m
    # 注意：代理环境可能返回 403，失败时会在 errors 列表中显示
    ("跨国串门儿计划", "podcast", "https://feed.xyzfm.space/r8t44lmvu99m"),
]

YOUTUBE_RSS_BASE = "https://www.youtube.com/feeds/videos.xml?channel_id="
PROXY = os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy")

# Max characters for transcript text in output
TRANSCRIPT_MAX_CHARS = 30000

def build_opener():
    if PROXY:
        return urllib.request.build_opener(
            urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
        )
    return urllib.request.build_opener()

def fetch_url(url, opener):
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (compatible; AITrendBot/1.0)"
        })
        resp = opener.open(req, timeout=20)
        return resp.read().decode("utf-8")
    except Exception:
        return None

def parse_rss(xml_text, podcast_name, source_type):
    """Parse RSS or Atom feed for podcast episodes."""
    episodes = []
    try:
        root = ET.fromstring(xml_text)
        
        # Atom (YouTube)
        ns_atom = {"atom": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015", "media": "http://search.yahoo.com/mrss/"}
        items = root.findall("atom:entry", ns_atom)
        
        if items:
            for entry in items[:5]:
                title = entry.findtext("{http://www.w3.org/2005/Atom}title", "")
                published = entry.findtext("{http://www.w3.org/2005/Atom}published", "")
                video_id = entry.findtext("{http://www.youtube.com/xml/schemas/2015}videoId", "")
                desc = ""
                mg = entry.find("{http://search.yahoo.com/mrss/}group")
                if mg is not None:
                    desc = mg.findtext("{http://search.yahoo.com/mrss/}description", "")
                link = f"https://www.youtube.com/watch?v={video_id}" if video_id else ""
                ep = {
                    "podcast": podcast_name, "title": title, "description": desc[:600],
                    "published": published, "link": link, "source": source_type,
                }
                # YouTube episodes always have a youtube_url
                if video_id:
                    ep["youtube_url"] = link
                    ep["has_transcript"] = True  # YouTube usually has auto-subs
                else:
                    ep["has_transcript"] = False
                episodes.append(ep)
        else:
            # Standard RSS
            itunes_ns = "http://www.itunes.com/dtds/podcast-1.0.dtd"
            for item in root.findall(".//item")[:5]:
                title = item.findtext("title", "")
                pub_date = item.findtext("pubDate", "")
                description = item.findtext("description", "")
                link = item.findtext("link", "")
                duration = item.findtext(f"{{{itunes_ns}}}duration", "")
                clean_desc = re.sub(r"<[^>]+>", "", description or "").strip()
                
                # Enclosure URL as fallback link
                enc = item.find("enclosure")
                if enc is not None and not link:
                    link = enc.get("url", link)
                
                # Detect YouTube URL in link or enclosure
                youtube_url = None
                yt_match = re.search(r'(https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+|https?://youtu\.be/[\w-]+)', link or "")
                if yt_match:
                    youtube_url = yt_match.group(1)
                # Also check description for YouTube links
                if not youtube_url:
                    yt_match = re.search(r'(https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+|https?://youtu\.be/[\w-]+)', clean_desc)
                    if yt_match:
                        youtube_url = yt_match.group(1)

                ep = {
                    "podcast": podcast_name, "title": title, "description": clean_desc[:600],
                    "published": pub_date, "link": link, "duration": duration, "source": source_type,
                }
                if youtube_url:
                    ep["youtube_url"] = youtube_url
                    ep["has_transcript"] = True
                else:
                    ep["has_transcript"] = False
                episodes.append(ep)
    except ET.ParseError:
        pass
    return episodes


def parse_pub_date(pub_str):
    """Try to parse various date formats into a datetime object (UTC)."""
    if not pub_str:
        return None
    # RFC 2822 (common in RSS): "Mon, 01 Jan 2024 12:00:00 +0000"
    for fmt in [
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S %Z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ]:
        try:
            dt = datetime.strptime(pub_str.strip(), fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    return None


def get_episode_transcript(episode):
    """Call get_transcript.py to fetch transcript for an episode.
    
    Returns transcript text (str) or None.
    """
    youtube_url = episode.get("youtube_url")
    if not youtube_url:
        return None

    script_dir = os.path.dirname(os.path.abspath(__file__))
    transcript_script = os.path.join(script_dir, "get_transcript.py")
    if not os.path.exists(transcript_script):
        return None

    try:
        proc = subprocess.run(
            [sys.executable, transcript_script, youtube_url],
            capture_output=True, text=True, timeout=120,
        )
        if proc.returncode != 0:
            return None
        result = json.loads(proc.stdout)
        return result.get("transcript")
    except Exception:
        return None


def fetch_all(days=7, with_transcript=False):
    opener = build_opener()
    all_episodes = []
    errors = []
    
    now_utc = datetime.now(timezone.utc)
    transcript_cutoff = now_utc - timedelta(hours=24)
    
    for name, ptype, source in PODCASTS:
        url = (YOUTUBE_RSS_BASE + source) if ptype == "youtube" else source
        xml_text = fetch_url(url, opener)
        if xml_text:
            episodes = parse_rss(xml_text, name, ptype)
            all_episodes.extend(episodes)
        else:
            errors.append(name)
    
    # Optionally fetch transcripts for recent episodes
    if with_transcript:
        for ep in all_episodes:
            if not ep.get("has_transcript"):
                continue
            pub_dt = parse_pub_date(ep.get("published", ""))
            if pub_dt and pub_dt < transcript_cutoff:
                continue  # Only fetch for episodes in last 24h
            transcript = get_episode_transcript(ep)
            if transcript:
                ep["transcript"] = transcript[:TRANSCRIPT_MAX_CHARS]
    
    return {
        "episodes": all_episodes,
        "fetched_at": datetime.utcnow().isoformat(),
        "total": len(all_episodes),
        "sources": len(PODCASTS),
        "errors": errors,
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch AI podcast episodes")
    parser.add_argument("--days", type=int, default=7, help="Days of history")
    parser.add_argument("--with-transcript", action="store_true",
                        help="Download transcripts for recent (24h) episodes")
    args = parser.parse_args()

    result = fetch_all(days=args.days, with_transcript=args.with_transcript)
    print(json.dumps(result, ensure_ascii=False, indent=2))
