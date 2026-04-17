---
name: sankuai-playwright-skill
description: 面向美团内网与外网页面的浏览器自动化技能。优先使用稳定入口 `tcx web-inspect` 或公开 Python API `turing_codex.web_inspect` 做页面响应定位；涉及学城文档处理时，先使用 `sankuai-km-docs`。
---

# 浏览器自动化 Skill

## 适用场景

- 定位页面上的关键字来自哪个网络响应
- 执行页面级交互、截图、DOM 检查、按钮点击或表单填写
- 访问外网站点，或访问已明确完成登录的内网站点

## 选择入口

- 学城文档读取、搜索、层级查看、创建、删除、DrawIO 提取等需求：切换到 `sankuai-km-docs`
- 只需要定位关键字来自哪个响应：优先使用 `tcx web-inspect`
- 说明：`tcx` 是 `turing-codex` 的等价简写，以下命令示例统一使用 `tcx`
- 需要在 Python 代码中做同类页面分析：使用 `turing_codex.web_inspect`
- 用户明确要求编写浏览器自动化脚本时：使用标准 Python Playwright
- 不要把 Playwright 作为学城专项能力失败后的默认兜底路径

## 前置

- 访问学城前先执行：`tcx login km`
- 访问其他内网站点时，按目标系统执行对应登录命令，例如：`tcx login ones`、`tcx login code`
- 若希望一次性预热多个系统登录态，可执行：`tcx login all`
- 使用前可先查看帮助：`tcx web-inspect --help`

## 路径一：命令行

当目标是“定位页面关键字来自哪个网络响应”时，优先使用：

- `tcx web-inspect --url <url> --keyword <keyword>`

### 命令行示例

```bash
tcx web-inspect \
  --url 'https://dev.sankuai.com/...' \
  --keyword 'demo'
```

```bash
tcx web-inspect \
  --url 'https://dev.sankuai.com/...' \
  --keyword 'demo' \
  --top-n 20 \
  --head
```

## 路径二：Python API

在已安装 `mt-turing-codex` 的 Python 环境中，可使用公开导入面：

```python
from turing_codex.web_inspect import WebInspectRequest, WebInspectService, item_to_dict
```

### Python 示例

```python
import asyncio
import json

from turing_codex.web_inspect import WebInspectRequest, WebInspectService, item_to_dict


async def main() -> None:
    service = WebInspectService()
    result = await service.run(
        WebInspectRequest(
            url="https://dev.sankuai.com/...",
            keyword="demo",
            top_n=10,
            head=False,
            timeout_seconds=30,
            wait_after_load_seconds=3,
        )
    )
    print(json.dumps([item_to_dict(item) for item in result.items], ensure_ascii=False, indent=2))


asyncio.run(main())
```

## 路径三：标准 Python Playwright

仅在用户明确要求编写浏览器自动化脚本，或任务本身就是页面交互自动化时使用。

### 使用建议

- 外网页面可直接使用标准 Playwright 脚本
- 对内网页面，先确保已经完成对应系统登录
- 若脚本运行后仍要求重新认证，可改用有头模式，在浏览器中完成登录后再继续

### 通用模板

```python
import asyncio
from playwright.async_api import async_playwright

TARGET_URL = "https://example.com"
HEADLESS = False


async def main() -> None:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=HEADLESS)
        page = await browser.new_page()
        await page.goto(TARGET_URL, wait_until="networkidle")
        print(await page.title())
        await page.screenshot(path="./playwright-screenshot.png", full_page=True)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
```

## 常见问题

- 访问学城文档却只是想读正文、搜文档、改文档：
  - 不要切到 Playwright，改用 `sankuai-km-docs`
- 页面分析只需要定位响应来源：
  - 优先用 `tcx web-inspect` 或 `turing_codex.web_inspect`
- 内网页面提示未登录：
  - 先执行对应的 `tcx login ...`，再重试

## 回复规范

- 先判断任务是不是学城文档处理；如果是，优先切换到 `sankuai-km-docs`
- 先判断是否可用 `web-inspect` / `turing_codex.web_inspect` 解决；能解决就不要直接写 Playwright 脚本
- 只有在用户明确要求浏览器自动化时，才给出 Playwright 代码
