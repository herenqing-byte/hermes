---
name: wx-article
description: 读取微信公众号文章内容。当用户发来 mp.weixin.qq.com 链接时，绕过验证码直接提取全文。触发词：微信文章、公众号链接、mp.weixin.qq.com、帮我看这篇文章、公众号文章分析。
---

# wx-article — 微信公众号文章读取

微信公众号文章在沙箱/自动化环境中会触发验证码。本 skill 通过**移动端 UA 直接 HTTP 请求**绕过验证。

## 核心方案（无需浏览器）

```bash
python3 /Users/herenqing/.hermes/workspaces/openclaw-migration/tools/fetch_wx_article.py "https://mp.weixin.qq.com/s/xxx"
```

工具位置：`/Users/herenqing/.hermes/workspaces/openclaw-migration/tools/fetch_wx_article.py`

## 工作原理

- **不使用 browser 工具**（会触发验证码）
- 用移动端 User-Agent 发 HTTP 请求，绕过大多数验证码拦截
- 自动从浏览器 CDP (127.0.0.1:9222) 提取 mp.weixin.qq.com cookie（如有）
- 提取 `id="js_content"` 区块内容并清理 HTML 标签

## 标准流程

1. 用户发来 mp.weixin.qq.com 链接
2. 调用工具获取全文：
   ```bash
   python3 /Users/herenqing/.hermes/workspaces/openclaw-migration/tools/fetch_wx_article.py "<url>"
   ```
3. 按用户需求处理内容（分析/总结/提炼观点）

## 如果失败（备用方案）

- 被验证码拦截 → 让用户粘贴文章文字
- 仅粉丝可读 → 需要微信登录态（cookie），暂无法绕过
- 网络超时 → 重试一次

## 注意

- **绝对不要用 browser 工具**去开微信文章链接，会一直卡在验证码页面
- web_fetch 也不行（返回空壳 HTML）
- 只有 Python HTTP 请求 + 移动端 UA 有效
