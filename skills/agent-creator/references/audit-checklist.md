# Auditing and Migrating an Existing Agent

Use when an agent predates the standard, or when `validate_agent.py` reports failures.
Run `scripts/validate_agent.py --all` (under `${CLAUDE_PLUGIN_ROOT}/skills/agent-creator/`) first — it catches every mechanical defect, so the
read-through only has to judge content.

## What a legacy agent looks like

The pre-standard agents (`dba-administrator`, `graphql-architect`) share a recognisable
shape, and it is worth knowing because it is what a generic agent-generator produces:

- `description` is a bare one-line sentence in quotes, with **no `<example>` blocks**
- No `color`, no `memory` — so the agent has no memory store and no terminal identity
- Body is an undifferentiated wall of **checklists**: `Database administration checklist:`,
  `GraphQL architecture checklist:`, followed by twenty unordered bullet fragments
- Opens with `When invoked:` and a numbered list, instead of the identity paragraph
- References a `context manager` that does not exist in this setup
- No `## Knowledge Base`, no `## Always`, no `## Memory Discipline`
- Absent from the `CLAUDE.md` routing table, so nothing ever routes to it

The checklists are the real problem. `- High availability configured (99.99%)` is a
success criterion with no instruction in it — the agent cannot act on it, and it costs
context on every invocation.

## Migration order

Work top-down; each step is independently verifiable.

### 1. Fix the frontmatter

- `name` must equal the filename. **`dba-engineer.md` declaring `name: dba-administrator`
  is the live example of this bug** — decide which is canonical, then rename the file or
  the field so they agree. Renaming the field breaks any `## Always` line in another agent
  that routes to the old name; renaming the file breaks nothing. Prefer renaming the file.
- Add `color`, choosing one not already taken (`validate_agent.py --all` lists collisions).
- Add `memory`: `project` if its learnings are codebase-specific, `user` if they are about
  the machine or an account.
- Keep `tools` and `model` unless the tool list contradicts what the body tells it to do —
  a body instructing it to inspect databases via MCP while `tools:` omits every MCP is a
  real contradiction, and the body or the field must give.

### 2. Rewrite the `description`

Keep the existing sentence as the trigger, then add 3–5 `<example>` blocks in the escaped
format from `agent-anatomy.md`. Mine the old checklists for the examples — a checklist line
like `RTO < 1 hour, RPO < 5 minutes` implies a real trigger ("set up disaster recovery for
the orders database"). This is the step that makes the agent routable, so do not skip it.

### 3. Convert checklists into the four sections

The mapping is mechanical once seen:

| Legacy content | Goes to |
| --- | --- |
| `When invoked:` numbered list | `## Workflow`, rewritten as imperative steps with "read the KB file" inserted |
| Checklist lines that are **rules** (`Never expose credentials`) | `## Always`, kept imperative |
| Checklist lines that are **targets** (`99.99% uptime`, `sub-second query performance`) | Fold into the identity paragraph or a single Always line — do not keep them as bullets |
| Deep procedural detail, tool matrices, config examples | A KB file under `~/.claude/docs-claude/kb/<area>/`, referenced from the `## Knowledge Base` table |
| Anything referencing a `context manager` | Delete |

A migrated body should be **shorter** than the original. Detail moves to the KB, where it
loads on demand instead of on every invocation. If the rewrite came out longer, content
that belonged in a KB file stayed in the agent.

### 4. Add the standard sections

`## Knowledge Base` (with at minimum `shared/concurrency.md`), the two global code rules in
`## Always`, a verification gate line, `## Memory Discipline` verbatim from
`assets/agent-template.md`, and a closing posture sentence.

### 5. Wire it up

- Add the routing row to the governing `CLAUDE.md`.
- If step 3 produced a KB file, create it and add its row to `docs-claude/kb/README.md`.
- Add deferral lines to other agents if this one now owns something they were doing.

### 6. Re-validate

`scripts/validate_agent.py <file>` must pass clean, then re-read the body once for the
things a validator cannot see: does each example describe a genuinely different trigger,
does every KB path resolve, is the gate line naming commands that actually exist in the
repos this agent works in.

## Retire instead of migrating when

The agent has no rows in the routing table **and** no corresponding KB area **and** its
domain is already covered by a conforming agent. Migrating creates a router ambiguity that
costs more than the agent is worth. Say so and propose deletion rather than doing the
rewrite silently.
