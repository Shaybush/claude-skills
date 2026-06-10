---
name: init-context
description: "Bootstrap progressive disclosure context architecture in any project. Turns CLAUDE.md into a router with a task-based routing table, consolidates context into a single knowledge directory, and cleans MEMORY.md into a pure index. Use when starting a new project, when CLAUDE.md has 'always read' directives, when context feels bloated, or when the user says /init-context."
---

# /init-context

Turn CLAUDE.md into a router, not a database.

The core problem: inline domain knowledge in CLAUDE.md loads tokens before the model knows the task. This isn't just wasteful — irrelevant context actively degrades reasoning quality. The fix is a routing table: load nothing by default, route to the right file based on the task.

**Arguments:** "$ARGUMENTS"

## Audit

Read the project root and report what exists with line counts:

- `CLAUDE.md` — classify: **router** (mostly pointers/structure) or **database** (inline domain knowledge, architecture details, conventions beyond the essential)
- `MEMORY.md` or auto-memory files — classify: **pure index** (one-liner pointers) or **hybrid** (mix of pointers and inline content)
- Context directories (`knowledge/`, `context/`, `docs/`) — what exists, any duplication
- Subdirectory `CLAUDE.md` files — any per-module instructions
- `README.md` — project description if no CLAUDE.md

Look for these red flags:
- "Always read" or "Before any task, read" directives
- Inline paragraphs of domain knowledge in CLAUDE.md or MEMORY.md
- Multiple context directories (`docs/` AND `context/` AND `knowledge/`)
- Context files that are always loaded but only relevant to specific task types

Report findings to the user before changing anything.

## Understand the Project

Extract the project's purpose from existing files. If nothing exists, ask:
1. What does this project do?
2. What are the main modules or areas of work?
3. What context do you find yourself repeatedly explaining to Claude in this repo?

That third question identifies exactly what should become routed context files — if you keep explaining it, it should be written down and loaded on demand.

## Classify Context: Cross-Cutting vs Task-Specific

Before designing the routing table, sort every piece of context into two buckets:

**Cross-cutting** (stays in CLAUDE.md) — information needed by most task types. Examples: template variable names used across the codebase, shared terminology, project-wide conventions, commands, deploy essentials. The test: if more than half the routing table rows would need it, it's cross-cutting.

**Task-specific** (goes in a knowledge file) — information only relevant to one or two task types. Examples: matching algorithm details, GCP IAM roles, deploy troubleshooting steps, feature specs.

Getting this wrong is the #1 source of problems. If you bury a cross-cutting concern in a task-specific file, the routing table actively blocks access to it for other tasks.

## Design the Routing Table

Build a task-based routing table that maps natural task descriptions to context files. Present it for confirmation before proceeding.

```markdown
## Context Loading

Do NOT read knowledge/ files upfront. Load only what the task requires:

| Task type | Load these files |
|---|---|
| [natural task description] | [1-2 specific file paths] |
```

Routing table principles:
- Every file load is conditional on the task — no "always read"
- Each row maps to 1-2 files maximum, not a whole directory
- The task descriptions in the left column should be specific enough that the model can match its current task without ambiguity
- If subdirectories have their own CLAUDE.md (auto-loaded when working there), note that in the table so context isn't double-loaded

## Scaffold

Apply the routing table to the project. The goal for each file:

**CLAUDE.md** — a router. Contains: project description, routing table, repo structure map, essential commands, deploy essentials, and cross-cutting context identified above. Does not contain: task-specific domain knowledge, architecture deep-dives, lengthy conventions. The test: if a section is only relevant to some tasks, it belongs in a knowledge file referenced from the routing table, not inline.

### One directory, not two

All context files go in ONE directory. Choose a descriptive name — `knowledge/` is a good default because it signals "on-demand context for the model" vs generic `docs/` which could mean anything.

**If a context directory already exists** (`docs/`, `context/`, etc.): rename it to `knowledge/` (or whatever name fits the project) and consolidate. Do NOT create a parallel directory. Use `git mv` to preserve history.

**If no context directory exists**: create `knowledge/` and extract task-specific content from CLAUDE.md into it.

### Deduplication

Before writing any new knowledge file, check for content overlap with existing files in the same directory. If two files cover the same topic:
- Keep the more detailed version
- Remove the duplicate content from the other
- Never have the same information in two places

### MEMORY.md

If auto-memory exists: MEMORY.md should be a pure index of one-liner pointers to individual memory files. Any inline content (paragraphs, technical details, gotchas) gets extracted into its own memory file. The index entry for each file should be descriptive enough that the model can decide relevance without opening it.

## Verify

After scaffolding, check:
- CLAUDE.md is a router — no inline domain knowledge, no "always read" directives
- Cross-cutting context is in CLAUDE.md, not buried in a knowledge file
- All knowledge files are in one directory (no parallel `docs/` + `knowledge/`)
- MEMORY.md (if exists) is a pure index — no inline paragraphs, just one-liner pointers
- Every knowledge/ file is reachable from the routing table
- No orphaned context (files that exist but aren't referenced from any routing entry)
- No duplicate content across knowledge files
- Subdirectory CLAUDE.md files are lean (stack, commands, gotchas — not domain knowledge)

Report the final structure and what changed.
