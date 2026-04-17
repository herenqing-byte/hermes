#!/usr/bin/env python3
"""
fetch_wechat.py - 微信公众号文章采集
用 catclaw_search（tencent-search 引擎）搜索各公众号最新文章
然后用 iPhone UA curl 抓取 mp.weixin.qq.com 文章摘要

用法: python3 fetch_wechat.py [hours=24]
"""

import sys
import json
import re
import subprocess
import time
import urllib.request
from datetime import datetime, timezone, timedelta

HOURS = int(sys.argv[1]) if len(sys.argv) > 1 else 24

ACCOUNTS = [
    "十字路口",
    "赛博禅心",
    "机器之心",
    "量子位",
    "InfoQ",
    "Z Potential",
    "AIGC开放社区",
    "Founder Park",
    "阿里云开发者",
    "36氪",
    "数字生命卡兹克",
    "硅星人Pro",
    "大厂日爆",
    "42章经",
]

CATCLAW_SEARCH = "/app/skills/catclaw-search/scripts/catclaw_search.py"
IPHONE_UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1 MicroMessenger/8.0.43"

now = datetime.now(tz=timezone(timedelta(hours=8)))
output_lines = [f"# 小潮·公众号情报 {now.strftime('%Y-%m-%d %H:%M')}\n"]
all_articles = []


def search_account(account_name):
    """用 catclaw tencent-search 搜索公众号最新文章"""
    query = f"{account_name} 公众号"
    try:
        result = subprocess.run(
            ["uv", "run", CATCLAW_SEARCH, "search", query,
             "-s", "tencent-search", "-n", "5", "--timeout", "15"],
            capture_output=True, text=True, timeout=20
        )
        data = json.loads(result.stdout)
        articles = []
        for r in data.get("results", []):
            url = r.get("url", "")
            title = r.get("title", "").strip()
            pub_time = r.get("publish_time", "")
            snippet = r.get("snippet", "").strip()[:100]
            
            # 只保留公众号文章链接
            if "mp.weixin.qq.com" in url or "weixin.qq.com" in url:
                date_str = pub_time[:10] if pub_time else now.strftime("%Y-%m-%d")
                articles.append({
                    "source": account_name,
                    "title": title,
                    "url": url,
                    "date": date_str,
                    "snippet": snippet,
                })
        return articles
    except Exception as e:
        return []


def fetch_mp_meta(url):
    """用 iPhone UA 抓取公众号文章的 og:title 和 og:description"""
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": IPHONE_UA,
            "Accept-Language": "zh-CN,zh;q=0.9",
        })
        with urllib.request.urlopen(req, timeout=8) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
        
        og_title = re.search(r'property=["\']og:title["\'] content=["\']([^"\']+)["\']', html)
        og_desc = re.search(r'property=["\']og:description["\'] content=["\']([^"\']+)["\']', html)
        return {
            "title": og_title.group(1) if og_title else None,
            "desc": og_desc.group(1) if og_desc else None,
        }
    except Exception:
        return {}


def main():
    print(f"# 小潮·公众号情报 {now.strftime('%Y-%m-%d %H:%M')}")
    print(f"扫描 {len(ACCOUNTS)} 个公众号...\n")

    for account in ACCOUNTS:
        articles = search_account(account)
        if articles:
            print(f"## 📱 {account} ({len(articles)} 篇)")
            for a in articles[:3]:
                # 尝试抓取更准确的标题和摘要
                meta = fetch_mp_meta(a["url"]) if "mp.weixin.qq.com" in a["url"] else {}
                title = meta.get("title") or a["title"]
                desc = meta.get("desc") or a["snippet"] or "（无摘要）"
                print(f"- **{title}** ({a['date']}) — {desc[:80]} [阅读]({a['url']})")
                all_articles.append({**a, "title": title, "desc": desc})
        else:
            print(f"## 📱 {account} — 未找到最新文章")
        
        print()
        time.sleep(0.5)

    # 保存 JSON
    output_path = f"/root/.openclaw/workspace/agents/intern/memory/raw/{now.strftime('%Y-%m-%d')}-wechat.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"# 小潮·公众号情报 {now.strftime('%Y-%m-%d %H:%M')}\n\n")
        for acc in set(a["source"] for a in all_articles):
            f.write(f"## 📱 {acc}\n")
            for a in [x for x in all_articles if x["source"] == acc]:
                f.write(f"- **{a['title']}** ({a['date']}) — {a.get('desc','')[:80]} [阅读]({a['url']})\n")
            f.write("\n")

    print(f"\n✅ 共采集 {len(all_articles)} 篇文章，已保存到 {output_path}")


if __name__ == "__main__":
    main()
