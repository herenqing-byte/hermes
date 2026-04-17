#!/usr/bin/env python3
"""
大象群消息总结工具
用法:
  python3 summarize.py --groups "AI应用讨论一群,大象助理头部玩家交流群" [--date 2026-03-18]
  python3 summarize.py --gids "66680558681,70428157100" [--date today]
输出: 发送大象消息给仁清 (uid=941328)
"""
import subprocess, json, sys, argparse, os
from datetime import date

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FETCH_SCRIPT = os.path.join(SCRIPT_DIR, "fetch_messages.py")
DX_PATH = "/tmp/xm-cli/node_modules/.bin/dx"
MY_UID = "941328"

# 已知 gid 映射
KNOWN_GIDS = {
    "AI应用讨论一群": "66680558681",
    "大象助理头部玩家交流群": "70428157100",
}

def fetch(gid, target_date, limit=300):
    result = subprocess.run(
        ["python3", FETCH_SCRIPT, "--gid", str(gid), "--date", str(target_date), "--limit", str(limit)],
        capture_output=True, text=True, timeout=180
    )
    try:
        return json.loads(result.stdout)
    except:
        return []

def format_msgs_for_ai(msgs):
    """格式化消息供 AI 分析"""
    lines = []
    for m in msgs:
        sender = m.get("sender", {}).get("name", "?")
        uid = m.get("sender", {}).get("uid", "")
        time_str = m.get("time", "")[:16] if m.get("time") else ""
        kind = m.get("kind", "text")
        content = m.get("content", {})
        
        if kind == "text":
            text = content.get("text", "")
        elif kind == "image":
            text = f"[图片] {content.get('caption', '')}"
        elif kind == "general":
            text = content.get("summary", content.get("text", "[卡片]"))
        else:
            text = str(content)[:100]
        
        if not text.strip():
            continue
            
        marker = "⭐" if uid == MY_UID else ""
        lines.append(f"{marker}[{time_str}] {sender}: {text[:300]}")
    
    return "\n".join(lines)

def resolve_gid(group_name):
    """根据群名解析 gid"""
    if group_name in KNOWN_GIDS:
        return KNOWN_GIDS[group_name]
    result = subprocess.run(
        [DX_PATH, "search", group_name, "--type", "group", "--json"],
        capture_output=True, text=True, timeout=30
    )
    try:
        data = json.loads(result.stdout)
        groups = data.get("results", {}).get("group", [])
        if groups:
            return str(groups[0].get("id") or groups[0].get("gid", ""))
    except:
        pass
    return None

def summarize_with_ai(group_name, msgs, target_date):
    """用 AI 总结消息（通过 OpenClaw message tool 发送给自己，或直接打印）"""
    my_msgs = [m for m in msgs if m.get("sender", {}).get("uid") == MY_UID]
    formatted = format_msgs_for_ai(msgs)
    
    print(f"\n{'='*60}", file=sys.stderr)
    print(f"群: {group_name} | 日期: {target_date} | 共 {len(msgs)} 条", file=sys.stderr)
    print(f"仁清发言: {len(my_msgs)} 条", file=sys.stderr)
    
    # 输出结构化数据供上层使用
    return {
        "group_name": group_name,
        "date": str(target_date),
        "total": len(msgs),
        "my_count": len(my_msgs),
        "my_msgs": [
            {
                "time": m.get("time", "")[:16],
                "text": m.get("content", {}).get("text", "")[:200]
            } for m in my_msgs
        ],
        "formatted": formatted,
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="大象群消息总结")
    parser.add_argument("--groups", help="群名列表，逗号分隔")
    parser.add_argument("--gids", help="群 gid 列表，逗号分隔")
    parser.add_argument("--date", default=str(date.today()), help="日期 YYYY-MM-DD 或 today")
    parser.add_argument("--limit", type=int, default=300)
    parser.add_argument("--json-out", action="store_true", help="输出 JSON（供 Claude 处理）")
    args = parser.parse_args()

    if args.date == "today":
        args.date = str(date.today())

    targets = []
    if args.gids:
        for gid in args.gids.split(","):
            gid = gid.strip()
            name = next((k for k, v in KNOWN_GIDS.items() if v == gid), gid)
            targets.append((name, gid))
    elif args.groups:
        for gname in args.groups.split(","):
            gname = gname.strip()
            gid = resolve_gid(gname)
            if not gid:
                print(f"[WARN] 找不到群: {gname}", file=sys.stderr)
                continue
            targets.append((gname, gid))
    else:
        # 默认处理两个主要群
        for name, gid in KNOWN_GIDS.items():
            targets.append((name, gid))

    results = []
    for name, gid in targets:
        msgs = fetch(gid, args.date, args.limit)
        summary = summarize_with_ai(name, msgs, args.date)
        results.append(summary)

    if args.json_out:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        # 打印可读格式
        for r in results:
            print(f"\n📊 {r['group_name']} | {r['date']} | {r['total']} 条消息")
            if r['my_msgs']:
                print(f"\n💬 仁清今天说了 ({r['my_count']} 条):")
                for m in r['my_msgs'][:10]:
                    print(f"  [{m['time']}] {m['text'][:100]}")
            else:
                print("\n💬 仁清今天无发言")
            print(f"\n📝 消息预览（前 10 条）:")
            for line in r['formatted'].split('\n')[:10]:
                print(f"  {line}")
