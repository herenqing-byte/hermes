---
name: talos-fe-deploy
description: "面向 `tcx fe-deploy ...` 的 Talos 前端部署技能。适用于用户要求部署前端、前端发布、Talos 部署等场景，支持美团前端项目在 Talos 平台的模板查询、构建与发布。默认仓库为图灵前端 banma_fe_turing，其他项目需手动指定 --repo。"
---

# Talos 前端部署 Skill

## 适用场景

- 查询前端 appId 和可用模板列表
- 在 Talos 平台发起前端构建与部署
- 查询部署状态和流水线进度
- 支持测试泳道、预发、线上三种环境发布

## 环境说明

| 环境 | target | 泳道 | 说明 |
|------|--------|------|------|
| 测试泳道 | `newtest` | **必填** | 日常开发联调 |
| 预发环境 | `staging` | 不需要 | 备机环境，上线前验证 |
| 线上环境 | `production` | 不需要 | 生产环境，正式发布 |

**⚠️ 线上部署需谨慎，建议先在预发环境验证通过后再发布。**

## 默认配置

图灵前端项目默认配置：

| 配置项 | 值 |
|--------|-----|
| 默认仓库 | `ssh://git@git.sankuai.com/bm/banma_fe_turing.git` |
| 默认 target | `newtest`（测试泳道） |

## 前置

- 首次使用或登录态过期时，先执行：`tcx login talos`
- 使用前可先查看帮助：`tcx fe-deploy --help`

## 标准工作流

### 1. 查询模板列表

**测试泳道（需要泳道）：**
```bash
tcx fe-deploy list-templates --swimlane <泳道名> --target newtest
```

**预发环境（不需要泳道）：**
```bash
tcx fe-deploy list-templates --target staging
```

**线上环境（不需要泳道）：**
```bash
tcx fe-deploy list-templates --target production
```

### 2. 发起部署

**测试泳道部署（需要泳道）：**
```bash
tcx fe-deploy deploy \
  --swimlane <泳道名> \
  --branch <分支名> \
  --template-id <测试环境模板ID> \
  --target newtest \
  --wait
```

**预发环境部署（不需要泳道）：**
```bash
tcx fe-deploy deploy \
  --branch <分支名> \
  --template-id <预发模板ID> \
  --target staging \
  --wait
```

**线上环境部署（不需要泳道）：**
```bash
tcx fe-deploy deploy \
  --branch <分支名> \
  --template-id <线上模板ID> \
  --target production \
  --wait
```

### 3. 查询部署状态

```bash
tcx fe-deploy status --flow-id <flowId>
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--swimlane` | 泳道名称（测试泳道必填，预发/线上不需要） | - |
| `--branch` | Git 分支名（必填） | - |
| `--repo` | 仓库地址 | 图灵前端仓库 |
| `--template-id` | 模板 ID（必填） | - |
| `--target` | 发布目标环境 | `newtest` |
| `--wait` | 持续跟踪部署状态 | - |

## 图灵前端常用模板

### 测试泳道 (newtest)

| 模板名 | templateId |
|--------|------------|
| 【泳道】AIGC | 534280 |
| 【泳道】index-机器学习平台 | 534070 |

### 预发环境 (staging)

| 模板名 | templateId |
|--------|------------|
| 法兰克福 | 530692 |
| 国内-model-AIGC | 538228 |
| 国内-index-机器学习平台 | 542718 |

### 线上环境 (production)

| 模板名 | templateId |
|--------|------------|
| 法兰克福-AIGC | 530691 |
| 国内-model-AIGC | 538229 |
| 国内-index-机器学习平台 | 542720 |

## 常见问题

- **登录态失效**：执行 `tcx login talos`
- **找不到模板**：确认 target 是否正确，不同环境模板不同
- **部署失败**：使用 `status --flow-id` 查看详细状态

## 回复规范

- 用户说"部署前端"或"测试环境部署" → 默认 `--target newtest`，需要泳道
- 用户说"预发部署"、"备机部署"、"staging" → `--target staging`，不需要泳道
- 用户说"线上部署"、"生产环境"、"production" → `--target production`，不需要泳道，并提示谨慎操作
- 用户未指定仓库时，自动使用默认仓库
- 部署成功后提供 flowId 和 Jenkins 日志链接