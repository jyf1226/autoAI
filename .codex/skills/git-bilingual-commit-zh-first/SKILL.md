---
name: git-bilingual-commit-zh-first
description: Use when writing git commit messages that must include both Chinese and English with Chinese first.
---

# Git Bilingual Commit (Chinese First)

## Overview

This skill enforces a bilingual commit message format where Chinese appears before English, so teams can read intent quickly in Chinese while keeping an English mirror for cross-language collaboration.

## When to Use

- The user asks for "中英文提交信息", "bilingual commit", or "中文在前".
- Team policy requires Chinese-first commit subjects.
- A repo has mixed Chinese/English contributors and wants consistent commit readability.

Do not use when the user explicitly asks for English-only or Chinese-only commit messages.

## Required Format

Always keep Chinese first, then English.

```text
<中文主题> / <English subject>

<中文说明（1-3行，讲为什么）>
<English explanation (1-3 lines, mirror intent)>
```

## Commit Rules

1. Subject must contain both Chinese and English, with Chinese first.
2. Chinese and English should express the same intent; avoid different meanings.
3. Prioritize "why" over "what changed".
4. If trailers are required by repo policy, keep them after the bilingual body.
5. If the user gives only one language, generate the missing language and keep Chinese first.

## Examples

### Good

```text
初始化项目并加入 AGENTS 中文说明 / Initialize project and add Chinese AGENTS guide

建立基础仓库结构并补充中文操作说明，降低新成员上手成本。
Set up the base repository structure and add a Chinese operation guide to improve onboarding speed.
```

### Bad

```text
Initialize project
```

Bad because it is not bilingual and does not keep Chinese first.

## Common Mistakes

- English appears before Chinese in subject.
- Chinese and English describe different scopes.
- Body only lists file changes without intent.
- Subject is bilingual, but body is single-language while user asked bilingual.

