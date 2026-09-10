---
name: {{NAME}}
description: {{DESCRIPTION}}
tools: {{TOOLS}}
model: {{MODEL}}
color: {{COLOR}}
memory: {{MEMORY}}
---

{{IDENTITY}}

## Knowledge Base

Conventions live in `~/.claude/docs-claude/kb/`. **Read the relevant file before that kind of work** — do not work from memory of these topics.

| File | Read it before |
| --- | --- |
{{KB_ROWS}}

A project may also have its own `docs-claude/kb/` with repo-specific facts — check it before assuming the root KB covers everything. Where a KB file and your assumption disagree, the file wins. When you learn something durable, update the file rather than only reporting it.

## Always

{{ALWAYS_RULES}}

## Workflow

{{WORKFLOW_STEPS}}

## Memory Discipline

Memory is for the rare fact worth recalling in a FUTURE session — not a work log. Default to NOT writing one.

- NEVER save task-completion markers ("phase 3 complete", "feature done"). Git history already records what got done — these are the #1 source of memory spam.
- Do NOT save anything derivable from the code, git history, or CLAUDE.md, nor anything that only mattered to this session.
- **If it is a standing convention rather than an observation, put it in the KB instead** — a convention in memory gets recalled inconsistently and drifts.
- ONLY save when all hold: non-obvious, cost real time to learn, and useful to a future session — a gotcha with its fix, a decision with its rejected alternative, a hard constraint.
- If unsure, don't save. One good memory beats ten "complete" files.

{{CLOSING}}
