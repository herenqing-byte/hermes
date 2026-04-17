---
name: devtools-pr-workflow
description: 面向 `tcx pr ...` 的 DevTools Pull Request 协作技能。当前稳定覆盖 `tcx pr create`，适用于准备 reviewer、分支、描述、草稿 PR 与 `--dry-run` 预检。
---

# DevTools PR 协作 Skill

## 适用场景

- 用户要创建 DevTools Pull Request
- 用户要创建草稿 PR，或先做 `--dry-run` 预检
- 用户不确定 reviewer、源分支、目标分支、描述文件等参数如何组织
- 用户执行 `pr` 相关命令时遇到登录态失效或 401

## 选择入口

- 默认优先使用命令行：`tcx pr`
- 说明：`tcx` 是 `turing-codex` 的等价简写，以下命令示例统一使用 `tcx`

## 前置

- 首次使用或登录态过期时，先执行：`tcx login code`
- 使用前可先查看帮助：`tcx pr --help`
- 若需求是“先确认请求体”，优先加 `--dry-run`

## 扩展参考

- 需要补充参数提醒或命令样例时，可按需使用以下资源：
  - `references/cli-cheatsheet.md`：补充命令样例与参数提醒
- 使用这些资源后，最终仍应回到稳定入口，优先输出 `tcx pr create ...` 命令

## 路径一：命令行

当前稳定 CLI 只有一个子命令：

- `tcx pr create`
  - 创建正式 PR 或草稿 PR

### 常用规则

- `--description` 与 `--description-file` 至少提供一个
- `--type normal` 时至少提供一个 `--reviewer`
- `--type draft` 可不传 reviewer
- `--source-branch` 与 `--target-branch` 同时支持短分支名与 `refs/heads/...`

### 命令行示例

```bash
# 创建正式 PR
tcx pr create \
  --title 'feat: demo' \
  --description '变更说明' \
  --source-branch feature/demo \
  --target-branch master \
  --reviewer zhangsan
```

```bash
# 先做 dry-run
tcx pr create \
  --title 'draft: test' \
  --description-file ./pr.md \
  --source-branch feature/demo \
  --target-branch master \
  --type draft \
  --dry-run
```

## 当前边界

- 当前稳定 CLI 只覆盖 `tcx pr create`
- 评论、审批等 PR 协作能力当前未作为稳定入口对外提供

## 常见问题

- 登录态失效或 401：
  - 先执行 `tcx login code`
- `--type normal` 但未传 reviewer：
  - 补充至少一个 `--reviewer`
- 描述为空：
  - 传 `--description` 或 `--description-file`
- 仓库或项目不是默认值：
  - 显式补 `--project-key`、`--repo-slug`

## 回复规范

- 优先输出可直接执行的 `tcx pr create ...` 命令
- 如参数不全，先给 `--dry-run` 版本，再列出待补字段
- 若用户需求超出当前稳定 CLI，明确说明“当前未作为稳定入口对外提供”
