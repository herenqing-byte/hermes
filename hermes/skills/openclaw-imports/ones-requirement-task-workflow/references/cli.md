# Ones CLI 源码导航

用于需要扩展命令行能力、理解默认参数与输出结构的场景。

## 入口与结构

- 入口文件：`src/turing_codex/cli/ones.py`
- 入口注册：`app = typer.Typer(...)` + `cli_entry(...)`
- 统一错误输出：`_render_error`（支持 `--debug` 透出响应细节）

## 子命令与调用关系

- `list` → `export_ones_cookies` → `fetch_todo_tasks`
- `bind` → `_read_job_name`/`_resolve_mis_id` → `bind_branch_to_task`
- `create-requirement` → `_resolve_project_id`/`_resolve_assigned` → `create_requirement`
- `create-task` → `_resolve_project_id`/`_resolve_assigned`/`_default_task_windows` → `create_task`
- `edit-task` → `edit_task`
- `get-task` → `fetch_task_detail`
- `edit-requirement` → `edit_requirement`
- `get-requirement` → `fetch_requirement_detail`
- `delete-task`/`delete-requirement` → `delete_issue`
- `list-spaces` → `fetch_followed_spaces`

## 常用辅助函数

- `_resolve_project_id`：未传 `--project-id` 时读取 `[ones].project_id`
- `_resolve_assigned`/`_resolve_mis_id`：默认从 `tcx whoami` 解析 git user 信息
- `_read_job_name`：从 `app.properties` 读取 `jobName`（用于 `bind`）
- `_default_task_windows`：未传时间字段时生成默认时间窗
- `_extract_first_value`：从 API 响应中抽取 ID

## 登录态与 Cookie

- CLI 在每个子命令中通过 `export_ones_cookies` 导出 Cookie
- 登录与 Cookie 导出逻辑在 `src/turing_codex/ones/auth.py`

## 阅读顺序建议

1) 先看 `src/turing_codex/cli/ones.py` 的子命令入口
2) 再看对应的 API 封装（见 `references/api.md`）
3) 需要自定义脚本时，可直接复用这些函数并自定义流程
