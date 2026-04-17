---
name: sankuai-octo-thrift
description: 面向 Octo 的 Thrift 排障技能，覆盖节点发现、接口签名查询与方法调用（nodes -> interfaces -> invoke）标准流程，适用于快速定位服务节点、确认签名并在 test 环境验证调用。
---

# Octo Thrift 排障 Skill

## 适用场景

- 查询某个 appkey 的在线节点（IP/端口/泳道）
- 从目标节点读取 Thrift 接口与方法签名
- 按签名调用服务方法进行联调验证
- 快速定位参数格式、签名不匹配与鉴权问题

## 核心前置

- 说明：`tcx` 是 `turing-codex` 的等价简写，以下命令示例统一使用 `tcx`
- 首次使用先登录：`tcx login mws`（`octo` 为别名）
- 默认优先在测试环境执行：`--env test`
- 调用前先做签名探查：`nodes -> interfaces -> invoke`

## 命令总览

- `tcx octo nodes APPKEY [--env test|prod] [--json]`
- `tcx octo interfaces APPKEY IP PORT [--env test|prod] [--json]`
- `tcx octo invoke APPKEY SERVICE METHOD IP PORT [--params JSON_ARRAY] [--host] [--cell] [--swimlane] [--env test|prod]`

## 输入规范

- `APPKEY`：服务 appkey（如 `com.sankuai.demo.service`）
- `METHOD`：方法完整签名（推荐从 `interfaces` 输出复制）
- 仅写方法名（如 `getDefaultVersion`）会报 `methodSign=... is invalid`
- `--params`：必须是 JSON 数组，默认 `[]`
- `--host`：不传时默认 `host-<ip>`
- `--env`：默认 `test`，生产调用前必须再次确认参数

## 标准流程

1) 查节点

```bash
tcx octo nodes com.sankuai.demo --env test --json
```

2) 查接口签名

```bash
tcx octo interfaces com.sankuai.demo 127.0.0.1 8080 --env test
```

3) 调接口

```bash
tcx octo invoke \
  com.sankuai.demo \
  com.sankuai.demo.thrift.DemoService \
  'ping(java.lang.String):java.lang.String' \
  127.0.0.1 8080 \
  --params '["hello"]' \
  --env test
```

## 常见错误与处理

- 鉴权失败/提示未登录：执行 `tcx login mws` 后重试
- `--params` 解析失败：检查是否是合法 JSON 数组
- 方法签名不匹配：先重新执行 `interfaces`，以目标节点返回签名为准
  - 示例：`getDefaultVersion(java.lang.String,java.lang.String):Map`
- 生产调用风险：先在 `test` 验证，再切换 `--env prod`

## 回复规范

- 节点查询：优先返回节点数量与关键字段（host/ip/port/cell/swimlane）
- 接口查询：按 service 分组输出签名
- 调用结果：返回 JSON 结构，不省略错误字段
