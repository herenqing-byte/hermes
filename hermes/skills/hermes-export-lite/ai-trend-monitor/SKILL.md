---
name: ai-trend-monitor
description: AI 行业趋势监控 Agent。追踪海外 AI 领域关键变化：X/Twitter 大佬观点碰撞、arXiv SOTA 论文、HN 热议、AI Coding 工具动态、OpenClaw 生态、播客深度访谈、博客/Newsletter。生成深度中文日报/周报并推送到大象。触发词：AI趋势、AI日报、AI周报、行业动态、tech news、AI monitor、trend report、生成AI日报、AI简报、播客摘要。
---

# AI 行业趋势监控

## 采集脚本

| 脚本 | 信息源 | 用法 |
|------|--------|------|
| `scripts/fetch_x.py` | X/Twitter (Nitter RSS + Catclaw fallback, 70 accounts) | `python3 scripts/fetch_x.py [hours] [json\|md]` |
| `scripts/fetch_arxiv.py` | arXiv AI 论文 | `python3 scripts/fetch_arxiv.py [max]` |
| `scripts/fetch_hn.py` | Hacker News AI 热帖 | `python3 scripts/fetch_hn.py` |
| `scripts/fetch_podcasts.py` | 播客 (Lex Fridman, Dwarkesh, Latent Space 等) | `python3 scripts/fetch_podcasts.py` |
| `scripts/fetch_blogs.py` | 博客 & Newsletter (16 sources) | `python3 scripts/fetch_blogs.py` |

## X/Twitter 采集详情

### 采集规则
- **每日扫描 70 个账号**，只获取最近 24 小时内的推文
- **双数据源**：优先 Nitter RSS，全部失败时自动降级到 Catclaw 搜索 API
- **时间过滤**：RSS 解析时严格按 pubDate 过滤，只保留时间窗口内的内容

### 输出分类（5 类）
| 分类 | 标签 | 说明 |
|------|------|------|
| leaders | 🏢 AI 公司领袖 | CEO/创始人级别，决策和战略方向 |
| researchers | 🔬 顶级研究员 | 学术和工业界研究领军人物 |
| coding | 💻 AI Coding | AI 编程工具、产品和实践者 |
| commentators | 🎙️ 评论员/意见领袖 | 播客主、博主、行业评论 |
| openclaw | 🐾 OpenClaw 生态 | OpenClaw 官方和核心团队 |

### 输出格式
- **JSON 模式**（默认）：`python3 scripts/fetch_x.py 24` — 结构化数据，含 tweets 列表和统计
- **Markdown 模式**：`python3 scripts/fetch_x.py 24 md` — 按分类输出，适合直接嵌入日报

### 每条推文格式要求
- 来源链接 + 发布日期
- 人物背景（首次出现时附 who 字段描述）
- 格式参考月报：`memory/ai-trends/twitter-monthly-analysis-2026-02.md`

### Catclaw Fallback 机制
当所有 Nitter 实例对某账号不可用时，自动通过 Catclaw 搜索 API 尝试：
1. `from:{handle} site:x.com since:{yesterday}`
2. `"{handle}" site:x.com`
3. `@{handle} site:twitter.com`

## 追踪维度

### 1. AI 公司 & 领袖
Sam Altman, Dario Amodei, Yann LeCun, Andrew Ng, Jeff Dean, Demis Hassabis, Satya Nadella, Arav Srinivas, Mustafa Suleyman

### 2. 顶级研究员
Andrej Karpathy, Jim Fan, François Chollet, Ilya Sutskever, Jack Clark, Wojciech Zaremba, Tri Dao, Tim Dettmers, Lilian Weng, Noam Brown, Mira Murati, Sebastien Bubeck, Amanda Askell, Chris Olah, Jan Leike, Sholto Douglas, Oriol Vinyals, Ian Goodfellow, Geoffrey Hinton, Fei-Fei Li, Soumith Chintala 等 27 人

### 3. AI Coding 赛道
Cursor, Windsurf, Cognition (Devin), GitHub Copilot, Cline, Sourcegraph, v0, bolt.new, Claude Code, OpenClaw

### 4. 播客
Lex Fridman, Dwarkesh Patel, Latent Space, AI Explained, ML Street Talk, No Priors, Practical AI

### 5. 博客 & Newsletter
Simon Willison, Lilian Weng, Google AI, HuggingFace, Import AI, Ahead of AI, Chip Huyen

### 6. OpenClaw 生态
OpenClaw 官方动态、社区更新

## ⚠️ 日报生成核心要求

### 时效性 & 去重（强制）
1. **严格时间窗口**：只收录 2 天内发布的内容。超过 2 天的文章一律丢弃，无论多重要。
2. **去重规则**：
   - 同一事件/话题的多篇报道，只保留信息量最大的 1 篇
   - **但如果**同一主题有不同观点/角度，则合并展示各方观点碰撞
   - 判断标准：标题相似度高且核心事实相同 → 去重；核心事实相同但立场/观点不同 → 保留并标注为"观点碰撞"
3. **日期标注**：每条内容必须标注发布日期，无法确认日期的标注"日期不详"

### 来源链接 + 发布日期（强制）
**每条资讯、每个事件、每篇论文、每期播客、每篇博客都必须同时附上：**
1. **原始来源链接** — 方便读者点击查看原文
2. **发布日期** — 该内容的实际发布/发表日期（精确到天）

**链接格式要求：**
- HN 帖子：附 `https://news.ycombinator.com/item?id=XXX` 链接
- arXiv 论文：附 `https://arxiv.org/abs/XXXX.XXXXX` 链接
- 播客：附播客平台链接（YouTube/Spotify/Apple Podcasts）
- 博客/Newsletter：附原文 URL
- X/Twitter：附推文链接或 Nitter 链接
- 微信公众号文章：附 mp.weixin.qq.com 链接（如有）
- 如果采集时未获得链接，标注"[链接待补]"而不是省略

**日期标注方式：**
在每条内容的标题或来源行旁标注发布日期，格式为 `(YYYY-MM-DD)`。例如：
- `### GPT-5.4 发布 (2026-03-05)` 
- `来源：[Simon Willison's Blog](https://simonwillison.net/...) (2026-03-06)`
- 如果无法确认发布日期，标注 `(日期不详)`

### 深度 > 广度
不要只报标题。对于重大事件必须：
1. **事件本身**：发生了什么、关键参数/特性
2. **各方观点碰撞**：谁赞、谁批评、谁持观望态度，引用原文
3. **行业影响分析**：对竞争格局、开发者、商业应用的影响
4. **争议点**：社区里的主要分歧是什么
### AI Coding 单独成节
每期必须包含 AI Coding 板块

### 人物背景标注（强制）
**首次提到某人时，必须附上其背景信息**，包括：
- 所属公司/机构
- 职位/角色
- 为什么他的观点值得关注（一句话）

格式示例：
- `**Simon Willison**（Datasette 创始人，Django 核心开发者，AI 工具链评论最具影响力的独立博主）`
- `**Bruce Schneier**（哈佛肯尼迪学院研究员，知名安全专家，著有《Applied Cryptography》等）`
- `**Jeremy Howard**（fast.ai 联合创始人，前 Kaggle 总裁，深度学习教育领域标杆人物）`

同一期日报中同一人物只需在首次出现时标注，后续提及可省略。

### 观点引用格式
> **@handle (身份)**: "原文核心句子..."
> — 解读/上下文补充

## 日报模板

```markdown
# 🤖 AI 日报 — YYYY-MM-DD

## 🔥 重大事件深度解读
### [事件标题]
**发生了什么 / 各方反应 / 影响判断**

## 💻 AI Coding 动态

## 🐦 大佬观点精选

## 📄 论文精选

## 🎙️ 播客 & 博客精选
（本周新发布的重要播客集和博客文章）

### ✍️ 播客写作风格（强制，每期必须遵循）

每期播客用叙事散文格式，**禁止用 bullet list 列功能清单**：

```
核心观点：[一句话判断——不是内容描述，而是观点]

[嘉宾名] 曾担任 [经历]，在那时就产生了一个强烈判断：[背景故事2-3句，说明观点是怎么形成的]

[产品/技术]的核心设计哲学是：[用类比或比喻说清架构，1-2句]

"[直接引用嘉宾原话]"

[重点描述最独特的1-2个功能/设计，聚焦差异点，不列功能清单]

对于配送、调度等复杂系统从业者而言，[具体行业启示，1-3句，说清楚借鉴什么，禁止"值得关注"等空话]
```

**风格原则：**
- 判断先行，背景做支撑（倒装结构，不要先铺背景再说观点）
- 叙事流畅，像读一篇科技评论，不是 PPT 要点
- 善用类比（如：Sidekick 是内核，agent 是应用层，就像操作系统的内核态和用户态）
- 嘉宾原话中英文皆可，1-2句

## 💬 社区热议 (HN)

## 🐾 OpenClaw 动态
（如有）
```

## 周报模板

每周一生成，汇总过去 7 天：
```markdown
# 🤖 AI 周报 — YYYY 第 XX 周

## 📊 本周关键趋势
（什么在升温/降温、行业格局变化）

## 🏆 本周最重大事件 Top 3

## 💻 AI Coding 周回顾

## 🎙️ 本周必听播客

## 📖 本周必读文章

## 🔮 下周关注
（预告、期待发布的东西）
```

## 存储

```
memory/ai-trends/
├── YYYY-MM-DD.md     # 每日报告
├── weekly/YYYY-WXX.md # 每周总结
└── raw/              # 原始 JSON (可选)
```

## 微信公众号追踪

### AI + 科技
机器之心、AI科技评论、量子位、InfoQ、阿里开发者、哔哩哔哩技术、滴滴技术、Founder Park、AIGC开放社区、赛博禅心、浅黑科技、数字生命卡兹克、语言即世界、tuzhuxi、开柒、张晓东西南北、十字路口Crossing

### 商业 / 投资
36氪、晚点LatePost、暗涌Waves、42章经、于冬琪商业笔记、正和岛、刘润、硅星人Pro、海外独角兽、Z Potentials、走马财经、大厂日爆、开曼4000、香帅的金融江湖、方伟看十年、北美华商会、十三邀、绕梁说、渤海小吏

### 采集脚本
`scripts/fetch_wechat.py` — 通过 Catclaw 搜索 (百度) 搜索 mp.weixin.qq.com 获取最新文章

### 日报中的呈现
```markdown
## 📱 国内公众号精选
### AI + 科技
- [标题] — 一句话摘要 (公众号名)
### 商业洞察
- [标题] — 一句话摘要 (公众号名)
```
