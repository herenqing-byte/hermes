User profile: 用户：何仁清 / herenqing
§
User profile: 时区：Asia/Shanghai
§
User profile: 角色主线：从早期配送/履约算法负责人，演进为履约技术负责人、履约平台 / B-team 管理者、业研 AI 委员会主席。
§
User profile: 工作重点：履约/配送核心业务、系统能力建设、架构治理、跨团队协同、AI Coding / Agent / 企业级 AI 工程体系推进。
§
User profile: 近年主线演进：
§
User profile: 2021：调度、ETA、定价、图灵平台、骑手安全与公平
§
User profile: 2022：履约技术、架构、稳定性、跨 BU 协同
§
User profile: 2023：技术前置、资源 ROI、主动参与业务决策
§
User profile: 2024：L 型组织建设、AI 技术体系、Agent、行业调研
§
User profile: 2025：L 型组织建设、AI 委员会工作
§
User profile: 工作风格：洞察快、判断强、决策果断、敢担责、推动技术前置。
§
User profile: 已知短板：耐心不足、共情偏弱、沟通偏直接；近两年主动改进为共创、讨论、白板、低压力沟通。
§
User profile: AI / Agent 关注点：memory / context engineering、observability / trace / 审计、human-in-the-loop、multi-agent 协作、CLI / MCP、工作流、知识接入、Agent 工程体系。
§
User profile: 偏好：结论先行，回复简短干练，少废话；复杂/耗时任务优先用 subagent 在后台并行处理，前台保持实时沟通。
§
User profile: 主会话治理：把当前窗口当“轻前台”，只放结论、关键证据、下一步动作；日志、长网页、长工具输出、排障过程默认不要直接灌进主会话，优先放到 subagent / 侧路处理，避免 context 爆掉和排队变重。
§
User profile: 大象里发链接时，不要裸发 URL；默认用标题链接格式（如 [标题](url)）。多条链接不要一坨一起发，按条分开发，便于阅读。
§
User profile: 服务原则：把口头要求落成机制、配置、记录与持续跟进；能自己解决的尽量自己解决，不反复把问题抛回给用户。
§
User profile: 长程任务执行偏好：执行期间需阶段性主动同步进展；若用户未回复，不要停在等待态，应默认自主决策、继续推进下一步，并由主 Agent 指挥 subagent 持续运行。
§
User profile: 2026-03-26 新增硬约束：当前轮次及后续类似任务，采用“继续执行 + 每个关键阶段主动同步”机制，不等用户追问；这不是话术要求，而是执行流程的一部分。
§
用户今天完成了 Hermes 大象接入调试：最终通过安装并启用 `@ai/daxiang@1.0.0-beta9`，让 `channels.daxiang` 真正被 Hermes 识别并连接成功；此前仅 `npm install -g @ai/daxiang` 不足以让 Hermes 加载该 channel。
§
大象已实际连通，用户 `herenqing`（大象 ID: `2011693`）通过大象向机器人发送了“你好/太好了/你现在是什么模型”等消息，确认收发正常。
§
期间也安装并测试过 elephant 方案；用户最终明确希望使用 `channels.daxiang` 这一路径，而不是仅保留 elephant。
§
用户要求以后优先通过本机 skill 查找美团 KM/学城能力；本机确实存在 skill：`/Users/herenqing/.Hermes/skills/sankuai-km-docs/SKILL.md`。
§
使用 KM skill 读取用户提供的学城文档《个人述职》（KM 文档 ID `364372093`）时，当前读取链路报错：文档密级为 `C4`，但当前阈值被限制为 `C2`，所以无法读取。Skill 文档本身写明常规情况下仅拒绝 `C5/C6`，说明当前环境里还有额外阈值配置需要排查。
§
用户希望我通过 KM skill 阅读他 2024/2025/2026 年的学城文档，尤其个人述职，用来了解他的背景；后续应优先继续解决 C4 读取阈值问题。
§
用户今天还要求安装 `KeepingYouAwake`，已从官方 GitHub release 安装到 `~/Applications/KeepingYouAwake.app` 并打开。
§
为避免 shell 中再次出现 `npm`/`node` 找不到，已在 `~/.zshrc` 增加 NVM Node v24.14.0 的兜底 PATH。
§
用户新增偏好：subagent 完成后要主动向主会话反馈；如果长时间没有反馈，主代理应主动检查状态，并与 subagent 沟通修复问题，不能只被动等待。
§
2026-03-19: 目标优先级：高治理 > 低成本。
