---
name: daxiang-reader
description: 读取大象(Daxiang)群聊消息。通过 CDP 自动化浏览器，导航到指定群聊，自动展开被折叠的长消息（点击查看全部内容），提取干净的消息列表（仅含时间、发送者、正文）。当需要从大象群聊获取消息内容、提取群聊数据、读取机器人推送的指标数据时使用。触发词：读取大象消息、大象群聊消息、提取群聊内容、大象群消息。

metadata:
  skillhub.creator: "xuyouji"
  skillhub.updater: "xuyouji"
  skillhub.version: "V1"
  skillhub.source: "FRIDAY Skillhub"
  skillhub.skill_id: "3964"
---

# 大象群聊消息读取

## 核心脚本

```bash
python3 scripts/dx_read_messages.py <群聊URL> [-o output.json] [--date MM-DD] [--scroll N] [--no-expand]
```

### 参数

| 参数 | 说明 |
|------|------|
| `chat_url` | 大象群聊 URL，如 `https://x.sankuai.com/chat/66926287794?type=groupchat` |
| `-o` / `--output` | 输出 JSON 路径（默认 `/tmp/dx_messages.json`） |
| `--date MM-DD` | **推荐**。目标日期前缀，如 `03-11`。智能滚动到该日期即停，只展开和提取该日期的消息。支持逗号分隔多个日期如 `03-10,03-11` |
| `--max-scroll N` | `--date` 模式下最大滚动次数（默认 50） |
| `--scroll N` | 向上滚动 N 次加载更多历史消息（与 `--date` 互斥，`--date` 优先） |
| `--no-expand` | 不展开被折叠的长消息 |
| `--no-navigate` | 假设已在目标页面，跳过导航 |
| `--wait N` | 页面加载等待秒数（默认 6） |

### 输出格式

```json
[
  {"time": "03-11 09:30", "sender": "大象机器人", "text": "【直连日报指标】2026-03-11\n..."},
  {"time": "03-11 09:22", "sender": "大象机器人", "text": "【日报】2026-03-10\n自建\n[先占座-成功率|https://raptor...]:91.74% -> 92.81% ✅\n..."}
]
```

### 关键改进

1. **`--date` 智能滚动**：指定目标日期后，只滚动到该日期即停，不会加载大量无关历史消息。大幅提升读取速度。
2. **完整消息提取**：链接保留为 `[文字|URL]` 格式，不丢失链接信息。
3. **JS 直接展开**：用 `span.click()` 直接展开折叠消息，不依赖鼠标坐标点击，可靠性更高。且指定 `--date` 时只展开目标日期的消息。

## 关键机制

### 折叠消息展开

大象会折叠过长的消息，在底部显示 `span.show-long-text`（"点击查看全部内容"）。
脚本通过 JS `span.click()` 直接展开，无需滚动到可视区域。指定 `--date` 时只展开目标日期的消息，避免不必要的展开操作。

### DOM 结构

```
.bubble-item                    ← 每条消息
  .message-item
    .right-content
      .bubble-item-time         ← 时间 "03-11 09:30"
      .wrapper-message-container
        .message-container
          .dx-message-text      ← 消息内容（含 <a class="link"> 链接）
          span.show-long-text   ← "点击查看全部内容"（如有）
```

### 典型用法

```bash
# 只读取昨天的消息（推荐，最快）
python3 scripts/dx_read_messages.py "https://x.sankuai.com/chat/66926287794?type=groupchat" --date 03-11

# 读取多天消息
python3 scripts/dx_read_messages.py "https://x.sankuai.com/chat/66926287794?type=groupchat" --date 03-10,03-11

# 传统方式：滚动N次加载所有
python3 scripts/dx_read_messages.py "https://x.sankuai.com/chat/66926287794?type=groupchat" --scroll 10
```

## 已知群聊 URL

| 群名 | URL |
|------|-----|
| 火车票供给组沟通群 | `https://x.sankuai.com/chat/66926287794?type=groupchat` |
| 未来编码实验室 | `https://x.sankuai.com/chat/68922311775?type=groupchat` |
| AI应用讨论一群 | `https://x.sankuai.com/chat/66680558681?type=groupchat` |
| 业务研发平台AI coding达人团 | `https://x.sankuai.com/chat/69624577776?type=groupchat` |
| 业务研发平台AI架构组 | `https://x.sankuai.com/chat/69361094794?type=groupchat` |
| 履约AI Coding虚拟组织周会群 | `https://x.sankuai.com/chat/69628818051?type=groupchat` |
| 头部客户BP | `https://x.sankuai.com/chat/69474738784?type=groupchat` |
| 大象个人助理CatClaw版尝鲜2群 | `https://x.sankuai.com/chat/70389490458?type=groupchat` |

> 遇到新群时，用下面的「查找群聊 URL」流程拿到 URL 后，补充到此表。

## 查找群聊 URL（当上表没有时）

**唯一可靠方式：用搜索框。不要尝试在会话列表里用 JS click。**

```
1. browser navigate → https://x.sankuai.com
2. browser snapshot → 找到搜索框 ref（textbox "搜索"）
3. browser act → click 搜索框，type 群名
4. wait 2s → snapshot → 在搜索结果的「群组」区域找到高亮群名
5. browser act → evaluate: 找到 em 元素（textContent === 群名），closest('div,li,a,span') 后 click
6. wait 2s → evaluate window.location.href → 拿到群聊 URL
7. 将 URL 补充到上面的「已知群聊 URL」表
```

### 踩坑记录（禁止重复犯错）

- 大象左侧会话列表中，**置顶区和无未读消息的群**在 snapshot 里只出现在纯 text 节点中，没有独立的 listitem ref
- 用 `comp-top-session` class 匹配到的是置顶组容器，click 不会进入具体群聊
- 大象是 SPA，点击后 URL 可能不立即变化，**必须 wait 2s 再检查**
- **永远不要在会话列表上反复 JS querySelector + click 试探**，直接走搜索

## 注意事项

- 需要浏览器已通过 CDP 9222 端口可用
- 需要已登录大象（SSO 认证通过）
- `--date` 模式下日期比较是简单字符串比较，适用于同年内的日期
- 跨年消息日期格式可能带年份前缀（如 `2025-12-31 09:22`），此时 `--date` 应传完整前缀如 `2025-12-31`
