---
name: plus-build-deploy
description: 面向 `tcx plus ...` 的 Plus 构建部署技能。适用于测试主干环境 / Stage 的服务查询、模板确认、构建与部署，不覆盖 Cargo 泳道环境或 Prod 发布。
---

# Plus 构建部署 Skill

## 适用场景

- 查询服务名、发布单、模板列表与模板详情
- 在测试主干环境 / Stage 发起 Plus 构建或部署
- 确认模板默认值、代码来源、部署目标等关键参数
- 排查登录态失效、模板参数缺失等常见问题

## 选择入口

- 服务检索使用：`tcx list-services`
- 构建部署使用：`tcx plus`
- 说明：`tcx` 是 `turing-codex` 的等价简写，以下命令示例统一使用 `tcx`
- 若需求是 Cargo 泳道联调，请切换到 `cargo-swimlane-build-deploy`

## 前置

- 首次使用或登录态过期时，先执行：`tcx login code`
- 使用前可先查看帮助：`tcx plus --help`

## 扩展参考

- 需要补充服务定位、模板确认或参数示例时，可按需使用以下资源：
  - `references/cli-cheatsheet.md`：补充服务定位、模板确认与构建部署参数示例
- 使用这些资源后，最终仍应回到稳定入口，优先输出 `tcx list-services ...` 与 `tcx plus ...` 命令

## 路径一：命令行

当前稳定 CLI 包括以下命令：

- `tcx list-services --keyword <keyword>`
- `tcx plus base-info --service-name <service_name>`
- `tcx plus list-templates --service-name <service_name>`
- `tcx plus template-info --service-name <service_name>`
- `tcx plus build --service-name <service_name>`
- `tcx plus deploy --service-name <service_name>`

### 标准工作流

1) 先定位服务

```bash
tcx list-services --keyword turing-codex
```

2) 确认基础信息与模板

```bash
tcx plus base-info --service-name com.sankuai.turing.aibox
tcx plus list-templates --service-name com.sankuai.turing.aibox
tcx plus template-info --service-name com.sankuai.turing.aibox --template-id 1008587
```

3) 发起构建

```bash
tcx plus build \
  --service-name com.sankuai.turing.aibox \
  --template-id 1008587 \
  --branch feature/demo
```

4) 发起部署

```bash
tcx plus deploy \
  --service-name com.sankuai.turing.aibox \
  --template-id 1008587 \
  --branch feature/demo \
  --hosts 10.0.0.1
```

### 参数规则

- `list-templates` 可直接传 `--service-name`；也可在已知发布单时直接传 `--release-id`
- `template-info`、`build`、`deploy` 中，`--template-id` 优先级高于 `--template-name`
- `--branch` 等价于 `--symbol-name branch --symbol-value <branch>`
- `--hosts` 可重复传入，也可逗号分隔
- 不传 `--hosts` 时默认 all；但 prod 语义不属于本 skill
- 模板没有默认值时，需要显式补齐 `--manifest`、`--tags-json`、`--build-option-json`、`--build-json`、`--deploy-json`
- 返回结果里建议优先看 `deployHistoryId`；`buildHistoryId` 为兼容保留字段

## 当前边界

- 本 skill 只覆盖测试主干环境 / Stage 的稳定 Plus CLI
- Prod 发布当前不在本 skill 范围内

## 常见问题

- 登录态失效或 401：
  - 先执行 `tcx login code`
- 服务名不确定：
  - 先执行 `tcx list-services --keyword ...`
- 模板 ID、模板名或发布单不确定：
  - 先执行 `plus base-info`、`plus list-templates`、`plus template-info`
- 模板缺少默认值导致参数校验失败：
  - 先执行 `plus template-info`，再补齐 manifest / tags / build / deploy 相关参数

## 回复规范

- 优先输出可直接执行的 `tcx` 命令
- 对不确定参数，先给“最小必填版本”并说明待补字段
- 一旦发现需求落到 Prod 或 Cargo 泳道，要明确切换 skill
