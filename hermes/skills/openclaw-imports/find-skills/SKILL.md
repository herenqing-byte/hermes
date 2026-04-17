---
name: find-skills
description: Discover and install skills from the open agent skills ecosystem (skills.sh). Use when the user asks "find a skill for X", "is there a skill for X", "can you do X" where X might be a specialized capability, or wants to search for tools, templates, or workflows to extend agent capabilities.
---

# Find Skills

Helps discover and install skills from the open agent skills ecosystem via `npx skills` CLI.

## Key Commands

- `npx skills find [query]` — Search for skills by keyword
- `npx skills add <owner/repo@skill> -g -y` — Install a skill globally
- `npx skills check` — Check for updates
- `npx skills update` — Update all installed skills

Browse at: https://skills.sh/

## Workflow

### 1. Search

Run with a relevant query based on the user's need:

```bash
npx skills find [query]
```

Examples:
- "make my React app faster" → `npx skills find react performance`
- "help with PR reviews" → `npx skills find pr review`
- "create a changelog" → `npx skills find changelog`

### 2. Present Results

Show the user:
- Skill name and what it does
- Install command
- Link to learn more at skills.sh

### 3. Install

```bash
npx skills add <owner/repo@skill> -g -y
```

## Common Categories

| Category | Example Queries |
|---|---|
| Web Dev | react, nextjs, typescript, tailwind |
| Testing | jest, playwright, e2e |
| DevOps | deploy, docker, kubernetes, ci-cd |
| Docs | readme, changelog, api-docs |
| Code Quality | review, lint, refactor |
| Design | ui, ux, design-system, accessibility |

## When No Skills Found

Acknowledge it, offer to help directly, and suggest:
```bash
npx skills init my-skill-name
```
