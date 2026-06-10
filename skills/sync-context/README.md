# /sync-context

End-of-session context sync for Claude Code. Reviews what was learned in the conversation and proposes updates to the project's context files so the next session starts up to date.

## What it does

At the end of any meaningful session, `/sync-context`:

1. Reads the full conversation
2. Compares it against existing context files (`knowledge/`, `people/`, `projects/`)
3. Proposes specific updates — for example, `ADD to knowledge/data-model.md: orders and deliveries share one ID space. We tried splitting them in March; reverted because join cost doubled.`
4. You approve or modify each proposal
5. Writes and commits the approved changes

## The idea

The code in your repo tells Claude (and new human teammates) what the system **is**. `/sync-context` captures what the code doesn't — the **why**: business context, rejected alternatives, architecture rationale, constraints that still hold.

Each session, you decide what was actually worth remembering. Over weeks, the project accumulates real institutional memory that both humans and AI work from.

## Install

Copy this folder into your Claude Code skills directory:

```bash
cp -r skills/sync-context ~/.claude/skills/
```

Then run `/sync-context` at the end of a meaningful session.

## Project structure

The skill expects (or creates) three folders at the project root:

- `knowledge/` — business, architecture, decisions that still hold
- `people/` — stakeholder preferences, decisions, open questions
- `projects/` — workstreams in progress, status, research artifacts

First time you run the skill on a project, it will offer to create these folders if they don't exist. You can use a subset (e.g. only `knowledge/` if there are no stakeholders) or different names to match your project's conventions — the skill adapts.

## When to use

- At the end of any non-trivial session
- After a design discussion, a debugging journey, or a decision that matters
- Before closing Claude Code for the day

Do **not** run it after trivial sessions (one-line fixes, typos) — there's nothing worth persisting.
