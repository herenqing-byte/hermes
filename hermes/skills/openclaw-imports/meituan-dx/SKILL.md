---
name: meituan-dx
description: "面向 `tcx dx ...` 的大象（DX/XM）即时通讯技能，覆盖登录检查、身份查询、联系人/群搜索、发送文本消息、历史查询与会话已读处理。适用于用户提到大象发消息、查会话未读、搜人/搜群、查聊天记录等场景。"
---

# 大象（DX/XM）即时通讯 Skill

## 适用场景

- 给用户、群或公众号发送文本消息
- 搜索用户、群、公众号并确认目标 ID
- 查询聊天记录，或按关键词过滤历史消息
- 查看会话列表、筛选未读、标记单个或全部会话为已读
- 排查 DX 登录态过期、页面运行态异常或会话模块未就绪

## 选择入口

- 默认优先使用命令行：`tcx dx`
- 以下命令示例统一使用 `tcx`

## 前置

- 首次使用或登录态过期时，先执行：`tcx login dx`
- 使用前可先查看帮助：`tcx dx --help`
- 若不确定运行态是否正常，先执行：`tcx dx doctor`

## 当前稳定 CLI

当前稳定 CLI 包括以下命令：

- `tcx dx doctor`
- `tcx dx whoami`
- `tcx dx search "关键词" --type user`
- `tcx dx send "消息内容" --uid <uid>`
- `tcx dx history --gid <gid> --limit 20`
- `tcx dx sessions --unread`
- `tcx dx sessions read <session_id>`
- `tcx dx sessions allread`

## 通用规则

- `send` 与 `history` 的目标参数只支持 `--uid` / `--gid` / `--pid` 三选一；未传时默认对自己
- `search --type` 支持 `user` / `group` / `pub` / `pubgroup`，可重复传入
- `history --keyword` 会走远端关键词搜索，建议与明确目标一起使用
- `sessions --type` 支持 `chat` / `group` / `pub`，可与 `--unread` 组合

## 标准工作流

### 1) 登录与健康检查

```bash
tcx login dx
tcx dx doctor
tcx dx whoami
```

### 2) 搜索目标并发送文本消息

```bash
tcx dx search "张三" --type user --limit 5
tcx dx search "技术支持群" --type group --limit 5
tcx dx send "你好，麻烦帮我看一下这个问题" --uid 2320057
tcx dx send "今晚 19:00 开会，请准时参加" --gid 68150133873
tcx dx send "日报已更新" --pid 137444296144
```

### 3) 查询历史消息

```bash
tcx dx history --gid 68150133873 --limit 20
tcx dx history --uid 2320057 --keyword "异常" --limit 10
tcx dx history --pid 137444296144 --limit 20 --json
```

### 4) 查询会话并处理未读

```bash
tcx dx sessions --limit 30
tcx dx sessions --type group --unread --limit 50
tcx dx sessions read 68313641799
tcx dx sessions allread --limit 200
```

## 当前未作为稳定入口对外提供

以下旧 DX 能力当前未作为稳定入口对外提供：

- 群创建、改名、公告设置、成员管理
- 回复消息、撤回消息
- Markdown / Link 卡片消息
- 实时事件监听与 watch 流程

遇到这些需求时，应明确说明“当前未作为稳定入口对外提供”，不要引导用户回退到旧 `dx`、bun 脚本或其他内部实现。

## 常见问题

- 登录态缺失或过期：
  - 重新执行 `tcx login dx`
- `doctor` 显示会话或消息运行态不可用：
  - 先重新执行 `tcx login dx`
  - 再执行 `tcx dx doctor --json`
- 搜索结果为空：
  - 缩短关键词，或改用更明确的人名 / 群名
  - 显式传入 `--type`
- 会话筛选结果为空：
  - 调大 `--limit`
  - 去掉 `--unread` 或 `--type` 后重试

## 回复规范

- 优先输出可直接执行的 `tcx dx ...` 命令
- 若目标信息不完整，先提示用户补充 `uid` / `gid` / `pid`，或给出可搜索关键词
- 若需求超出当前稳定入口，明确说明“当前未作为稳定入口对外提供”
