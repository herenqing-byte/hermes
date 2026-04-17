---
name: wechat-article
description: 抓取并分析微信公众号文章（mp.weixin.qq.com 链接）。微信公众号对桌面浏览器有验证拦截，必须用 iPhone UA 通过 curl 抓取，不能用 browser 工具直接打开。
---

# wechat-article - 微信公众号文章抓取

## 核心方法

微信公众号页面对桌面浏览器做验证拦截，但对 iOS 微信内置浏览器的请求不做验证。
**必须用 iPhone User-Agent 通过 curl 抓取，不能用 browser 工具直接打开。**

## 抓取命令

```bash
curl -s -L \
  -H 'User-Agent: Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1 MicroMessenger/8.0.43' \
  -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8' \
  -H 'Accept-Language: zh-CN,zh;q=0.9' \
  '<微信文章URL>' | python3 -c "
import sys, re
html = sys.stdin.read()

# 提取标题
og_title = re.search(r'property=\"og:title\" content=\"([^\"]+)\"', html)
print('标题:', og_title.group(1) if og_title else 'N/A')

# 提取正文
content = re.search(r'id=\"js_content\"[^>]*>(.*)', html, re.DOTALL)
if content:
    text = content.group(1)
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
    text = re.sub(r'</p>', '\n', text)
    text = re.sub(r'<br\s*/?>', '\n', text)
    text = re.sub(r'</section>', '\n', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'&amp;', '&', text)
    text = re.sub(r'&lt;', '<', text)
    text = re.sub(r'&gt;', '>', text)
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    print(text.strip())
else:
    print('NO CONTENT FOUND')
" > /tmp/wechat_article.txt
wc -c /tmp/wechat_article.txt
```

## 保存到文件再分析

内容较长时，建议先保存到文件：

```bash
# 保存全文
curl ... > /tmp/wechat_article.txt

# 分段读取
cat /tmp/wechat_article.txt | python3 -c "import sys; print(sys.stdin.read()[0:6000])"
cat /tmp/wechat_article.txt | python3 -c "import sys; print(sys.stdin.read()[6000:12000])"
# 以此类推
```

## 验证是否抓到内容

- 成功：文件有几万字，能看到正文内容
- 失败（被拦截）：只有几十字，内容是"环境异常，完成验证后即可继续访问"

失败原因通常是 URL 有问题或文章已删除，此时告知用户无法访问。

## 注意事项

- web_fetch 和 browser 工具**无法**绕过微信验证，不要尝试
- 文章末尾通常有"还有大量内容只有视频/播客有"等提示，属于公众号节选，正文不完整属正常
- og:title 和 og:description 在 HTML head 部分，即使拦截也能读到摘要信息
