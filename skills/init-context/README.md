# /init-context

A Claude Code skill that bootstraps progressive disclosure context architecture in any project.

## The Problem

Your CLAUDE.md can be 40 lines and still drown the model. Inline domain knowledge loads hundreds of lines of context before Claude knows what the task is. A CSS fix loads your infrastructure docs. A deploy loads your stakeholder profiles.

Irrelevant context doesn't just waste tokens — it actively degrades reasoning quality. Tokens spent on context you don't need are stolen from thinking.

## The Fix

Replace inline knowledge with a task-based routing table. Claude loads 0 context files by default, reads the routing table, and grabs only what the task needs.

**Before:**
```markdown
## Context Loading
Always read:
- knowledge/business.md
- knowledge/products.md
- people/stakeholders.md
```

**After:**
```markdown
## Context Loading
Do NOT read knowledge/ files upfront. Load only what the task requires:

| Task type | Load these files |
|---|---|
| Business/strategy | knowledge/business.md |
| Building features | knowledge/products.md |
| People/org context | people/stakeholders.md |
| Deploying | knowledge/infrastructure.md |
```

## What It Does

Run `/init-context` in any project. The skill:

1. **Audits** your existing CLAUDE.md and MEMORY.md (line counts, router vs database classification)
2. **Classifies context** as cross-cutting (stays in CLAUDE.md) vs task-specific (goes to knowledge files) — this prevents burying shared concerns where the routing table blocks access
3. **Designs a routing table** mapping task types to context files
4. **Consolidates** into a single `knowledge/` directory — renames existing `docs/`/`context/` directories instead of creating parallel ones
5. **Deduplicates** content across files before writing
6. **Cleans** MEMORY.md into a pure index of one-liner pointers
7. **Verifies** the result (no "always read", no orphaned files, no duplicate content)

## Key Principles

- **CLAUDE.md** is a router, not a database. Cross-cutting context (commands, shared conventions, deploy essentials) stays inline. Task-specific knowledge gets routed.
- **One directory, not two.** If `docs/` already exists, rename it — don't create `knowledge/` alongside it.
- **Cross-cutting vs task-specific.** If more than half the routing table rows need it, it belongs in CLAUDE.md. Burying a cross-cutting concern in a knowledge file means the routing table actively blocks access to it.
- **Dedup before writing.** Check existing files for overlap before creating new ones.
- **MEMORY.md** is an index, not a notebook. One-liner links to individual files.
- **"Always read"** is a context engineering bug.

## Install

1. Copy the skill:
```bash
mkdir -p ~/.claude/skills/init-context
cp SKILL.md ~/.claude/skills/init-context/SKILL.md
```

2. Create the command trigger:
```bash
cat > ~/.claude/commands/init-context.md << 'EOF'
---
description: Bootstrap progressive disclosure context architecture in any project. Creates lean CLAUDE.md with routing table, knowledge/ directory, and clean MEMORY.md index. Run once per project.
---

Read `~/.claude/skills/init-context/SKILL.md` and follow its instructions.

**Arguments:** "$ARGUMENTS"
EOF
```

3. Run `/init-context` in any project.

## Background

Based on the progressive disclosure pattern: a lightweight index is always loaded, detailed files are loaded just-in-time based on the task, and raw data is only ever searched — never loaded into context directly.

## License

MIT
