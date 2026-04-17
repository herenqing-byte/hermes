#!/usr/bin/env python3
"""Fetch top AI-related stories from Hacker News."""

import json
import sys
import urllib.request
from datetime import datetime

HN_TOP = "https://hacker-news.firebaseio.com/v0/topstories.json"
HN_ITEM = "https://hacker-news.firebaseio.com/v0/item/{}.json"

AI_KEYWORDS = [
    "ai", "artificial intelligence", "llm", "gpt", "claude", "gemini",
    "openai", "anthropic", "deepmind", "meta ai", "llama", "mistral",
    "machine learning", "deep learning", "transformer", "diffusion",
    "agent", "rag", "fine-tune", "embedding", "neural", "reasoning",
    "multimodal", "vision language", "chatbot", "copilot", "model",
    "training", "inference", "benchmark", "alignment", "safety",
    "open source ai", "huggingface", "nvidia", "gpu", "tpu",
]

def is_ai_related(title):
    """Check if a story title is AI-related."""
    title_lower = title.lower()
    return any(kw in title_lower for kw in AI_KEYWORDS)

def fetch_hn_ai(max_stories=200, max_results=20):
    """Fetch top AI-related HN stories."""
    # Get top story IDs
    resp = urllib.request.urlopen(HN_TOP, timeout=15)
    story_ids = json.loads(resp.read())[:max_stories]
    
    ai_stories = []
    for sid in story_ids:
        if len(ai_stories) >= max_results:
            break
        try:
            resp = urllib.request.urlopen(HN_ITEM.format(sid), timeout=10)
            item = json.loads(resp.read())
            title = item.get("title", "")
            if is_ai_related(title):
                ai_stories.append({
                    "title": title,
                    "url": item.get("url", f"https://news.ycombinator.com/item?id={sid}"),
                    "score": item.get("score", 0),
                    "comments": item.get("descendants", 0),
                    "by": item.get("by", ""),
                    "hn_link": f"https://news.ycombinator.com/item?id={sid}",
                    "time": datetime.fromtimestamp(item.get("time", 0)).isoformat(),
                })
        except Exception:
            continue
    
    ai_stories.sort(key=lambda x: x["score"], reverse=True)
    
    return {
        "stories": ai_stories,
        "fetched_at": datetime.utcnow().isoformat(),
        "total": len(ai_stories),
    }

if __name__ == "__main__":
    result = fetch_hn_ai()
    print(json.dumps(result, ensure_ascii=False, indent=2))
