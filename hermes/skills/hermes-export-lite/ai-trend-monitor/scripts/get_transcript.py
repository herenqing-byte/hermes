#!/usr/bin/env python3
"""Extract transcript/subtitles from a YouTube video.

Usage:
    python3 get_transcript.py <youtube_url_or_video_id> [--output /tmp/transcript.txt]

Output (stdout): JSON with video_id, title, transcript text, and segments.

Strategy:
  1. yt-dlp: try English manual subs, then auto subs
  2. youtube-transcript-api as fallback
  3. Clean VTT/SRT: deduplicate lines, strip timestamps, output plain text
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def extract_video_id(url_or_id):
    """Extract YouTube video ID from various URL formats or bare ID."""
    if re.match(r'^[\w-]{11}$', url_or_id):
        return url_or_id
    patterns = [
        r'(?:v=|/v/|youtu\.be/|/embed/|/shorts/)([\w-]{11})',
        r'^([\w-]{11})$',
    ]
    for p in patterns:
        m = re.search(p, url_or_id)
        if m:
            return m.group(1)
    return None


def clean_vtt_text(raw):
    """Clean VTT/SRT subtitle text: remove timestamps, tags, deduplicate."""
    lines = raw.splitlines()
    seen = set()
    clean_lines = []
    for line in lines:
        line = line.strip()
        # Skip VTT header, sequence numbers, timestamp lines
        if not line or line.startswith("WEBVTT") or line.startswith("NOTE"):
            continue
        if re.match(r'^\d+$', line):
            continue
        if re.match(r'\d{2}:\d{2}', line) and '-->' in line:
            continue
        # Remove HTML tags and VTT cue tags
        line = re.sub(r'<[^>]+>', '', line)
        # Remove leading/trailing whitespace
        line = line.strip()
        if not line:
            continue
        # Deduplicate consecutive identical lines (common in auto-subs)
        if line not in seen:
            clean_lines.append(line)
        seen.add(line)
        # Reset seen set periodically to allow repeated phrases later
        if len(seen) > 50:
            seen = {line}
    return "\n".join(clean_lines)


def _run(cmd, timeout=120):
    """Run a subprocess, return (stdout, stderr, returncode)."""
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
        return proc.stdout, proc.stderr, proc.returncode
    except FileNotFoundError:
        return "", "command not found", 1
    except subprocess.TimeoutExpired:
        return "", "timeout", 1


# ---------------------------------------------------------------------------
# Method 1: yt-dlp
# ---------------------------------------------------------------------------

def try_ytdlp(video_id):
    """Try to get transcript via yt-dlp subtitle download."""
    url = f"https://www.youtube.com/watch?v={video_id}"
    tmpdir = tempfile.mkdtemp(prefix="ytsub_")
    out_template = os.path.join(tmpdir, "%(id)s.%(ext)s")

    # Try manual English subs first, then auto subs
    for sub_args in [
        ["--write-sub", "--sub-lang", "en", "--skip-download"],
        ["--write-auto-sub", "--sub-lang", "en", "--skip-download"],
    ]:
        cmd = ["yt-dlp"] + sub_args + [
            "--sub-format", "vtt/srt/best",
            "-o", out_template,
            url,
        ]
        stdout, stderr, rc = _run(cmd, timeout=60)
        if rc == 0:
            # Look for downloaded subtitle file
            for f in os.listdir(tmpdir):
                if f.endswith((".vtt", ".srt")):
                    fpath = os.path.join(tmpdir, f)
                    with open(fpath, "r", encoding="utf-8", errors="replace") as fh:
                        raw = fh.read()
                    # Cleanup temp
                    for ff in os.listdir(tmpdir):
                        os.remove(os.path.join(tmpdir, ff))
                    os.rmdir(tmpdir)
                    text = clean_vtt_text(raw)
                    if text.strip():
                        return text, "yt-dlp"
    # Cleanup
    for f in os.listdir(tmpdir):
        os.remove(os.path.join(tmpdir, f))
    os.rmdir(tmpdir)
    return None, None


# ---------------------------------------------------------------------------
# Method 2: youtube-transcript-api
# ---------------------------------------------------------------------------

def try_transcript_api(video_id):
    """Try to get transcript via youtube-transcript-api."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        return None, None, None

    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        # Prefer manual English, then any manual, then auto English, then any
        transcript = None
        for t in transcript_list:
            if not t.is_generated and t.language_code.startswith("en"):
                transcript = t
                break
        if transcript is None:
            for t in transcript_list:
                if not t.is_generated:
                    transcript = t
                    break
        if transcript is None:
            for t in transcript_list:
                if t.is_generated and t.language_code.startswith("en"):
                    transcript = t
                    break
        if transcript is None:
            transcript = next(iter(transcript_list))

        segments = transcript.fetch()
        # Handle both old and new API formats
        if hasattr(segments, 'to_raw_data'):
            raw_segments = segments.to_raw_data()
        elif isinstance(segments, list):
            raw_segments = segments
        else:
            raw_segments = list(segments)

        text_parts = []
        result_segments = []
        for s in raw_segments:
            if isinstance(s, dict):
                t = s.get("text", "")
                start = s.get("start", 0)
                dur = s.get("duration", 0)
            else:
                t = getattr(s, 'text', str(s))
                start = getattr(s, 'start', 0)
                dur = getattr(s, 'duration', 0)
            text_parts.append(t)
            result_segments.append({"start": start, "duration": dur, "text": t})

        full_text = "\n".join(text_parts)
        return full_text, result_segments, "youtube-transcript-api"
    except Exception:
        return None, None, None


# ---------------------------------------------------------------------------
# Get video title via yt-dlp
# ---------------------------------------------------------------------------

def get_video_title(video_id):
    """Get video title via yt-dlp --get-title."""
    url = f"https://www.youtube.com/watch?v={video_id}"
    stdout, stderr, rc = _run(["yt-dlp", "--get-title", url], timeout=30)
    if rc == 0 and stdout.strip():
        return stdout.strip()
    return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def get_transcript(url_or_id):
    """Get transcript for a YouTube video. Returns dict."""
    video_id = extract_video_id(url_or_id)
    if not video_id:
        return {"error": f"Cannot extract video ID from: {url_or_id}"}

    title = get_video_title(video_id)

    # Method 1: yt-dlp
    text, method = try_ytdlp(video_id)
    if text:
        return {
            "video_id": video_id,
            "title": title,
            "method": method,
            "transcript": text,
            "char_count": len(text),
        }

    # Method 2: youtube-transcript-api
    text, segments, method = try_transcript_api(video_id)
    if text:
        result = {
            "video_id": video_id,
            "title": title,
            "method": method,
            "transcript": text,
            "char_count": len(text),
        }
        if segments:
            result["segments"] = segments
        return result

    return {
        "video_id": video_id,
        "title": title,
        "error": "No transcript available (tried yt-dlp and youtube-transcript-api)",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract YouTube video transcript")
    parser.add_argument("url", help="YouTube URL or video ID")
    parser.add_argument("--output", "-o", help="Write transcript text to file")
    args = parser.parse_args()

    result = get_transcript(args.url)

    if args.output and "transcript" in result:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(result["transcript"])
        print(f"Transcript written to {args.output}", file=sys.stderr)

    print(json.dumps(result, ensure_ascii=False, indent=2))
