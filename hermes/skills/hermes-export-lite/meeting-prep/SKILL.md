# meeting-prep

扫描日历，提前 30 分钟发送会前提醒，包含 KM Wiki 内容三层 AI 分析 + 上下文关联检索。

## 功能

- 每 30 分钟扫描未来 2 小时内的会议
- 检测会议备注（memo）中是否包含 `km.sankuai.com` 链接
- 提前 25–35 分钟触发提醒（每个会议只提醒一次）
- AI 按三层结构分析 KM 内容 + 检索历史上下文
- 通过大象发送给仁清（single_941328）

## 提醒消息格式

```
📅 会前提醒：[会议名称]
⏰ 30分钟后开始 | [时间] | [地点/链接]

📋 会议背景
[2-3句说清楚为什么开这个会，背景和目标]

🔑 材料关键问题
• [重要决策点或争议点]
• [风险点或存疑事项]
• [影响落地的关键问题]

❓ 建议主动询问
• [作为履约平台技术负责人应主动提出的技术/业务问题]
• [涉及配送系统架构/算法/资源/跨团队协作的关注点]
• [推动决策或澄清边界的具体问题]

🔍 相关历史上下文（有则显示，无则省略整节）
• [调研知识库 / 历史记忆 / 学城文档中找到的相关内容]

📎 原始材料：[KM链接]
```

## 文件结构

```
./
├── SKILL.md
└── scripts/
    ├── check_meetings.py   # 核心脚本：扫描日历 + 读 KM + 上下文检索
    └── requirements.txt
```

## 状态文件

已提醒记录：`~/.meeting-prep/reminded.json`
格式：`{"schedule_id": "ISO8601提醒时间", ...}`

## 手动测试

```bash
# 查看今天含 KM 链接的所有会议（不受时间窗口限制，不发消息）
python3 scripts/check_meetings.py --dry-run

# 指定日期测试
python3 scripts/check_meetings.py --dry-run --date 2026-03-23
```

## Cron 安装命令

```bash
openclaw cron add \
  --name "会前材料提醒" \
  --cron "*/30 * * * *" \
  --tz "Asia/Shanghai" \
  --session isolated \
  --message "执行会前材料提醒任务。

## 第一步：运行脚本

运行以下命令，获取当前需要提醒的会议（JSON 格式输出）：

  python3 scripts/check_meetings.py

## 第二步：判断是否需要发送

- 如果输出为空列表 []，说明当前没有需要提醒的会议，直接回复 NO_REPLY，不做任何操作。
- 如果有一条或多条会议，对**每条**按第三步发送大象消息。

## 第三步：生成并发送提醒消息

对脚本输出的每个会议条目，使用 message 工具（channel: daxiang, target: single_941328）发送以下格式的消息：

---
📅 会前提醒：{title}
⏰ 30分钟后开始 | {start_str} | {location 或 meeting_url}

📋 会议背景
根据 km_links[].content 的内容，用 2-3 句话说清楚：
• 这个会议的背景（项目/问题/决策背景）
• 这次会议要讨论/解决什么
• 预期达成什么结论或决策

🔑 材料关键问题
从 km_links[].content 中提炼 3-5 个关键问题，聚焦于：
• 文档中尚未决策的重要事项
• 方案中的风险点、依赖项、存疑假设
• 需要在会议上明确的边界条件

❓ 建议主动询问
基于何仁清的角色（履约平台技术负责人，关注配送系统/调度优化/AI Agent落地），列出 2-3 个他在这个会议上应该主动提出的问题：
• 涉及技术架构、资源、跨团队协作、落地可行性的问题
• 推动决策、澄清职责边界的问题
• 可能影响配送系统长期发展的战略问题

（如果 context.research / context.memory / context.citadel 任何一项非空，则追加以下节：）

🔍 相关历史上下文
根据 context 字段内容，列出相关历史信息：
• context.research 中的报告：「{title}」— {summary 前100字}（路径：{path}）
• context.memory 中的记忆：你曾在 {date} 讨论过：{snippet}
• context.citadel 中的文档：[{title}]({url}) — {snippet}
注意：只展示实际找到的内容，没有找到则整节不显示，不写「未找到」

📎 原始材料：{km_links[0].url}（多个链接时逐行列出）
---

## 重要注意事项

- km_links[].content 字段已包含 KM 文档内容，直接基于该字段生成分析，**不需要再次访问 KM**
- keywords 字段是脚本已提取的检索关键词，供参考
- 每个会议只发一条消息（脚本内部已做去重，状态已在脚本运行时写入）
- 何仁清的背景：美团履约平台技术负责人，关注智能配送/调度优化/ETA/骑手系统/AI Agent落地
" \
  --channel daxiang \
  --to "single_941328"
```
