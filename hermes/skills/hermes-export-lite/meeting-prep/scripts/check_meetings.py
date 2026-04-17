#!/usr/bin/env python3
"""
会前材料提醒脚本
- 扫描未来 2 小时内的会议
- 提前 25-35 分钟窗口触发
- 读取会议 memo 中的 KM wiki 链接并提取内容
- 搜索本地调研知识库 / 历史记忆 / 学城文档
- 输出 JSON 供 cron AI 生成五层分析提醒

提醒消息格式（五层结构）：

📅 会前提醒：[会议名称]
⏰ 30分钟后开始 | [时间] | [地点/链接]

📋 材料核心内容总结
[把 KM 文档主要内容结构化总结：背景、主要议题/方案、关键数据/目标、各方立场]
[用表格、要点列表，让仁清不读原文也能掌握全貌，300-500字]

🔑 关键问题与决策点
• [材料里的风险/决策/存疑之处]

❓ 建议主动询问
• [仁清作为履约平台技术负责人应该问的问题]

🔍 相关历史上下文
[如果在调研知识库/记忆/学城找到相关内容则显示，否则省略整节]

📎 原始材料：[KM链接]
"""

import subprocess
import json
import re
import os
import sys
import time
import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ── 常量 ────────────────────────────────────────────────────────────────────
STATE_DIR  = Path.home() / ".meeting-prep"
STATE_FILE = STATE_DIR / "reminded.json"
MEMORY_DIR = Path("/root/.openclaw/workspace/memory")
RESEARCH_DIR = Path("/root/.openclaw/workspace/research/reports")
VECTOR_INDEX = Path("/root/.openclaw/workspace/research/tools/vector_index.py")
TOKEN_CACHE  = Path.home() / ".openclaw/workspace/tools/.sso_token_cache.json"

# 提醒窗口：距会议开始 25~35 分钟
REMIND_MIN_MINUTES = 25
REMIND_MAX_MINUTES = 35

# 上下文检索：最近 30 天记忆文件
MEMORY_LOOKBACK_DAYS = 30

# KM 内容截断（避免 token 过多）
KM_MAX_CHARS = 4000

TZ_CST = timezone(timedelta(hours=8))

# ── 工具函数 ─────────────────────────────────────────────────────────────────

def run(cmd, timeout=30):
    """运行 shell 命令，返回 stdout 字符串（失败返回空串）"""
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip()
    except Exception:
        return ""


def now_cst():
    return datetime.now(TZ_CST)


# ── SSO Token 检查 ────────────────────────────────────────────────────────────

def check_token_cache_valid():
    """检查 SSO token 缓存是否有效（未过期）"""
    if not TOKEN_CACHE.exists():
        return False
    try:
        data = json.loads(TOKEN_CACHE.read_text())
        expires_at = data.get("expires_at", 0)
        return time.time() < expires_at - 60  # 留60秒余量
    except Exception:
        return False


def ensure_sso_token(mis="herenqing"):
    """
    确保 SSO token 有效。
    - token 有效：直接返回 True
    - token 过期：先发大象通知，再调 auto_sso_confirm.py，等待最多60秒
    返回 True 表示 token 已就绪，False 表示仍然失败。
    """
    if check_token_cache_valid():
        return True

    # token 过期，通知用户
    print("[SSO] token 已过期，正在发起 CIBA 认证...", file=sys.stderr)
    notify_cmd = (
        'python3 -c "'
        'import subprocess; '
        'subprocess.run([\"openclaw\", \"message\", \"send\", '
        '\"--channel\", \"daxiang\", \"--to\", \"single_941328\", '
        '\"--message\", \"⚠️ 会前提醒：SSO 需要重新授权，请打开大象点击确认后，会议提醒将延迟发送。\"], '
        'check=False)"'
    )
    run(notify_cmd, timeout=10)

    # 调用 auto_sso_confirm.py 处理 CIBA 认证
    auto_sso = Path("/root/.openclaw/workspace/tools/auto_sso_confirm.py")
    if auto_sso.exists():
        try:
            subprocess.run(
                ["python3", str(auto_sso), mis],
                timeout=90,
                capture_output=False,
            )
        except subprocess.TimeoutExpired:
            print("[SSO] auto_sso_confirm.py 超时", file=sys.stderr)
            return False
        except Exception as e:
            print(f"[SSO] auto_sso_confirm.py 异常: {e}", file=sys.stderr)
            return False
    else:
        print(f"[SSO] 找不到 auto_sso_confirm.py: {auto_sso}", file=sys.stderr)
        return False

    # 再次检查
    if check_token_cache_valid():
        return True

    # 等待最多60秒（用于 CIBA 异步确认场景）
    print("[SSO] 等待用户确认（最多60秒）...", file=sys.stderr)
    deadline = time.time() + 60
    while time.time() < deadline:
        time.sleep(5)
        if check_token_cache_valid():
            return True

    print("[SSO] 等待超时，token 仍未就绪", file=sys.stderr)
    return False


# ── 日历 ─────────────────────────────────────────────────────────────────────

def get_meetings_for_date(date_str):
    """用 mtcal -f json day 获取指定日期的会议列表"""
    out = run(f"mtcal -f json day --date {date_str}", timeout=30)
    # 跳过第一行"Fetching…"提示行，找 JSON 数组
    lines = out.splitlines()
    json_start = next((i for i, l in enumerate(lines) if l.strip().startswith("[")), None)
    if json_start is None:
        return []
    try:
        return json.loads("\n".join(lines[json_start:]))
    except Exception:
        return []


def get_meeting_detail(schedule_id):
    """用 mtcal -f json detail 获取会议详情（含 memo）"""
    out = run(f"mtcal -f json detail {schedule_id}", timeout=30)
    lines = out.splitlines()
    json_start = next((i for i, l in enumerate(lines) if l.strip().startswith("{")), None)
    if json_start is None:
        return {}
    try:
        return json.loads("\n".join(lines[json_start:]))
    except Exception:
        return {}


def get_upcoming_meetings(target_date=None, dry_run=False):
    """
    返回未来 2 小时内（或指定日期全天）的会议列表。
    dry_run=True 且未指定 target_date 时，扫今天 + 明天两天。
    每条补充 detail（含 memo）。
    """
    now = now_cst()
    dates_to_check = set()

    if target_date:
        # 用户明确指定日期，只扫那天
        dates_to_check.add(target_date)
    elif dry_run:
        # dry-run 模式：扫今天 + 明天，方便提前发现明天有 KM 链接的会议
        dates_to_check.add(now.strftime("%Y-%m-%d"))
        tomorrow = now + timedelta(days=1)
        dates_to_check.add(tomorrow.strftime("%Y-%m-%d"))
    else:
        # 正式模式：当天 + 跨天场景（当前时间接近午夜时加明天）
        dates_to_check.add(now.strftime("%Y-%m-%d"))
        future2h = now + timedelta(hours=2)
        dates_to_check.add(future2h.strftime("%Y-%m-%d"))

    meetings = []
    seen_ids = set()
    for d in sorted(dates_to_check):
        for m in get_meetings_for_date(d):
            sid = m.get("schedule_id", "")
            if sid and sid not in seen_ids:
                seen_ids.add(sid)
                meetings.append(m)
    return meetings


# ── KM 链接 ──────────────────────────────────────────────────────────────────

KM_PATTERN = re.compile(r'https?://km\.sankuai\.com/(?:collabpage|page)/(\d+)[^\s\]"\'<>]*')


def extract_km_links(text):
    """从文本中提取所有 km.sankuai.com 链接，返回 [(url, content_id), ...]"""
    if not text:
        return []
    return [(m.group(0), m.group(1)) for m in KM_PATTERN.finditer(text)]


def fetch_km_content(content_id, url):
    """
    通过 oa-skills citadel getMarkdown 获取 KM 内容，截断到 KM_MAX_CHARS。
    调用前先检查 SSO token，token 过期则先刷新，避免卡住等待 CIBA 确认。
    """
    # SSO 检查：token 过期则先刷新
    if not ensure_sso_token("herenqing"):
        return f"[KM内容获取失败：SSO token 过期且刷新失败，请手动确认后重试]"

    out = run(f'oa-skills citadel getMarkdown --contentId "{content_id}" --mis herenqing', timeout=40)
    # 跳过 CLI 头部提示行（✓ 开头）
    lines = [l for l in out.splitlines() if not l.startswith("\x1b") and not l.startswith("✓")]
    content = "\n".join(lines).strip()
    if len(content) > KM_MAX_CHARS:
        content = content[:KM_MAX_CHARS] + "\n\n…（内容已截断）"
    return content


# ── 上下文关联检索 ────────────────────────────────────────────────────────────

def extract_keywords(title):
    """从会议标题中提取搜索关键词（去掉常见停用词）"""
    stopwords = {"会议", "讨论", "沟通", "对齐", "周会", "例会", "汇报", "评审", "同步", "交流"}
    # 保留中文词和英文词，过滤停用词
    words = re.findall(r'[\u4e00-\u9fa5]{2,}|[A-Za-z][A-Za-z0-9_\-]{1,}', title)
    keywords = [w for w in words if w not in stopwords]
    return " ".join(keywords[:4]) if keywords else title[:10]


def search_research_kb(keywords):
    """
    用向量索引搜索本地调研知识库。
    返回 [{"title": ..., "summary": ..., "path": ...}, ...]，最多3条。
    """
    if not VECTOR_INDEX.exists():
        return []
    out = run(f'python3 "{VECTOR_INDEX}" --search "{keywords}"', timeout=30)
    if not out:
        return []

    results = []
    # 解析输出：每条结果通常包含 文件路径 + 摘要段落
    # vector_index.py 输出格式：每条结果一个 JSON 对象或纯文本块
    # 尝试 JSON 解析
    try:
        data = json.loads(out)
        if isinstance(data, list):
            for item in data[:3]:
                results.append({
                    "title": item.get("title") or Path(item.get("path", "")).stem,
                    "summary": (item.get("content") or item.get("summary") or "")[:300],
                    "path": item.get("path", ""),
                })
            return results
    except Exception:
        pass

    # 纯文本解析：按 --- 分块
    blocks = re.split(r'-{3,}', out)
    for block in blocks[:3]:
        block = block.strip()
        if not block:
            continue
        # 尝试提取文件路径
        path_match = re.search(r'/[^\s]+\.md', block)
        path = path_match.group(0) if path_match else ""
        title = Path(path).stem if path else block.splitlines()[0][:60]
        summary = block[:300]
        results.append({"title": title, "summary": summary, "path": path})

    return results


def search_memory_files(keywords):
    """
    搜索最近 30 天的 memory 日记文件，找与关键词相关的段落。
    返回 [{"date": "YYYY-MM-DD", "snippet": ...}, ...]，最多3条。
    """
    if not MEMORY_DIR.exists():
        return []

    now = now_cst()
    cutoff = now - timedelta(days=MEMORY_LOOKBACK_DAYS)
    keyword_list = [k.lower() for k in keywords.split() if len(k) >= 2]
    if not keyword_list:
        return []

    results = []
    # 遍历 memory/YYYY-MM-DD.md 文件
    for f in sorted(MEMORY_DIR.glob("????-??-??.md"), reverse=True):
        try:
            date_str = f.stem
            file_date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=TZ_CST)
        except ValueError:
            continue
        if file_date < cutoff:
            break

        try:
            text = f.read_text(encoding="utf-8")
        except Exception:
            continue

        # 按段落搜索
        paragraphs = [p.strip() for p in re.split(r'\n{2,}', text) if p.strip()]
        for para in paragraphs:
            para_lower = para.lower()
            if any(kw in para_lower for kw in keyword_list):
                snippet = para[:200].replace("\n", " ")
                results.append({"date": date_str, "snippet": snippet})
                if len(results) >= 3:
                    return results

    return results


def search_citadel(keywords):
    """
    用 oa-skills citadel search 搜索仁清学城个人空间。
    返回 [{"title": ..., "url": ..., "snippet": ...}, ...]，最多3条。
    """
    out = run(
        f'oa-skills citadel search --keyword "{keywords}" --mis herenqing --limit 5 2>&1',
        timeout=30
    )
    if not out or "error" in out.lower()[:50]:
        return []

    results = []
    try:
        # 尝试 JSON
        lines = out.splitlines()
        json_start = next((i for i, l in enumerate(lines) if l.strip().startswith("[") or l.strip().startswith("{")), None)
        if json_start is not None:
            data = json.loads("\n".join(lines[json_start:]))
            if not isinstance(data, list):
                data = [data]
            for item in data[:3]:
                cid = item.get("contentId") or item.get("id") or ""
                results.append({
                    "title": item.get("title", ""),
                    "url": f"https://km.sankuai.com/collabpage/{cid}" if cid else "",
                    "snippet": (item.get("summary") or item.get("content") or "")[:150],
                })
            return results
    except Exception:
        pass

    return []


# ── 状态管理 ──────────────────────────────────────────────────────────────────

def load_reminded():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_reminded(data):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# ── 主逻辑 ────────────────────────────────────────────────────────────────────

def check(dry_run=False, target_date=None):
    now = now_cst()
    reminded = load_reminded()
    pending = []   # 本次需要提醒的会议

    # Bug 1 fix: dry-run 时传入 dry_run 标志，让 get_upcoming_meetings 扫今天+明天
    meetings = get_upcoming_meetings(target_date=target_date, dry_run=dry_run)

    for m in meetings:
        sid = m.get("schedule_id", "")
        if not sid:
            continue

        # ── 已提醒过则跳过 ──
        if sid in reminded and not dry_run:
            continue

        # ── 时间窗口判断（dry-run 模式跳过时间限制） ──
        start_ms = m.get("start_time", 0)
        start_dt = datetime.fromtimestamp(start_ms / 1000, tz=TZ_CST)
        minutes_until = (start_dt - now).total_seconds() / 60

        in_window = REMIND_MIN_MINUTES <= minutes_until <= REMIND_MAX_MINUTES
        if not in_window and not dry_run:
            continue
        # dry-run：扫今天+明天所有有 KM 链接的会议，不受时间窗口限制

        # ── 获取详情（含 memo） ──
        detail = get_meeting_detail(sid)
        memo = detail.get("memo", "") or ""
        meeting_url = detail.get("meeting_join_url", "") or ""
        location = detail.get("location", "") or m.get("location", "")

        km_links = extract_km_links(memo)

        # dry-run 模式：列出所有含 KM 链接的会议
        if dry_run and not km_links:
            continue

        # 正式模式：只提醒有 KM 链接的会议
        if not km_links and not dry_run:
            continue

        # ── 读取 KM 内容（Bug 2 fix: 先检查 SSO token） ──
        km_contents = []
        for url, cid in km_links:
            if dry_run:
                content = "[dry-run: KM内容未读取]"
            else:
                content = fetch_km_content(cid, url)
            km_contents.append({"url": url, "content_id": cid, "content": content})

        # ── 上下文关联检索 ──
        title = m.get("title", "")
        keywords = extract_keywords(title)

        research_hits = search_research_kb(keywords) if not dry_run else []
        memory_hits   = search_memory_files(keywords)
        citadel_hits  = search_citadel(keywords) if not dry_run else []

        context = {
            "research": research_hits,
            "memory":   memory_hits,
            "citadel":  citadel_hits,
        }
        has_context = any(context[k] for k in context)

        # ── 构建输出条目 ──
        entry = {
            "schedule_id":    sid,
            "title":          title,
            "start_datetime": m.get("start_datetime", ""),
            "start_str":      m.get("start_str", ""),
            "end_str":        m.get("end_str", ""),
            "location":       location,
            "meeting_url":    meeting_url,
            "minutes_until":  round(minutes_until, 1),
            "km_links":       km_contents,
            "context":        context if has_context else {},
            "keywords":       keywords,
        }
        pending.append(entry)

        # ── 记录已提醒状态（非 dry-run） ──
        if not dry_run:
            reminded[sid] = now.isoformat()

    # 保存状态
    if not dry_run and pending:
        save_reminded(reminded)

    return pending


# ── 入口 ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="会前材料提醒脚本")
    parser.add_argument("--dry-run", action="store_true",
                        help="不发消息，不记录状态，只打印将要提醒的会议（默认扫今天+明天）")
    parser.add_argument("--date", default=None,
                        help="指定日期 YYYY-MM-DD（dry-run 用，覆盖默认扫描范围）")
    args = parser.parse_args()

    results = check(dry_run=args.dry_run, target_date=args.date)

    if args.dry_run:
        print(f"\n{'='*60}")
        print(f"[dry-run] 共找到 {len(results)} 个含 KM 链接的会议")
        if not args.date:
            now = now_cst()
            tomorrow = (now + timedelta(days=1)).strftime("%Y-%m-%d")
            print(f"[dry-run] 扫描范围：{now.strftime('%Y-%m-%d')}（今天）+ {tomorrow}（明天）")
        else:
            print(f"[dry-run] 扫描范围：{args.date}（指定日期）")
        print('='*60)
        for r in results:
            print(f"\n📅 {r['title']}")
            print(f"   时间：{r['start_str']} - {r['end_str']}  ({r['start_datetime'][:10]})")
            print(f"   地点：{r['location']}")
            print(f"   关键词：{r['keywords']}")
            print(f"   KM 链接：")
            for km in r["km_links"]:
                print(f"     - {km['url']}")
            if r.get("context"):
                ctx = r["context"]
                if ctx.get("memory"):
                    print(f"   📝 记忆命中：{len(ctx['memory'])} 条")
                    for hit in ctx["memory"]:
                        print(f"      [{hit['date']}] {hit['snippet'][:80]}…")
    else:
        # 正式模式：输出 JSON 供 cron AI 读取
        print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
