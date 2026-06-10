---
name: sync-context
description: "End-of-session context sync. Reviews what was learned in the conversation and proposes updates to knowledge/, people/, and projects/ files. Use when the user says /sync-context, 'sync context', 'update context', or at the end of a session in a project that uses the compounding-context structure."
---

# /sync-context — Compound Project Context

Sync what was learned this session into the project's context files so the next session starts smarter.

**Arguments:** "$ARGUMENTS"

## Step 1: Detect or set up context structure

Check which context directories exist at the project root:

```bash
ls docs-claude/core/ docs-claude/people/ docs-claude/projects/ 2>/dev/null
```

If none exist, ask the user if they want to set up the compounding-context structure. Default: create `docs-claude/core/`, `docs-claude/people/`, and `docs-claude/projects/` directories. The user may want a subset (e.g., only `docs-claude/core/` for a solo project without stakeholders) or different folder names to match existing project conventions — adapt accordingly.

If a subset already exists, use what's there. Don't create missing folders unless the user asks.

Once the structure exists (or has been created), proceed to Step 2.

## Step 2: Read current context

Read all existing context files to understand what's already captured:

```bash
# List all context files
find docs-claude/core/ docs-claude/people/ docs-claude/projects/ -name "*.md" -type f 2>/dev/null
```

Read each file to understand the current state of captured knowledge.

## Step 3: Review the session

Analyze this conversation for new information that should persist. Look for:

**Knowledge updates** (docs-claude/core/):

- Business decisions or constraints learned
- Technical decisions made
- New requirements or scope changes
- Platform, tool, or vendor evaluations
- Domain knowledge that was clarified

**People updates** (docs-claude/people/):

- Stakeholder preferences revealed ("she wants it simple", "he pushed back on X")
- Communication style observations
- Decisions a person made and why
- New open questions for a stakeholder
- Answers to previously open questions (close them)

**Project updates** (docs-claude/projects/):

- New workstreams identified → create a folder with a README.md
- Research or analysis done → save as an artifact in the relevant project folder
- Decisions made within a workstream
- Status changes or blockers

## Step 4: Propose updates

Present ALL proposed changes to the user in a clear format:

```
## Context Updates

### docs-claude/core/business.md
- ADD: [what to add and why]

### docs-claude/people/stakeholder.md
- UPDATE preferences: [what was learned]
- CLOSE question: [question that was answered]
- ADD decision: [decision made and date]

### docs-claude/projects/platform-selection/
- CREATE: research-notes.md with [summary of what was discussed]
```

Group by file. Show what changes and why. Be specific — quote the conversation where relevant.

## Step 5: Apply approved updates

After the user approves (they may modify or reject some), apply the changes using the Edit tool. For new files, use Write.

Rules:

- Never remove existing content unless it's clearly wrong or superseded
- Add to existing sections rather than rewriting them
- Date-stamp decisions: `- [YYYY-MM-DD] Decided to use vendor X for Phase 1`
- Keep files scannable — use headers, short bullets, tables where appropriate
- If a docs-claude/people/ file has placeholder fields (like "Communication style:"), fill them in rather than adding a new section

## Step 6: Commit context updates

```bash
git add docs-claude/core/ docs-claude/people/ docs-claude/projects/
git diff --cached --stat
```

If there are changes, commit them:

```bash
git commit -m "sync-context: update [list of files changed]"
```

## Notes

- This skill is about **persistent context**, not session notes. Don't save ephemeral details (what commands were run, debugging steps tried). Save what matters for the next session.
- Bias toward updating existing files over creating new ones.
- If nothing meaningful was learned this session, say so. Don't force updates.
- Works in any project with a docs-claude/core/, docs-claude/people/, docs-claude/projects/ structure — or any subset that fits the project.
