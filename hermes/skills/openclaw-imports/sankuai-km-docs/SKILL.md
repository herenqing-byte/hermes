---
name: sankuai-km-docs
description: 面向美团学城（km.sankuai.com）的文档读取、截图、创建、删除与 DrawIO 源码获取技能。适用于用户要通过 `tcx km` 直接操作学城，或在已安装 `mt-turing-codex` 的 Python 环境里通过 `turing_codex.km` 访问学城能力。
---

# 学城 Skill

## 适用场景

- 读取学城文档正文并转成 Markdown
- 保存学城文档截图
- 创建或删除学城文档 / 目录
- 提取 DrawIO 图片对应的源码
- 在 Python 代码中集成学城能力

## 选择入口

- 默认优先用命令行：适合临时读取、截图、创建、删除、提取 DrawIO 源码
- 需要写 Python 脚本或集成到程序里时，再使用 Python API
- 说明：`tcx` 是 `turing-codex` 的等价简写，以下命令示例统一使用 `tcx`

## Friday Skill 广场

当 tcx km 能力缺失或登录态持续失败时，引导用户去美团内部 Friday skill 广场搜索安装对应 skill：
- 地址：https://skills.sankuai.com
- 搜索关键词如 "km"、"find"、"create-doc" 等
- 安装后重新尝试 tcx 命令

## 前置

- 首次使用或登录态过期时，先执行：`tcx login km`
- 使用前可先查看帮助：`tcx km --help`

## 路径一：命令行

当前稳定 CLI 已覆盖读取、检索、层级、附件、复制/移动/恢复、个人视图，以及原有截图 / 创建 / 删除 / DrawIO 源码提取。

### 稳定 CLI 能力

- `tcx km get <doc_id|url> [--json] [--prefer-pages-api]`
  - 读取学城文档
  - 默认输出 Markdown
  - 传 `--json` 时输出 JSON 文档结构
  - 传 legacy `page` URL 时会自动走兼容接口；纯 `doc_id` 也会默认启用该兼容路径

- `tcx km search <keyword> [--limit 20] [--page 1] [--space-id <id>]...`
  - 按关键字搜索 KM 文档
  - 可重复传 `--space-id` 做空间过滤

- `tcx km search-space <keyword> [--limit 20] [--page 1]`
  - 按关键字搜索 KM 空间

- `tcx km read-file <file_url> [--compression-level 0|1|2|3]`
  - 读取 KM 附件内容
  - 图片通常返回 Data URI；SVG/XML 等文本资源返回原始文本

- `tcx km hierarchy-info [--doc-id <doc_id|url>] [--space-id <space_id>]`
  - 查看文档或空间的层级结构
  - `--doc-id` 与 `--space-id` 二选一即可

- `tcx km copy <doc_id> (--parent-doc-id <doc_id|url> | --space-id <space_id>) [--title ...]`
  - 复制文档到新的父目录或空间

- `tcx km move <doc_id> [--new-parent-id <doc_id>] [--new-space-id <space_id>]`
  - 移动文档到新的父目录或空间

- `tcx km restore <doc_id>`
  - 恢复已删除文档

- `tcx km my <view>`
  - 查看个人视图
  - 当前稳定子命令：`history`、`edits`、`favorites`、`quick-access`、`mentioned`、`received`、`comments`

### 兼容保留命令

- `tcx km get-content <doc_id|url>`
  - 旧入口；读取正文并转换为 Markdown
  - 建议新场景优先使用 `tcx km get`

- `tcx km capture-screenshot <url>`
  - 生成学城文档截图并保存到本地配置目录
  - 必须传完整文档 URL，不能只传 `doc_id`

- `tcx km create-doc --title ... (--parent-doc-id ... | --space-id ...) [--markdown-content ...] [--markdown-file ...]`
  - 创建文档或目录
  - `--parent-doc-id` 与 `--space-id` 至少提供一个
  - `--parent-doc-id` 可传纯数字 ID，也可传学城 URL
  - `--markdown-file` 与 `--markdown-content` 可同时传；文件优先

- `tcx km delete-doc <doc_id|url>`
  - 删除文档

- `tcx km history [--operation-type browse|edit|edit-non-deleted|1|2|3] [--page-no 1] [--page-size 30] [--creator <mis>]`
  - 查询最近浏览 / 最近编辑历史

- `tcx km perms <doc_id|url> [--raw-json]`
  - 查询文档权限信息
  - 默认输出归一化结构；加 `--raw-json` 可返回接口原始 JSON
  - 兼容别名：`tcx km permissions <doc_id|url> [--raw-json]`

- `tcx km get-drawio-source <src>`
  - 提取 DrawIO 图片的源码

### 命令行示例

```bash
# 读取文档
tcx km get 2742721788
tcx km get 2742721788 --json

# 搜索文档 / 空间
tcx km search "mcp" --limit 5
tcx km search-space "基础技术部文档" --limit 5

# 读取附件
tcx km read-file "https://km.sankuai.com/api/file/..." --compression-level 3

# 查看层级
tcx km hierarchy-info --doc-id 2742721788

# 复制 / 移动 / 恢复
tcx km copy 2742721788 --parent-doc-id 2742721799 --title "副本"
tcx km move 2742721788 --new-parent-id 2742721799
tcx km restore 2742721788

# 个人视图
tcx km my favorites --page-size 5

# 兼容保留命令
tcx km create-doc \
  --title "接口联调记录" \
  --parent-doc-id 2742721788 \
  --markdown-file ./draft.md
tcx km delete-doc 2742721788
# 最近浏览
tcx km history --operation-type browse --page-size 5

# 查询文档权限（默认归一化输出）
tcx km perms 2742721788

# 查询文档权限（原始 JSON 输出）
tcx km perms 2742721788 --raw-json

# 兼容别名
tcx km permissions https://km.sankuai.com/page/2742721788

# 提取 DrawIO 源码
tcx km get-drawio-source \
  "https://km.sankuai.com/api/file/cdn/123/456?contentType=0"
```

### 命令行边界

- 当前仍**不提供**稳定 CLI：`tcx km edit`、`tcx km discussion`
- 需要在脚本中做批处理或程序内复用时，优先走下面的 Python API

## 路径二：Python API

在已安装 `mt-turing-codex` 的 Python 环境中，公开导入面如下：

```python
from turing_codex.km import KMReadService, KMHierarchyService, KMOperationService
```

### 常用能力

- `KMReadService.get_document(doc_id_or_url, convert_to_md=True)`
  - 读取学城文档，默认返回 Markdown 字符串

- `KMReadService.search_documents(keyword, limit=30, offset=0, space_ids=None)`
  - 搜索学城文档

- `KMReadService.search_spaces(keyword, limit=20, offset=0)`
  - 搜索学城空间

- `KMReadService.read_file_content(url, compression_level=3)`
  - 读取学城附件内容

- `KMReadService.get_operation_history(operation_type="browse", page_no=1, page_size=30, creator=None)`
  - 获取最近浏览 / 最近编辑历史

- `KMReadService.get_document_permissions(doc_id_or_url, raw_json=False)`
  - 查询文档权限信息
  - `raw_json=False` 时返回归一化结构；`raw_json=True` 时返回接口原始 JSON

- `KMHierarchyService.get_doc_or_space_info(km_doc_id=0, space_id=0)`
  - 查看文档或空间的层级结构

- `KMOperationService.create_document(...)`
  - 创建文档或目录

- `KMOperationService.copy_document(...)`
  - 复制文档

- `KMOperationService.move_document(...)`
  - 移动文档

- `KMOperationService.delete_document(doc_id)`
  - 删除文档

- `KMOperationService.restore_document(doc_id)`
  - 恢复文档

### Python 示例

```python
import asyncio

from turing_codex.km import KMReadService, KMHierarchyService, KMOperationService


async def main() -> None:
    read_service = KMReadService()
    markdown = await read_service.get_document(
        "https://km.sankuai.com/collabpage/2742721788"
    )
    print(markdown[:200])

    docs = await read_service.search_documents("mcp", space_ids=[98076])
    for item in docs:
        print(item.title, item.doc_link)

    hierarchy_service = KMHierarchyService()
    snapshot = await hierarchy_service.get_doc_or_space_info(km_doc_id=2742721788)
    for child in snapshot.children:
        print(child.title, child.url)

    operation_service = KMOperationService()
    result = await operation_service.create_document(
        title="接口联调记录",
        parent_doc_id=2742721788,
        content_file="./draft.md",
    )
    print(result.message)


asyncio.run(main())
```

### Python 路径说明

- Python API 同样依赖已有登录态；首次使用前仍建议先执行 `tcx login km`
- `get_document()` 与 `read_file_content()` 返回字符串
- 搜索结果、层级结果、写操作结果返回对象，直接读取对象属性即可
- 如果你只是临时执行一次操作，优先用命令行；如果你要做批量处理或程序集成，再用 Python API

## 常见问题

- 登录态失效：
  - 重新执行 `tcx login km`

- 读取高密级文档失败：
  - 当前读取链路会按 `SECRET_LEVEL_THRESHOLD=5` 拒绝高密级文档；C5/C6 文档不在当前可读取范围内

- 截图失败：
  - 先确认传入的是完整 `km.sankuai.com` 文档 URL，而不是单独的 `doc_id`

- 创建文档失败：
  - 先确认是否提供了 `--parent-doc-id` 或 `--space-id`
  - 如果同时传了 `--markdown-file` 与 `--markdown-content`，会以文件内容为准

- DrawIO 源码提取失败：
  - 先确认输入的是 DrawIO 图片的 `src`，不是普通页面 URL
