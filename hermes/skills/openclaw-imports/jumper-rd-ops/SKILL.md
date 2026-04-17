---
name: jumper-rd-ops
description: 美团研发 Jumper 一体化技能。用于通过 `tcx jumper-cli` 执行远程命令、批量巡检、原生命令透传，以及处理 daemon 卡住、中断失败等排障场景。
---

# Jumper 研发排障 Skill

## 适用场景

- 需要在目标机器上执行标准化排障命令，例如 `hostname`、`uptime`、日志查看、JVM 核查
- 需要执行 `getappkey`、`pssh`、`ssh` 这类 Jumper 原生命令
- 需要在发布后做批量巡检或小范围探测
- 需要处理中断不了、daemon 卡住、命令长时间无响应等 Jumper 常见故障

## 触发规则

- 用户提到“jumper 登录”“跳板机排障”“远程看日志”“批量执行命令”
- 用户提到 `getappkey`、`pssh`、`ssh <host>`、`daemon restart` 等 Jumper 语义
- 用户明确要求通过跳板机到目标机器执行命令

## 边界说明

- 本 skill 聚焦“远程执行 + 巡检 + 故障处理”
- 统一入口使用 `tcx jumper-cli`，不直接把外部工具当作主工作流
- 说明：`tcx` 是 `turing-codex` 的等价简写，以下命令示例统一使用 `tcx`
- 数据库、高危写操作、批量变更类命令不应在本 skill 中默认执行

## 核心前置

- 本机已具备可用的 Jumper 环境
- 建议先执行：`tcx jumper-cli daemon status`
- 若出现认证或连接异常，按公司既有安全流程完成确认后再重试

## 命令总览

- `tcx jumper-cli run --host <host> -- '<command>'`
  - 面向单机标准命令执行，适合日志、进程、JVM、环境检查
- `tcx jumper-cli raw -- '<jumper_command>'`
  - 直接透传 `getappkey`、`pssh`、`ssh` 等 Jumper 原生命令
- `tcx jumper-cli daemon status|restart`
  - 查询或重启 daemon
- `tcx jumper-cli interrupt`
  - 向当前任务发送中断信号

## 选择规则

- 已知目标主机，且只是执行一段标准 shell：优先 `run`
- 需要 `getappkey`、`pssh` 或原生 `ssh` 语义：使用 `raw`
- 遇到批量命令：先缩小范围试跑，再扩大到全量
- 命令卡住或会话异常：先 `interrupt`，仍无效再 `daemon restart`

## 标准工作流

### 1) 单机健康检查

```bash
tcx jumper-cli run --host set-xx-yy -- 'hostname && date && uptime'
```

适用于发布后快速核对机器是否在线、系统时间是否正常、负载是否异常。

### 2) 日志与进程排查

```bash
tcx jumper-cli run --host set-xx-yy --sudo-user sankuai -- 'tail -n 200 /var/sankuai/logs/*/error.log'
tcx jumper-cli run --host set-xx-yy --sudo-user sankuai -- 'ps aux | grep java'
tcx jumper-cli run --host set-xx-yy --sudo-user sankuai -- 'jps -l'
```

### 3) 先小范围再批量巡检

```bash
tcx jumper-cli raw -- 'getappkey -e test com.sankuai.waimai.app'
tcx jumper-cli raw -- 'pssh -r 1-2 -e test com.sankuai.waimai.app "uptime"'
```

确认输出与权限都正常后，再决定是否扩大范围。

### 4) 需要原生命令透传

```bash
tcx jumper-cli raw -- 'ssh app-server-01 "hostname && uptime"'
tcx jumper-cli raw -- 'getappkey -e test com.sankuai.waimai.app'
```

仅在确实需要原生 Jumper 语义时使用；`raw` 更适合一次性非交互命令，不适合进入交互式 ssh shell；常规排障优先 `run`。

### 5) daemon 卡住或任务无法中断

```bash
tcx jumper-cli interrupt
tcx jumper-cli daemon restart
tcx jumper-cli daemon status
```

建议顺序是：先中断，再重启，最后检查状态。

## 常见故障处理

- 命令长时间无响应：
  - 先执行 `tcx jumper-cli interrupt`
  - 再视情况执行 `tcx jumper-cli daemon restart`
- 提示权限不足：
  - 确认是否需要补 `--sudo-user sankuai`
- 批量命令超时：
  - 先缩小 `pssh -r` 范围，再逐步扩大
- 原生命令执行失败：
  - 先在 `raw` 中保留最小命令集，排除引号与转义问题

## 回复规范

- 优先给出可直接执行的 `tcx jumper-cli` 命令
- 批量命令默认建议先小范围验证
- 遇到高风险操作时，先说明风险，再让用户确认具体命令
