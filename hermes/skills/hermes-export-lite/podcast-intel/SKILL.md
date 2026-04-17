# podcast-intel

高效播客内容检索与提炼工具，专为调研场景设计。目标：节省 40-60% token 消耗，直接输出可复制进调研报告的素材包。

## 触发时机

当用户提到以下关键词时激活此 skill：
- 播客、podcast、访谈、对话节目
- "搜索播客"、"播客摘要"、"播客内容"
- 具体节目名：Latent Space、Lex Fridman、a16z、硅谷101

## 使用方式

### 基本用法

```bash
python3 scripts/fetch_podcast.py \
  --query "AI agent skills" \
  --top 5 \
  --sources all
```

### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--query` / `-q` | 搜索关键词（必填） | - |
| `--top` / `-n` | 返回最多 N 个结果 | 5 |
| `--sources` | 数据源：`latent_space`, `lex`, `a16z`, `all` | `all` |
| `--context-chars` | 每个段落上下文字符数 | 600 |
| `--output` / `-o` | 输出文件路径（不指定则打印到 stdout） | - |

### 示例

```bash
# 搜索 AI agent 相关播客
python3 scripts/fetch_podcast.py \
  --query "AI agent autonomous" --top 3 --sources latent_space

# 全量搜索
python3 scripts/fetch_podcast.py \
  --query "openclaw skills ecosystem" --top 5 --sources all
```

## 输出格式

输出为结构化 Markdown 素材包，包含：
- 来源元数据（节目名、发布时间、原文链接）
- 相关段落（带相关度分数）
- Token 节省估算

## 数据源

| 源 | 标识 | 获取方式 |
|----|------|----------|
| Latent Space | `latent_space` | Substack API |
| Lex Fridman | `lex` | RSS + 文章页 |
| a16z | `a16z` | RSS 抓取 |
| 网络搜索 | 自动 fallback | web_search |

## 工作原理

1. 并行查询各数据源 API/RSS
2. web_fetch 抓取文章/transcript 页面  
3. segment_extractor.py 按关键词定位上下文 ±300 字
4. Jaccard 相似度去重（>0.7 合并）
5. 按关键词覆盖率排序，输出 Top N

---

## 小宇宙抓取（中文播客）

直接抓取小宇宙单集内容（无需登录，获取 shownotes + 时间线 + 金句）：

```bash
# 抓取单集，输出 Markdown
python3 scripts/xiaoyuzhou_fetch.py \
  https://www.xiaoyuzhoufm.com/episode/<id>

# 保存到文件
python3 scripts/xiaoyuzhou_fetch.py <url> -o output.md

# 输出原始 JSON（看所有字段）
python3 scripts/xiaoyuzhou_fetch.py <url> --json
```

**支持内容**：节目介绍、关键要点、金句、时间线（章节）、播客主介绍
**限制**：逐字稿需登录后获取（可注入 cookie 扩展）

触发词：小宇宙、xiaoyuzhou、播客链接（xiaoyuzhoufm.com）
