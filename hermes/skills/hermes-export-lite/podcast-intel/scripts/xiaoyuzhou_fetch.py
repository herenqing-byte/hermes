#!/usr/bin/env python3
"""
小宇宙播客内容抓取工具
用法：python3 xiaoyuzhou_fetch.py <episode_url_or_id> [--output file.md]
"""

import sys
import json
import re
import urllib.request
import html
import argparse
from pathlib import Path


def fetch_episode(episode_id: str) -> dict:
    """抓取单集完整数据（从 __NEXT_DATA__）"""
    url = f"https://www.xiaoyuzhoufm.com/episode/{episode_id}"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xhtml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    })
    with urllib.request.urlopen(req, timeout=15) as r:
        html_content = r.read().decode("utf-8", errors="ignore")

    # 提取 __NEXT_DATA__
    match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html_content, re.DOTALL)
    if not match:
        raise ValueError("未找到 __NEXT_DATA__，页面结构可能已变更")

    data = json.loads(match.group(1))

    # 深度找 episode 数据
    props = data.get("props", {})
    page_props = props.get("pageProps", {})
    episode = page_props.get("episode", page_props.get("data", {}))

    return episode, data


def html_to_text(html_str: str) -> str:
    """简单的 HTML → 纯文本转换"""
    if not html_str:
        return ""
    # 保留段落换行
    text = re.sub(r'<br\s*/?>', '\n', html_str)
    text = re.sub(r'</p>', '\n', text)
    text = re.sub(r'</li>', '\n', text)
    text = re.sub(r'<hr\s*/?>', '\n---\n', text)
    text = re.sub(r'<blockquote[^>]*>', '\n> ', text)
    text = re.sub(r'</blockquote>', '\n', text)
    text = re.sub(r'<h[1-6][^>]*>', '\n## ', text)
    text = re.sub(r'</h[1-6]>', '\n', text)
    # 去掉其他标签
    text = re.sub(r'<[^>]+>', '', text)
    # 解码 HTML 实体
    text = html.unescape(text)
    # 清理多余空行
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def format_episode(episode: dict) -> str:
    """格式化为 Markdown"""
    lines = []

    title = episode.get("title", "（无标题）")
    lines.append(f"# {title}\n")

    # 元信息
    podcast = episode.get("podcast", {})
    podcast_title = podcast.get("title", "")
    if podcast_title:
        lines.append(f"**播客**：{podcast_title}")

    pub_time = episode.get("publishedAt", episode.get("pubDate", ""))
    if pub_time:
        lines.append(f"**发布时间**：{pub_time[:10]}")

    duration_ms = episode.get("duration", 0)
    if duration_ms:
        mins = int(duration_ms) // 60000 if duration_ms > 10000 else int(duration_ms) // 60
        lines.append(f"**时长**：{mins} 分钟")

    ep_url = episode.get("url", "")
    if not ep_url:
        eid = episode.get("eid", episode.get("id", ""))
        if eid:
            ep_url = f"https://www.xiaoyuzhoufm.com/episode/{eid}"
    if ep_url:
        lines.append(f"**链接**：{ep_url}")

    # 音频地址
    media = episode.get("mediaKey", episode.get("enclosure", {}).get("url", ""))
    if media:
        lines.append(f"**音频**：{media}")

    lines.append("")

    # Shownotes（主要内容）
    shownotes = episode.get("shownotes", "")
    description = episode.get("description", "")

    content = shownotes if len(shownotes) > len(description) else description

    if content:
        # 判断是 HTML 还是纯文本
        if "<p>" in content or "<span>" in content:
            content = html_to_text(content)
        lines.append("## 节目内容\n")
        lines.append(content)

    # Transcript（如果有）
    transcript = episode.get("transcript", "")
    if transcript:
        lines.append("\n## 文字稿\n")
        if isinstance(transcript, list):
            for seg in transcript:
                speaker = seg.get("speaker", "")
                text = seg.get("text", "")
                start = seg.get("startTime", 0)
                mins, secs = divmod(int(start), 60)
                ts = f"[{mins:02d}:{secs:02d}]"
                if speaker:
                    lines.append(f"**{ts} {speaker}**：{text}")
                else:
                    lines.append(f"{ts} {text}")
        else:
            lines.append(str(transcript))

    return "\n".join(lines)


def parse_id_from_url(url_or_id: str) -> str:
    """从 URL 或直接 ID 提取 episode ID"""
    # 支持完整 URL 或纯 ID
    match = re.search(r'episode/([a-f0-9]+)', url_or_id)
    if match:
        return match.group(1)
    # 如果本身就是 24 位 hex ID
    if re.match(r'^[a-f0-9]{24}$', url_or_id):
        return url_or_id
    raise ValueError(f"无法识别的 URL 或 ID：{url_or_id}")


def main():
    parser = argparse.ArgumentParser(description="小宇宙播客内容抓取")
    parser.add_argument("url", help="小宇宙 episode URL 或 ID")
    parser.add_argument("--output", "-o", help="输出文件路径（默认打印到终端）")
    parser.add_argument("--json", action="store_true", help="输出原始 JSON")
    args = parser.parse_args()

    episode_id = parse_id_from_url(args.url)
    print(f"正在抓取 episode: {episode_id} ...", file=sys.stderr)

    episode, raw_data = fetch_episode(episode_id)

    if args.json:
        output = json.dumps(episode, ensure_ascii=False, indent=2)
    else:
        output = format_episode(episode)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"✅ 已保存到 {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
