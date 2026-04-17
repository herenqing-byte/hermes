---
name: xiaohongshu-reader
description: 搜索小红书笔记、查看笔记详情和评论，对比分析内容。当用户想搜索小红书、对比笔记、查看评论、分析内容时使用。触发词：小红书、红书、XHS、搜笔记、看笔记、笔记详情、笔记评论、小红书搜索。
---

# 小红书 Reader

小红书页面内容由 JS 动态渲染，web_fetch 无法直接获取笔记列表。以下是 token 消耗从低到高的方案，按顺序尝试。

## 方案一：通过 Google 搜索（最轻量）

用 web_search 搜索，Google 会索引小红书公开笔记：

```
site:xiaohongshu.com <关键词>
```

或者：

```
小红书 <关键词> 笔记
```

从搜索结果的 snippet 中提取标题、摘要、链接，通常够用于对比分析。

## 方案二：抓取笔记详情页

拿到笔记 URL 后（格式：`https://www.xiaohongshu.com/explore/<note_id>`），用 web_fetch 抓取。

小红书笔记详情页有 SSR 渲染部分，可以提取：
- 标题、正文
- 标签（#话题）
- 作者名
- 部分互动数据

抓取时用 `extractMode: text` 减少 token。

## 方案三：通过分享链接

用户提供小红书 App 分享的短链（`https://xhslink.com/xxx`），web_fetch 跟随跳转后抓取详情页。

## 对比多篇笔记

1. 先用 web_search 搜索，拿到 3-5 个笔记链接
2. 按需 web_fetch 抓取详情（不超过 5 篇，节省 token）
3. 用表格对比：标题 / 核心观点 / 标签 / 互动数

## 评论获取

评论通过 API 异步加载，web_fetch 通常拿不到。
- 如果用户需要评论，建议让用户复制粘贴评论内容过来分析
- 或使用 agent-browser skill（需要 Playwright）

## 注意

- 优先用方案一，够用就不要多抓
- 遇到登录墙时告知用户，不要重试
- 不要循环抓取大量页面
