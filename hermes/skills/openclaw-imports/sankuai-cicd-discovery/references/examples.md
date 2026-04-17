# 典型问法与执行路径

## 场景 1：只知道一个模糊服务名

用户可能会说：

- “帮我查一下 turing aibox 对应的服务信息”
- “这个 appkey 是啥来着，名字里好像有 turing”

推荐路径：

1. 执行 `tcx list-services --keyword turing`
2. 如结果过多，再补 `--tenant sankuai` 或 `--type ...`
3. 先输出已收敛的 `service-name`、`appkey`
4. 如果用户继续问流水线或模板，再进入 `cargo` / `plus`

## 场景 2：要找 test 流水线

用户可能会说：

- “帮我查某服务的 test 流水线”
- “我想知道这个服务对应哪个 stack”

推荐路径：

1. 若尚未确认服务，先执行 `tcx list-services --keyword ...`
2. 执行 `tcx cargo list-pipelines --env test --page-size 20 --max-items 100`
3. 根据结果整理 `stack_uuid` 与 `cargo_url`
4. 若用户要看详情，继续执行 `tcx cargo stack-info --stack-uuid ...`

## 场景 3：要看机器或失败机器

用户可能会说：

- “这个泳道哪些机器失败了”
- “这个服务现在落在哪些机器上”

推荐路径：

1. 先确保已有 `stack_uuid` 或 `cargo_url`
2. 执行 `tcx cargo list-hosts --stack-uuid ...`
3. 如要看失败机器，增加 `--status failed`
4. 如要看某服务，增加 `--service-name ...` 或 `--appkey ...`

## 场景 4：要看最近构建/部署记录

用户可能会说：

- “帮我看最近一次部署有没有成功”
- “最近这个服务发过版吗”

推荐路径：

1. 已知 `service-name` 时，执行 `tcx cargo list-jobs --service-name ... --job-type all`
2. 只看构建时，用 `--job-type build`
3. 只看部署时，用 `--job-type deploy`
4. 输出最近记录摘要，不直接倾倒所有历史

## 场景 5：要查 Plus 模板

用户可能会说：

- “帮我查这个服务有哪些 Plus 模板”
- “某个模板的详情是什么”

推荐路径：

1. 执行 `tcx plus base-info --service-name ...`
2. 执行 `tcx plus list-templates --service-name ...`
3. 若用户指定模板名，再执行 `tcx plus template-info --service-name ... --template-name ...`
4. 若已有模板 ID，优先执行 `tcx plus template-info --service-name ... --template-id ...`

## 场景 6：要查前端 Talos 模板

用户可能会说：

- “这个前端泳道有哪些模板”
- “Talos 上这个泳道发到 newtest 用哪个模板”

推荐路径：

1. 如需确认 appId，先执行 `tcx fe-deploy list-appids`
2. 执行 `tcx fe-deploy list-templates --swimlane ... --target newtest`
3. 输出模板候选与 `template-id`
4. 如果用户转为要发布，交给执行型 skill

## 场景 7：用户直接要求发版

用户可能会说：

- “帮我 build deploy 一下”
- “直接帮我发到 test”

处理规则：

1. 先用本 skill 补齐缺失标识
2. 明确说明本 skill 只做查询与参数发现
3. 切换到执行型 skill，例如 `pipeline-build-deploy`
