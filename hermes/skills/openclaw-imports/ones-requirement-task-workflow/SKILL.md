---
name: ones-requirement-task-workflow
description: 面向 `tcx ones ...` 的 Ones 需求 / 任务管理技能，覆盖登录态准备、待办查询、分支绑定、新建 / 编辑 / 删除需求与任务、读取详情与列出关注空间的常见流程。
---

# Ones 需求与任务工作流 Skill

## 适用场景

- 查询我的待办任务
- 绑定分支到 Ones 任务
- 新建需求 / 任务、编辑描述、读取详情
- 删除需求 / 任务
- 列出我关注的空间并筛选
- 排查登录态、鉴权失败或配置缺失

## 选择入口

- 默认优先使用命令行：`tcx ones`
- 说明：`tcx` 是 `turing-codex` 的等价简写，以下命令示例统一使用 `tcx`

## 前置

- 首次使用或登录态过期时，先执行：`tcx login ones`
- 如需隔离登录态或测试账号，可先设置环境变量：`TCX_APP_SLUG=<slug>`
- 使用前可先查看帮助：`tcx ones --help`

## 扩展参考

- 需要补充默认值、返回结构或程序化调用细节时，可按需使用以下资源：
  - `references/cli.md`：补充命令默认值、返回结构与调用关系
  - `references/api.md`：补充请求示例与程序化调用细节
- 若任务需要写 Python 脚本，可优先基于公开包 `turing_codex.ones` 组织代码；使用这些资源后，最终仍应回到稳定 CLI 或公开 Python API

## 路径一：命令行

当前稳定 CLI 包括以下命令：

- `tcx ones list`
- `tcx ones bind`
- `tcx ones create-requirement`
- `tcx ones create-task`
- `tcx ones edit-task`
- `tcx ones get-task`
- `tcx ones edit-requirement`
- `tcx ones get-requirement`
- `tcx ones delete-task`
- `tcx ones delete-requirement`
- `tcx ones list-spaces`

### 通用规则

- `--project-id` 未显式传入时，会优先读取 `ones.project_id` 默认值
- `--assigned` / `--mis-id` 默认尝试从 `tcx whoami` 解析
- `--desc` 支持 HTML 片段，例如 `<p>描述</p>`
- `bind` 未传 `--app-key` 时会尝试自动识别；若自动识别失败，请显式传入

### 标准工作流

1) 登录并确认空间

```bash
tcx login ones
tcx ones list-spaces --name "你的空间名" --debug
```

2) 新建需求

```bash
tcx ones create-requirement \
  --name "需求标题" \
  --desc "<p>需求描述</p>" \
  --project-id 15823
```

3) 新建任务

```bash
tcx ones create-task \
  --issue-id 93466302 \
  --name "任务标题" \
  --desc "<p>任务描述</p>" \
  --project-id 15823
```

4) 编辑 / 获取详情 / 删除

```bash
tcx ones edit-task --issue-id 93346645 --desc "<p>更新说明</p>"
tcx ones get-task --issue-id 93346645

tcx ones edit-requirement --issue-id 93466302 --project-id 15823 --desc "<p>更新说明</p>"
tcx ones get-requirement --issue-id 93466302

tcx ones delete-task --issue-id 93344214
tcx ones delete-requirement --issue-id 93343759
```

5) 绑定分支到任务

```bash
tcx ones bind \
  --branch "feature/15823-93271855/short-name" \
  --ones-id 93271855 \
  --mis-id "your.misid" \
  --app-key "your_appkey"
```

### 默认行为

- `create-task` 的时间字段若未传入，会自动补默认时间
- `create-requirement` 默认 `subtype_id=55826`

## 常见问题

- 登录态缺失或过期：
  - 重新执行 `tcx login ones`
- 未配置空间 ID：
  - 显式传 `--project-id`，或在 turing-codex 配置中设置 `ones.project_id`
- `--assigned` / `--mis-id` 无法解析：
  - 先设置 `git user.email` / `git user.name`，或直接传参
- `bind` 报 appkey 相关错误：
  - 改用 `--app-key` 明确传入

## 回复规范

- 优先输出可直接执行的 `tcx ones ...` 命令
- 对不确定字段，先给最小可执行版本，再说明待补参数
- 若用户需求超出当前稳定 CLI，明确说明“当前未作为稳定入口对外提供”
