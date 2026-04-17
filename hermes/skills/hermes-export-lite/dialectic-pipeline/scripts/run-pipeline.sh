#!/usr/bin/env bash
# run-pipeline.sh — 辩证分析 Pipeline 编排示例
#
# 用法: ./run-pipeline.sh <input-file>
#
# 此脚本展示如何用 OpenClaw sub-agent 编排 3 阶段流程。
# 实际使用中 Agent 会直接 spawn sub-agent，此脚本仅作参考。

set -euo pipefail

INPUT="${1:?用法: $0 <input-file>}"
WORKDIR="/root/.openclaw/workspace/dialectic-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$WORKDIR"

echo "📂 工作目录: $WORKDIR"
echo "📄 输入文件: $INPUT"
cp "$INPUT" "$WORKDIR/input.md"

# ── Phase 1: Draft ──
echo ""
echo "═══════════════════════════════════════"
echo "📝 Phase 1: Draft（深度分析）"
echo "═══════════════════════════════════════"
cat <<'PROMPT' > "$WORKDIR/phase1-prompt.md"
你是领域专家。阅读以下内容，按 Draft 格式输出深度分析。
要求：
- 有明确立场，不做两边都说的太极拳
- 每个论断必须可证伪
- 按格式输出：核心论断 → 支撑证据(带强度) → 趋势判断 → 行动建议
PROMPT
cat "$WORKDIR/input.md" >> "$WORKDIR/phase1-prompt.md"
echo "→ Draft prompt 已生成: $WORKDIR/phase1-prompt.md"
echo "→ [实际运行] spawn sub-agent 执行 Phase 1，输出存 $WORKDIR/phase1-draft.md"

# ── Phase 2: Critique ──
echo ""
echo "═══════════════════════════════════════"
echo "🔍 Phase 2: Critique（对抗性质疑）"
echo "═══════════════════════════════════════"
cat <<'PROMPT' > "$WORKDIR/phase2-prompt.md"
你是批判审查员。阅读以下 Draft 分析，按 Critique 格式输出质疑报告。
要求：
- 参考质疑清单逐项检查
- 至少 1 个红色质疑，找不到要说明原因
- 按三色分级：🔴红色 🟡黄色 🟢绿色
PROMPT
echo "[Phase 1 Draft 输出将追加到此处]" >> "$WORKDIR/phase2-prompt.md"
echo "→ Critique prompt 已生成: $WORKDIR/phase2-prompt.md"
echo "→ [实际运行] spawn sub-agent 执行 Phase 2，输出存 $WORKDIR/phase2-critique.md"

# ── Phase 3: Synthesis ──
echo ""
echo "═══════════════════════════════════════"
echo "⚖️  Phase 3: Synthesis（综合裁判）"
echo "═══════════════════════════════════════"
echo "→ [实际运行] 主 Agent 读取 phase1-draft.md + phase2-critique.md"
echo "→ 输出综合裁决：结论存活表 + 修正后结论 + 最终建议(带置信度) + 信息缺口"
echo "→ 最终输出存 $WORKDIR/phase3-synthesis.md"

echo ""
echo "═══════════════════════════════════════"
echo "✅ Pipeline 编排完成"
echo "═══════════════════════════════════════"
echo "产出文件："
echo "  $WORKDIR/phase1-draft.md"
echo "  $WORKDIR/phase2-critique.md"
echo "  $WORKDIR/phase3-synthesis.md"
