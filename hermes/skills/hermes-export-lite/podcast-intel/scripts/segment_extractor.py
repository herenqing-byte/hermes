#!/usr/bin/env python3
"""
segment_extractor.py - Pure Python text segment extraction
Input: long text + keyword list
Output: relevant segments (deduped, sorted by relevance)
No LLM dependency.
"""

import re
import argparse
import sys
from typing import List, Tuple


def tokenize(text: str) -> set:
    """Simple word tokenizer for Jaccard similarity."""
    words = re.findall(r'\b[a-zA-Z0-9]+\b', text.lower())
    return set(words)


def jaccard_similarity(text1: str, text2: str) -> float:
    """Compute Jaccard similarity between two texts."""
    tokens1 = tokenize(text1)
    tokens2 = tokenize(text2)
    if not tokens1 or not tokens2:
        return 0.0
    intersection = tokens1 & tokens2
    union = tokens1 | tokens2
    return len(intersection) / len(union)


def keyword_coverage(text: str, keywords: List[str]) -> float:
    """Return fraction of keywords found in text."""
    if not keywords:
        return 0.0
    text_lower = text.lower()
    found = sum(1 for kw in keywords if kw.lower() in text_lower)
    return found / len(keywords)


def keyword_density(text: str, keywords: List[str]) -> float:
    """Return total keyword occurrences per 1000 chars."""
    if not keywords or not text:
        return 0.0
    text_lower = text.lower()
    total = sum(text_lower.count(kw.lower()) for kw in keywords)
    return total / (len(text) / 1000.0)


def extract_relevant_segments(
    text: str,
    keywords: List[str],
    context_chars: int = 600,
    top_n: int = 5,
    dedup_threshold: float = 0.7
) -> List[Tuple[str, float]]:
    """
    Extract relevant segments from text around keyword positions.
    
    Args:
        text: Input text (can be very long)
        keywords: List of keywords to search for
        context_chars: Characters of context on each side of keyword
        top_n: Max number of segments to return
        dedup_threshold: Jaccard threshold for deduplication (>= removes as duplicate)
    
    Returns:
        List of (segment_text, relevance_score) tuples, sorted by score desc
    """
    if not text or not keywords:
        return []
    
    # Find all keyword positions
    positions = []
    text_lower = text.lower()
    
    for keyword in keywords:
        kw_lower = keyword.lower()
        start = 0
        while True:
            pos = text_lower.find(kw_lower, start)
            if pos == -1:
                break
            positions.append(pos)
            start = pos + 1
    
    if not positions:
        # No keywords found — return beginning of text as fallback
        snippet = text[:context_chars * 2].strip()
        if snippet:
            return [(snippet, 0.0)]
        return []
    
    # Cluster nearby positions (within 2*context_chars) to avoid overlapping windows
    positions.sort()
    clusters = []
    current_cluster = [positions[0]]
    
    for pos in positions[1:]:
        if pos - current_cluster[-1] <= context_chars:
            current_cluster.append(pos)
        else:
            clusters.append(current_cluster)
            current_cluster = [pos]
    clusters.append(current_cluster)
    
    # Extract segments for each cluster (centered on cluster midpoint)
    segments_with_scores = []
    
    for cluster in clusters:
        center = (cluster[0] + cluster[-1]) // 2
        start = max(0, center - context_chars)
        end = min(len(text), center + context_chars)
        
        # Try to start/end at sentence boundaries
        # Look backwards for sentence start
        lookback = text[max(0, start - 100):start + 50]
        for sep in ['. ', '.\n', '! ', '? ', '\n\n']:
            idx = lookback.rfind(sep)
            if idx != -1:
                start = max(0, start - 100 + idx + len(sep))
                break
        
        # Look forward for sentence end
        lookahead = text[end - 50:min(len(text), end + 100)]
        for sep in ['. ', '.\n', '! ', '? ', '\n\n']:
            idx = lookahead.find(sep)
            if idx != -1:
                end = min(len(text), end - 50 + idx + len(sep))
                break
        
        segment = text[start:end].strip()
        if len(segment) < 50:
            continue
        
        # Score: combination of keyword coverage and density
        coverage = keyword_coverage(segment, keywords)
        density = keyword_density(segment, keywords)
        score = (coverage * 0.6) + (min(density / 5.0, 1.0) * 0.4)
        
        segments_with_scores.append((segment, score))
    
    # Deduplicate using Jaccard similarity
    deduped = []
    for seg, score in segments_with_scores:
        is_duplicate = False
        for existing_seg, _ in deduped:
            if jaccard_similarity(seg, existing_seg) >= dedup_threshold:
                is_duplicate = True
                break
        if not is_duplicate:
            deduped.append((seg, score))
    
    # Sort by score descending
    deduped.sort(key=lambda x: x[1], reverse=True)
    
    return deduped[:top_n]


def format_segments(
    segments: List[Tuple[str, float]],
    source_name: str = "",
    keywords: List[str] = None
) -> str:
    """Format segments as Markdown blockquotes with metadata."""
    if not segments:
        return "_No relevant segments found._\n"
    
    lines = []
    for i, (seg, score) in enumerate(segments, 1):
        lines.append(f"**[段落 {i}]** （相关度: {score:.2f}）")
        # Wrap in blockquote
        quoted = "\n".join(f"> {line}" if line.strip() else ">" for line in seg.split('\n'))
        lines.append(quoted)
        lines.append("")
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Extract relevant segments from text by keyword"
    )
    parser.add_argument(
        "--text", "-t",
        required=True,
        help="Input text (or @filepath to read from file)"
    )
    parser.add_argument(
        "--keywords", "-k",
        required=True,
        help="Comma-separated keywords"
    )
    parser.add_argument(
        "--top", "-n",
        type=int,
        default=5,
        help="Max segments to return (default: 5)"
    )
    parser.add_argument(
        "--context", "-c",
        type=int,
        default=600,
        help="Context chars on each side of keyword (default: 600)"
    )
    parser.add_argument(
        "--dedup-threshold",
        type=float,
        default=0.7,
        help="Jaccard dedup threshold (default: 0.7)"
    )
    args = parser.parse_args()
    
    # Read text
    text = args.text
    if text.startswith("@"):
        filepath = text[1:]
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                text = f.read()
        except Exception as e:
            print(f"Error reading file {filepath}: {e}", file=sys.stderr)
            sys.exit(1)
    
    keywords = [kw.strip() for kw in args.keywords.split(",") if kw.strip()]
    
    segments = extract_relevant_segments(
        text=text,
        keywords=keywords,
        context_chars=args.context,
        top_n=args.top,
        dedup_threshold=args.dedup_threshold
    )
    
    print(format_segments(segments, keywords=keywords))


if __name__ == "__main__":
    main()
