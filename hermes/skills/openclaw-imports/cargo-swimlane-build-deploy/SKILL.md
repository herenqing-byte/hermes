---
name: cargo-swimlane-build-deploy
description: 面向 `tcx cargo ...` 的 Cargo 泳道环境构建部署技能。适用于开发联调场景下的泳道查询、构建、部署与结果核对，不覆盖 Plus 测试主干环境或 Prod 发布。
---

# Cargo 泳道构建部署 Skill

## 适用场景

- 查询当前账号可操作的 Cargo 泳道
- 查看泳道基础信息、候选镜像、机器状态与构建 / 部署记录
- 发起 `build`、`build-deploy`、`deploy`
- 处理 `stack_uuid`、`cargo_url`、`runner-image` 等常见参数问题

## 选择入口

- 默认优先使用命令行：`tcx cargo`
- 说明：`tcx` 是 `turing-codex` 的等价简写，以下命令示例统一使用 `tcx`
- 若需求是 Plus 测试主干 / Stage，请切换到 `plus-build-deploy`

## 前置

- 首次使用或登录态过期时，先执行：`tcx login code`
- 使用前可先查看帮助：`tcx cargo --help`

## 扩展参考

- 需要补充参数细节、命令组合或批量生成辅助时，可按需使用以下资源：
  - `references/cli-cheatsheet.md`：补充命令组合与参数示例
  - `scripts/render_runner_flags.py`：当用户已经提供 `list-images` 输出，且需要批量生成 `--runner-image` 参数时，可内部复用该脚本减少手工拼接错误
- 使用这些资源后，最终仍应回到稳定入口，输出整理好的 `tcx cargo ...` 命令

## 路径一：命令行

当前稳定 CLI 包括以下命令：

- `tcx cargo list-pipelines`
- `tcx cargo list-cargos`
- `tcx cargo stack-info`
- `tcx cargo list-hosts`
- `tcx cargo list-jobs`
- `tcx cargo list-images`
- `tcx cargo build`
- `tcx cargo build-deploy`
- `tcx cargo deploy`

### 标准工作流

1) 查询可操作泳道

```bash
tcx cargo list-pipelines --env test --page-size 20 --max-items 200
```

2) 查看泳道基础信息

```bash
tcx cargo stack-info \
  --cargo-url 'https://dev.sankuai.com/cargo/stack/detail/<stack_uuid>/build?title=<title>&tag=all'
```

3) 发起构建或构建并部署

```bash
tcx cargo build \
  --cargo-url 'https://dev.sankuai.com/cargo/stack/detail/<stack_uuid>/build?title=<title>&tag=all' \
  --branch com.demo.service=feature/demo \
  --wait
```

```bash
tcx cargo build-deploy \
  --cargo-url 'https://dev.sankuai.com/cargo/stack/detail/<stack_uuid>/build?title=<title>&tag=all' \
  --branch com.demo.service=feature/demo \
  --wait
```

4) 先查镜像候选，再执行独立部署

```bash
tcx cargo list-images --stack-uuid '<stack_uuid>'
```

```bash
tcx cargo deploy \
  --stack-uuid '<stack_uuid>' \
  --runner-image '<runner_uuid>=<image_uuid>' \
  --wait
```

5) 核对结果与机器状态

```bash
tcx cargo list-jobs --service-name com.demo.service --job-type deploy
tcx cargo list-hosts --stack-uuid '<stack_uuid>' --service-name com.demo.service
```

### 参数规则

- `--stack-uuid` 传了就直接使用；未传时可尝试从标准 `--cargo-url` 中解析
- `--cargo-url` 通常使用 `https://dev.sankuai.com/cargo/stack/detail/<stack_uuid>/build?...` 或 `/host?...` 形式
- `build` / `build-deploy` 至少需要一个 `--branch 服务名=分支`
- `deploy` 至少需要一个 `--runner-image runner_uuid=image_uuid`
- 若用户已提供 `list-images` 输出且需要批量生成多个 `--runner-image` 参数，可在内部按需使用 `scripts/render_runner_flags.py`；但最终回复仍应给出整理好的 `tcx cargo deploy ...` 命令

## 常见问题

- 登录失败或 401：
  - 重新执行 `tcx login code`
- 报 `缺少 stack_uuid`：
  - 补 `--stack-uuid`，或传可解析的 `--cargo-url`
- 不确定该用 `build` 还是 `build-deploy`：
  - 只需要构建产物时用 `build`
  - 需要构建后自动部署时用 `build-deploy`
- 不确定 `runner_uuid=image_uuid` 映射：
  - 先执行 `tcx cargo list-images --stack-uuid '<stack_uuid>'`

## 回复规范

- 优先输出可直接执行的 `tcx cargo ...` 命令
- 若用户只说“测试环境部署”，先确认他要的是 Cargo 泳道联调还是 Plus 测试主干 / Stage
- 需求超出当前稳定 CLI 时，明确说明“当前未作为稳定入口对外提供”
