#!/usr/bin/env python3
"""
大象群消息拉取工具
用法:
  python3 fetch_messages.py --gid 66680558681 --date 2026-03-17 [--limit 500]
  python3 fetch_messages.py --group-name "AI应用讨论一群" --date today [--limit 500]
输出: JSON 格式的当天消息列表（stdout），meta 信息到 stderr
"""
import subprocess, json, sys, argparse, os, shutil
from datetime import datetime, date

DX_PATH = "/tmp/xm-cli/node_modules/.bin/dx"

def get_dx():
    if shutil.which("dx"):
        return "dx"
    if os.path.exists(DX_PATH):
        return DX_PATH
    raise RuntimeError("dx CLI not found")

def fetch_messages(gid, target_date=None, limit=500):
    dx = get_dx()
    try:
        result = subprocess.run(
            [dx, "history", "--gid", str(gid), "--limit", str(limit), "--json"],
            capture_output=True, text=True, timeout=120
        )
    except subprocess.TimeoutExpired:
        print(f"[ERROR] timeout for gid={gid}", file=sys.stderr)
        return []
    try:
        data = json.loads(result.stdout)
        if isinstance(data, dict):
            msgs = data.get("messages") or data.get("data") or data.get("list") or []
        else:
            msgs = data
    except Exception as e:
        print(f"[ERROR] JSON parse failed: {e}", file=sys.stderr)
        return []
    if target_date:
        date_str = str(target_date)
        filtered = [m for m in msgs if m.get("time","").startswith(date_str)]
        print(f"[INFO] gid={gid} total={len(msgs)} date={date_str} filtered={len(filtered)}", file=sys.stderr)
        return filtered
    return msgs

def resolve_gid(group_name):
    dx = get_dx()
    try:
        result = subprocess.run(
            [dx, "search", group_name, "--type", "group", "--json"],
            capture_output=True, text=True, timeout=30
        )
        data = json.loads(result.stdout)
        groups = data.get("results", {}).get("group", []) if isinstance(data, dict) else data
        if groups:
            return str(groups[0].get("id") or groups[0].get("gid",""))
    except Exception as e:
        print(f"[ERROR] search failed: {e}", file=sys.stderr)
    return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--gid")
    parser.add_argument("--group-name")
    parser.add_argument("--date", default=str(date.today()))
    parser.add_argument("--limit", type=int, default=500)
    args = parser.parse_args()
    if args.date == "today":
        args.date = str(date.today())
    gid = args.gid
    if not gid and args.group_name:
        gid = resolve_gid(args.group_name)
        if not gid:
            print(json.dumps({"error": f"找不到群: {args.group_name}"}))
            sys.exit(1)
    if not gid:
        print(json.dumps({"error": "必须提供 --gid 或 --group-name"}))
        sys.exit(1)
    msgs = fetch_messages(gid, args.date, args.limit)
    print(json.dumps(msgs, ensure_ascii=False, indent=2))
