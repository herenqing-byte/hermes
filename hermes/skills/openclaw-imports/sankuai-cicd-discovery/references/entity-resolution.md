# 实体与标识关系

## 核心标识

| 标识 | 含义 | 常见来源 | 典型下游命令 |
| --- | --- | --- | --- |
| `keyword` | 用户给出的模糊关键字 | 用户口述、仓库名片段、服务片段 | `tcx list-services --keyword ...` |
| `appkey` | 服务或应用标识 | `list-services`、用户口述 | `tcx cargo list-hosts --appkey ...` |
| `service-name` | 发布系统中的标准服务名，常见为 `com.xxx...` | `list-services`、`plus` 查询结果 | `tcx plus *`、`tcx cargo list-jobs` |
| `stack_uuid` | Cargo 流水线编排唯一标识 | `list-pipelines`、Cargo URL | `tcx cargo stack-info`、`list-hosts`、`list-images` |
| `cargo_url` | Cargo 页面 URL | 用户粘贴链接、`list-pipelines` 结果 | `tcx cargo stack-info`、`list-images` |
| `release-id` | Plus 发布单 ID | `tcx plus base-info` | `tcx plus list-templates`、`tcx cargo list-jobs` |
| `template-id` | Plus 或 Talos 模板 ID | 模板列表查询结果 | `tcx plus template-info`、执行型 skill |
| `template-name` | 模板名 | 用户口述、模板列表 | `tcx plus template-info --template-name ...` |
| `swimlane` | 前端或测试泳道名称 | 用户口述 | `tcx fe-deploy list-templates` |
| `appId` | Talos 前端应用 ID | `tcx fe-deploy list-appids` | `tcx fe-deploy list-templates` |

## 收敛顺序

1. 模糊关键词优先收敛到 `service-name` 或 `appkey`
2. `service-name` 优先收敛到 `release-id`、模板列表、发布记录
3. `stack_uuid` / `cargo_url` 优先收敛到 stack 详情、机器列表、镜像候选
4. `swimlane` 优先收敛到 Talos 模板列表

## 选择规则

- 只有模糊关键词时，不要直接猜 `service-name`，先跑 `list-services`
- 同时有 `service-name` 与 `release-id` 时：
  - 查 Plus 模板优先保留 `service-name`
  - 只在明确需要时才直接使用 `release-id`
- 同时有 `stack_uuid` 与 `cargo_url` 时：
  - 优先保留 `stack_uuid` 作为稳定标识
  - 需要复现用户提供的页面上下文时再保留 `cargo_url`
- Talos 相关优先保留 `swimlane` 与 `template-id`

## 常见误判

- 仓库名不等于 `service-name`
- UI 展示标题不等于 `stack_uuid`
- 模板展示名不等于 `template-id`
- `appkey` 与 `service-name` 常常相关，但不能无依据互推
