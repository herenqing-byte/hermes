---
name: daxiang-group-summary
description: 大象群消息监控与总结。给定群名/gid，拉取当天消息，生成三部分摘要：全群讨论主题、仁清(herenqing)的发言要点、重要To-Do。触发词：群消息总结、群里讨论了什么、仁清今天说了什么、AI群日报、群聊摘要。
---

# 大象群消息监控 Skill

## 功能
给定群名列表（或 gid），拉取当天消息，生成结构化总结，发送到仁清大象。

## 用法

### 方式一：Claude 直接调用

```python
# 1. 拉消息
import subprocess, json
result = subprocess.run(
    ["python3", "scripts/fetch_messages.py",
     "--gid", "66680558681", "--date", "2026-03-18", "--limit", "300"],
    capture_output=True, text=True
)
msgs = json.loads(result.stdout)

# 2. 过滤仁清发言
MY_UID = "941328"
my_msgs = [m for m in msgs if m.get("sender", {}).get("uid") == MY_UID]

# 3. 格式化后让 AI 总结（见下方 summarize.py）
```

### 方式二：命令行

```bash
python3 scripts/summarize.py \
  --groups "AI应用讨论一群,大象助理头部玩家交流群" \
  --date 2026-03-18
```

## 输出格式

```
📊 群消息日报 | 2026-03-18

【AI应用讨论一群】共 XX 条消息

🌐 今日热点话题
- 钉钉全面 CLI 化以支持 AI 调用
- OpenAI 推出 Codex Subagents 对抗 Claude Code
- ...

💬 仁清今天说了什么
- 17:30 回复了关于 xxx 的问题
- ...（如果当天无发言，显示"今日无发言"）

✅ 重要 To-Do
- [ ] xxx（来自 hh:mm 的讨论）
- ...
```

## 群 gid 参考
- AI应用讨论一群: `66680558681`
- 大象助理头部玩家交流群: `70428157100`
- AI时代组织和人才变革的讨论: (待确认，可用 dx search 获取)

## 仁清识别
- misId: `herenqing`
- uid: `941328`
- 大象 UID: `941328`（一致）

## 注意
- dx history 的 --from/--to 不做真正日期过滤，必须客户端按 `time` 字段过滤
- 图片消息（kind=image）只取 caption，无 caption 则跳过
- general 类消息取 summary 字段（卡片消息）
- 限制拉取 300-500 条以覆盖当天（活跃群消息量通常 <200 条/天）
