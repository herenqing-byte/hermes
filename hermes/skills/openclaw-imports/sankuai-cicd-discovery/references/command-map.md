# 命令映射速查

| 用户意图 | 首选命令 | 常用参数 | 产出/作用 | 下一步 |
| --- | --- | --- | --- | --- |
| 根据关键词找服务 | `tcx list-services` | `--keyword` `--type` `--tenant` | 收敛 `service-name`、`appkey`、服务类型 | 进入 `cargo` / `plus` |
| 查看全部服务原始字段 | `tcx list-services` | `--raw-json` | 便于 agent 抽字段 | 整理标准标识 |
| 查 test 流水线列表 | `tcx cargo list-pipelines` | `--env test` `--page-size` `--max-items` | 找 `stack_uuid`、`cargo_url`、泳道候选 | 进入 `stack-info` |
| 查 stack 编排详情 | `tcx cargo stack-info` | `--stack-uuid` 或 `--cargo-url` `--view summary` | 查看机器、项目、镜像、构建任务 | 再查 hosts/images |
| 查机器列表或失败机器 | `tcx cargo list-hosts` | `--stack-uuid` `--status` `--service-name` `--appkey` | 看服务落到哪些主机、哪些失败 | 定位故障或做发布前核对 |
| 查构建/部署历史 | `tcx cargo list-jobs` | `--service-name` 或 `--release-id` `--job-type` | 查看最近 build/deploy 记录 | 判断最近动作与结果 |
| 查 deploy 候选镜像 | `tcx cargo list-images` | `--stack-uuid` 或 `--cargo-url` | 查看 `runner_uuid` / `image_uuid` 候选 | 交给发布 skill |
| 查 Plus 基础信息 | `tcx plus base-info` | `--service-name` | 解析发布单基础信息与 `release-id` | 查模板 |
| 查 Plus 模板列表 | `tcx plus list-templates` | `--service-name` 或 `--release-id` | 获取模板候选 | 进入 `template-info` |
| 查 Plus 模板详情 | `tcx plus template-info` | `--service-name` `--template-id` 或 `--template-name` | 查看模板详细配置 | 交给发布 skill |
| 查前端 appId | `tcx fe-deploy list-appids` | 无 | 获取 Talos 可用 appId | 查模板 |
| 查前端模板列表 | `tcx fe-deploy list-templates` | `--swimlane` `--app-id` `--target` | 获取 Talos 模板候选 | 交给发布 skill |
| 确认当前 misId | `tcx whoami` | 无 | 确认当前账号身份 | 作为辅助信息 |
| 刷新登录态 | `tcx login` | 目标名（如 `code` / `talos` / `km` / `ones` / `mws` / `all`） | 修复认证问题 | 回到查询命令 |

## 默认参数建议

- `tcx list-services`：默认不加 `--raw-json`
- `tcx cargo stack-info`：默认 `--view summary`
- `tcx cargo list-pipelines`：优先 `--page-size 20 --max-items 100`
- `tcx cargo list-jobs`：优先 `--job-type all`
- `tcx plus list-templates`：优先传 `--service-name`
- `tcx fe-deploy list-templates`：优先 `--target newtest`

## 交接规则

- 需要 `build`、`build-deploy`、`deploy`、`release` 时，转交执行型 skill。
- 本 skill 可以把查询出的 `service-name`、`stack_uuid`、`release-id`、`template-id` 作为交接上下文。
