# DevTools PR 协作速查

## 登录

```bash
tcx login code
```

## 正式 PR

```bash
tcx pr create \
  --title 'feat: demo' \
  --description '变更说明' \
  --source-branch feature/demo \
  --target-branch master \
  --reviewer zhangsan
```

## 草稿 PR / 预检

```bash
tcx pr create \
  --title 'draft: test' \
  --description-file ./pr.md \
  --source-branch feature/demo \
  --target-branch master \
  --type draft \
  --dry-run
```

## 参数提醒

- 正式 PR：`--type=normal` 时必须传 `--reviewer`
- 描述：`--description` 与 `--description-file` 至少提供一个
- 跨仓库：显式补 `--project-key` 与 `--repo-slug`
- 当前稳定 CLI 能力是 `tcx pr create`；评论、approve 待后续入口稳定后纳入
