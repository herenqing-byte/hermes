# Cargo 泳道 CLI 速查

## 发现与选择

```bash
# 列出可用泳道（当前仅支持 test）
tcx cargo list-pipelines --env test --page-size 20 --max-items 200

# 查询 stack 详情（summary/full/raw）
tcx cargo stack-info --stack-uuid <stack_uuid> --view summary

# 查询部署候选（runner + image）
tcx cargo list-images --stack-uuid <stack_uuid>

# 查询机器状态
tcx cargo list-hosts --stack-uuid <stack_uuid> --service-name <service_name>
```

## 构建与部署

```bash
# 构建
tcx cargo build \
  --cargo-url '<build_url>' \
  --branch <service_name>=<branch> \
  --wait

# 构建并部署
tcx cargo build-deploy \
  --cargo-url '<build_url>' \
  --branch <service_name>=<branch> \
  --wait

# 独立部署
tcx cargo deploy \
  --stack-uuid <stack_uuid> \
  --runner-image <runner_uuid>=<image_uuid> \
  --wait
```

## 结果核对

```bash
# 查询发布任务列表
tcx cargo list-jobs --service-name <service_name> --job-type all

# 只看部署记录
tcx cargo list-jobs --service-name <service_name> --job-type deploy
```

## 关键约束

- `cargo build` / `build-deploy`：必须至少一个 `--branch 服务名=分支`
- `cargo deploy`：必须至少一个 `--runner-image runner_uuid=image_uuid`
- `--title` 可省略：优先从 URL 解析，再反查 stack 名，最后读配置 `cargo.title`
- `--stack-uuid` 与 `--cargo-url` 二选一，但至少提供一个可解析 stack_uuid 的输入
- 登录失败先执行：`tcx login code`
