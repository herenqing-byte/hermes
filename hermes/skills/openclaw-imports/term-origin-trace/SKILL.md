---
name: term-origin-trace
description: Trace the origin, evolution, mainstreaming, and competing definitions of a term/concept, then write a compact but evidence-backed timeline explainer. Use when asked to do 术语溯源、名词考据、概念史、who coined this、谁先提出、什么时候开始流行、某个词如何从小圈子走向行业主流, or when the user provides a sample thread/post and asks to “仿照这个写一个”.
---

# Term Origin Trace

## Overview

Produce a high-signal term-origin explainer that separates **prehistory**, **naming**, **popularization**, and **mainstream adoption**. Prefer “who named and popularized it” over overclaiming “who invented it”.

## Workflow

### 1. Define the claim surface first

Before searching, lock the exact scope:

- The target term in original language and likely variants
- The target domain (software engineering, AI agents, economics, etc.)
- The output goal: internal note, social thread, report section, or executive summary

Use a narrow framing sentence internally:

> I am tracing not just earliest occurrence, but the path from prior practice → explicit naming → public spread → industry acceptance.

### 2. Build a four-layer timeline

Always organize findings into these layers:

1. **前史 / Prehistory**
   - Earlier adjacent usage in another field
   - Similar practice before the term became explicit
2. **显性命名 / Explicit naming**
   - Earliest strong public instance that clearly uses the term in the target sense
3. **引爆传播 / Popularization**
   - Person/company/post that made the term legible to a wider audience
4. **行业定型 / Mainstreaming**
   - Multiple credible actors adopt similar framing, making the term stable enough to reference

Do not collapse these into a single “inventor” story unless evidence is unusually strong.

### 3. Rank evidence instead of treating all mentions equally

Use this reliability order:

- First-party primary sources: company blogs, author posts, official docs, talks
- Contemporary third-party analysis quoting primary sources
- Later retrospectives
- Social reposts or unattributed summaries

Prefer exact publication dates and exact wording when possible.

### 4. Separate three different questions

Most term-origin confusion comes from mixing these up:

- **Who first used similar practice?**
- **Who first used this exact term in the relevant sense?**
- **Who made the term mainstream?**

If the answers differ, say so explicitly.

### 5. Write with calibrated certainty

Use these labels in your own reasoning and optionally in output:

- **✅ 已验证**: backed by direct primary evidence
- **⚠️ 来源分歧**: conflicting accounts or ambiguous chronology
- **📌 单源未验证**: plausible but currently anchored on one source

If chronology is uncertain, prefer:

- “目前可确认的早期公开记录之一”
- “更像是命名并引爆，而非凭空发明”
- “前史早已存在，但在 X 语境下由 Y 推成显性概念”

Avoid absolute claims unless you truly have them.

## Default output structure

Use this structure unless the user asks for another format. The goal is not just to be correct, but to resemble a strong “industry term origin” note that can be forwarded as-is.

### 标题

Use a title of the form:

> 术语溯源：[term] —— 从[前史领域]到[当前主流语境]

### 开头摘要

Start with 2-4 sentences answering:

- What the term roughly means today
- Whether the practice predates the wording
- Who named it / who mainstreamed it / why it matters now

### Mandatory body sections

Always include these sections in this order:

1. **术语溯源：从前史到当前语境**
   - Explain the prehistory briefly
   - State whether practice came before naming
   - Clarify whether the current meaning is narrower than earlier adjacent uses

2. **🔑 关键时间线**
   - Use dated bullets
   - Each bullet should answer why this moment matters
   - Prefer 4-8 milestones rather than exhaustive chronology

3. **🏢 各大公司 / 人物的核心观点**
   - Include 3-6 actors when available
   - For each actor, summarize in 1 short paragraph:
     - how they define the term
     - what problem they think it solves
     - what makes their framing distinctive
   - Prefer named people/companies over anonymous community summaries

4. **💡 概念的核心争议**
   - Include at least one criticism, boundary dispute, or conceptual tension
   - Good examples: “old wine in new bottles”, “framework vs harness”, “prompt vs context”, “naming vs invention”

5. **总结一句话**
   - Compress the whole story into one sentence
   - Prefer the pattern: “X practices existed earlier, but Y named/popularized/mainstreamed the term in Z context.”

### Output density standard

A good output should feel like a high-signal mini-brief, not a research dump:

- brief prehistory
- milestone timeline
- actor-by-actor viewpoints
- one sharp dispute section
- one hard closing line

If the user says “仿照这个写”, prioritize matching this composition and rhythm over adding extra background.

## Writing style

Write like an informed operator, not an academic historian:

- Lead with the punchline
- Keep chronology crisp
- Quote only the minimal decisive phrase
- Compress interpretation into a few strong judgments
- Avoid padding with generic industry background

Good sentence patterns:

- “这个概念往往不是被某个人发明，而是被某个人命名并引爆。”
- “实践先于术语，术语再反过来重组行业认知。”
- “真正重要的不是谁最早提到，而是谁把它变成了可传播、可复用、可对齐的概念。”

## Distinguish origin from framing

When the user really wants a modern strategic concept piece, do not get trapped in pure philology. End with:

- Why the term matters now
- What operational distinction it creates
- What decision it changes for teams or managers

## Quality bar

A good result should let the user answer all of these in under one minute:

- 这个词之前有没有前史？
- 谁最早在当前语境下明确这么叫？
- 谁把它带火了？
- 行业内现在是怎么理解它的？
- 它和相近概念到底差在哪？

## Common failure modes

Avoid these mistakes:

- Treating earliest adjacent usage as equivalent to current meaning
- Confusing coined / named / popularized / standardized
- Copying a timeline without judgment
- Overstating certainty from one blog post
- Writing a history note that never explains why the term matters

## If the user says “仿照这个写一个”

Treat the sample as a target composition, not just a loose inspiration.

Extract and preserve these structural signals:

- a short “前史” paragraph that shows practice predates terminology
- a **🔑 关键时间线** section with dated milestones
- a **🏢 各大公司/人物的核心观点** section with named actors
- a **💡 概念的核心争议** section that adds tension rather than praise
- a one-sentence summary that answers naming vs popularization cleanly

Mirror the structure, density, and rhetorical rhythm. Do not flatten the result into generic research prose.

## Resources

- For a compact checklist and phrasing patterns, read `references/trace-checklist.md`.
