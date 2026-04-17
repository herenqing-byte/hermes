# Ones API 封装导航

用于需要直接调用 Python 函数或理解接口细节的场景。

## 入口与基础常量

- 入口文件：`src/turing_codex/ones/api.py`
- 基础域名：
  - `ONES_BASE_URL = https://ones.sankuai.com`
  - `FSD_BASE_URL = https://fsdopen.sankuai.com`
- access-token Header：从 Cookie 的 `ssoid` 或 `meituan.ee.ones.fe_ssoid` 构造

## 函数与端点

- `fetch_todo_tasks` → `GET /api/proxy/layout/card`
- `bind_branch_to_task` → `GET /api/qa/v1/branch/baseBranch/branchBindOnes`
- `create_requirement` → `POST /api/qa/v1/onesDetail/createRequirement`
- `edit_requirement` → `POST /api/qa/v1/onesDetail/updateReqInfo`
- `fetch_requirement_detail` → `GET /api/qa/v1/onesDetail/queryReqDetail`
- `create_task` → `POST /api/qa/v1/reqSchedule/addOrUpdateOrgScheduleV2`
- `edit_task` → `POST /api/qa/v1/ones/editOnesBaseProperties`
- `fetch_task_detail` → `GET /api/proxy/daojia/issue/{issueId}`
- `delete_issue` → `GET /api/qa/v1/ones/deleteOnes`
- `fetch_followed_spaces` → `GET /api/proxy/project/category/search/detail`

## 错误与鉴权处理

- `_request_json` 统一处理 HTTP 错误、鉴权失败与响应格式异常
- 鉴权失败会抛 `OnesAuthError` 并提示执行 `tcx login ones`

## Python 直连示例

```python
import asyncio

from turing_codex.ones import export_ones_cookies
from turing_codex.ones.api import create_task

cookies = asyncio.run(export_ones_cookies())
result = create_task(
    cookies,
    issue_id="93466302",
    project_id=15823,
    name="任务标题",
    desc="<p>任务描述</p>",
    assigned="yinfeifan",
)
print(result)
```

## 相关登录逻辑

- Cookie 导出：`src/turing_codex/ones/auth.py` 的 `export_ones_cookies`
- 登录入口：`tcx login ones`
