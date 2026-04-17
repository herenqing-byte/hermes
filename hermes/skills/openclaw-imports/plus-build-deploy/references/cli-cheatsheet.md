# Plus 构建部署速查

## 登录

```bash
tcx login code
```

## 服务定位

```bash
tcx list-services --keyword turing-codex
tcx list-services --keyword aibox --raw-json
```

## 基础信息与模板

```bash
tcx plus base-info --service-name com.sankuai.turing.aibox
tcx plus list-templates --service-name com.sankuai.turing.aibox
tcx plus list-templates --release-id 186473
tcx plus template-info --service-name com.sankuai.turing.aibox --template-id 1008587
```

## 构建

```bash
tcx plus build \
  --service-name com.sankuai.turing.aibox \
  --template-id 1008587 \
  --branch feature/demo
```

## 部署

```bash
tcx plus deploy \
  --service-name com.sankuai.turing.aibox \
  --template-id 1008587 \
  --branch feature/demo \
  --hosts 10.0.0.1
```

## 参数提醒

- `--template-id` 优先于 `--template-name`
- `--branch` 等价于 `--symbol-name branch --symbol-value <branch>`
- 模板无默认值时，补 `--manifest`、`--tags-json`、`--build-option-json`、`--build-json`、`--deploy-json`
- 本 skill 当前只面向测试主干环境 / Stage 环境，不覆盖 Prod
- `plus deploy` 返回中优先看 `deployHistoryId`，`buildHistoryId` 为兼容字段
