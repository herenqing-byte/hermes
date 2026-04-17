---
name: sankuai-cicd-discovery
description: 使用 tcx 只读查询美团研发 CI/CD 元数据与发布上下文，包括 DevTools 服务检索、Cargo 流水线与机器/构建部署记录查询、Plus 发布单与模板信息查询、Talos 前端模板信息查询。用于用户询问 代码仓库地址、service-name、appkey、stack_uuid、cargo_url、release-id、template-id、swimlane、appId 等标识，或需要在构建/部署前做信息发现、参数补全、上下文定位时。若用户要求实际 build/deploy/release，转交执行型 skill（如 pipeline-build-deploy），不要在本 skill 中直接执行发布动作。
---

# TCX CI/CD Discovery

## 概览

- 专注只读查询，不执行 build、deploy、release。
- 优先把模糊线索收敛成标准标识，再进入后续查询链路。
- 默认使用 `tcx cargo`，不要主动回退到旧别名 `tcx pipeline`。
- 默认输出精简结果；只有在需要二次解析字段时才使用 `--raw-json` 或 raw 视图。

## 核心原则

1. 先确认用户要查什么实体，再选命令，不要一上来盲查全量。
2. 已知 `keyword` 或 `appkey` 时，优先执行 `tcx list-services`。
3. 已知 `stack_uuid` 或 `cargo_url` 时，优先执行 `tcx cargo stack-info`。
4. 已知 `service-name` 时，优先进入 `plus` 或 `cargo list-jobs` 链路。
5. 已知 `swimlane` 时，优先进入 `tcx fe-deploy list-templates` 链路。
6. 用户要构建、部署、发布时，停止在查询阶段并切换到执行型 skill。

## 前置检查

- 查询 Cargo、DevTools、Plus 信息前，先确认是否需要 `tcx login code`。
- 查询 Talos 前端信息前，先确认是否需要 `tcx login talos`。
- 用户提到“我是谁”“当前账号是谁”时，优先用 `tcx whoami` 辅助确认 misId；`tcx me` 仅作为兼容别名。

## 标准工作流

### 1. 收敛输入线索

先识别用户已提供的标识：

- 模糊关键词：服务名片段、仓库名片段、`appkey` 片段
- 服务标识：`service-name`、`appkey`
- 流水线标识：`stack_uuid`、`cargo_url`
- 代码仓库：`repo`，注意：list-services 中返回的 repo 列进行了可能前缀省略，请务必加上`ssh://git@git.sankuai.com`前缀
- 发布标识：`release-id`、`template-id`、`template-name`
- 前端标识：`swimlane`、`appId`

不确定用户给出的名称是不是标准标识时，先执行服务发现，不要直接猜。

### 2. 选择最短查询入口

- 查服务归属、服务名、`appkey`、代码仓库、类型、租户：执行 `tcx list-services`
- 查 test 流水线列表：执行 `tcx cargo list-pipelines`
- 查某个 stack 的机器、项目、镜像、构建任务：执行 `tcx cargo stack-info`
- 查机器状态、失败机器、主机归属：执行 `tcx cargo list-hosts`
- 查最近构建/部署记录：执行 `tcx cargo list-jobs`
- 查 deploy 候选镜像与 runner：执行 `tcx cargo list-images`
- 查 Plus 发布单、模板、模板详情：执行 `tcx plus base-info`、`tcx plus list-templates`、`tcx plus template-info`
- 查 Talos 前端模板：执行 `tcx fe-deploy list-appids`、`tcx fe-deploy list-templates`

### 3. 逐步补全关键标识

遵循以下补全顺序：

1. `keyword/appkey` → `service-name`
2. `service-name` → `release-id` / Plus 模板信息 / 发布记录
3. `stack_uuid/cargo_url` → 机器、镜像、构建任务、宿主信息
4. `swimlane` → Talos 模板列表

如果当前命令返回的信息足以回答问题，就停止，不要继续扩查。

### 4. 输出结构化结论

每次查询后都优先整理成短结论，尽量显式给出：

- 已确认的标准标识：`service-name`、`appkey`、`stack_uuid`、`release-id`、`template-id`
- 当前查询依据：关键词、服务名、泳道名、模板名
- 查询结果摘要：找到什么、缺什么、下一步最适合查什么

## 决策规则

- 用户只提供模糊关键词：先执行 `tcx list-services --keyword ...`
- 用户要“找 test 流水线/泳道”：先执行 `tcx cargo list-pipelines`
- 用户要“看某泳道/stack 编排详情”：先执行 `tcx cargo stack-info`
- 用户要“看失败机器/某服务在哪些机器”：先执行 `tcx cargo list-hosts`
- 用户要“看最近构建或部署历史”：先执行 `tcx cargo list-jobs`
- 用户要“查 Plus 模板”：先执行 `tcx plus base-info` 或 `tcx plus list-templates --service-name ...`
- 用户要“查前端 Talos 模板”：先执行 `tcx fe-deploy list-templates --swimlane ...`
- 用户要“帮我发版/部署/构建”：切换到执行型 skill，不在此 skill 内执行

## 输出约定

- 除非用户明确要原始数据，否则优先解释性摘要，不直接倾倒整段 JSON。
- 只有需要 agent 自行抽字段时，才使用：
  - `tcx list-services --raw-json`
  - `tcx cargo stack-info --view raw`
- 分页命令优先收敛范围，避免一次拉取过多上下文：
  - `tcx cargo list-pipelines --page-size 20 --max-items 100`
  - `tcx cargo list-jobs --page-size 40 --max-items 100`

## 常见陷阱

- 不要把仓库名、展示名、下划线风格名称当成 `service-name`。
- 不要在只知道关键词时直接猜 `stack_uuid` 或 `release-id`。
- 不要把本 skill 用成发布 skill；它的职责是发现与定位，不是执行。
- 不要默认使用旧别名 `tcx pipeline`，除非用户明确要求兼容旧命令。

## 参考资料

- 命令与意图映射：`references/command-map.md`
- 实体与标识关系：`references/entity-resolution.md`
- 典型问法与执行路径：`references/examples.md`
