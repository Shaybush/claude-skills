---
name: agent-creator
description: Creates new subagent definitions that match this setup's house standard, and audits or migrates existing ones. This skill should be used when the user wants to add a new agent (e.g. "create a security agent", "we need an agent for Terraform work", "add a QA engineer agent"), when an existing agent needs bringing up to standard, or when agent definitions should be linted. It runs a structured interview, stamps the agent from the shared template, wires it into the CLAUDE.md routing table and the knowledge base, and validates the result.
---

# Agent Creator

## Purpose

Agents in this setup follow a strict shared shape — frontmatter, a Knowledge Base table,
`## Always`, `## Workflow`, and a verbatim Memory Discipline block. That shape carries real
load: the `description` decides whether the agent is ever routed to, the KB table decides
whether it reads conventions or invents them, and the routing table in `CLAUDE.md` decides
whether it exists as far as the main session is concerned. An agent written freehand
typically misses two or three of these and quietly never gets used.

This skill produces agents that match the standard, and repairs ones that do not.

## When to use

- Creating a new agent for a domain not covered by the existing ones.
- An agent exists but is never invoked — usually a `description` with no examples, or a
  missing routing-table row.
- Bringing a legacy or third-party agent definition up to the house standard.
- Linting agent definitions after manual edits.

## Resources

Paths below are relative to `${CLAUDE_PLUGIN_ROOT}/skills/agent-creator/`.

| File | Use |
| --- | --- |
| `references/agent-anatomy.md` | Field-by-field spec of every frontmatter key and body section, with the real conventions behind each. **Read before writing or editing any agent.** |
| `references/audit-checklist.md` | The migration procedure for legacy agents, and when to retire rather than migrate |
| `assets/agent-template.md` | The template `new_agent.py` stamps. Also the source of truth for the Memory Discipline block — copy it, never paraphrase |
| `assets/kb-file-template.md` | Starting structure for a new KB file |
| `scripts/new_agent.py` | Renders the template from a JSON spec and writes it to the right directory |
| `scripts/validate_agent.py` | Lints one agent or `--all`; catches name/filename mismatch, missing examples, dead KB paths, colour collisions, unrouted agents |

## Creating a new agent

### Step 1 — Establish the trigger cases

Before any decisions about model or tools, get **3–5 concrete things a user would say**
that should route to this agent. Ask for them directly; if the user offers a domain rather
than examples, propose examples and have them confirm or correct.

These become the `<example>` blocks, and they are the highest-leverage part of the file —
the router matches on them. They must cover **distinct trigger shapes**, not one situation
restated. Reject a set where every example is the same verb on a different noun.

Also settle here: is this genuinely uncovered by the existing agents? Check
`~/.claude/CLAUDE.md`'s routing table. An agent overlapping an existing one creates router
ambiguity — say so and propose extending the existing agent instead.

### Step 2 — Interview for the remaining fields

Use `AskUserQuestion`, batched into calls of at most four questions. Recommend a default in
each rather than presenting an open choice.

| Decide | Default to recommend | Read for context |
| --- | --- | --- |
| Scope: user (`~/.claude/agents/`) or project (`<repo>/.claude/agents/`) | user, unless the domain only exists in one repo | — |
| `model`: `sonnet` or `opus` | `sonnet`; `opus` only when the work is architectural judgment over long context | `agent-anatomy.md` § model |
| `tools` preset | The app-dev preset for code-writing agents | `agent-anatomy.md` § tools |
| `memory`: `project` or `user` | `project`, unless learnings are about the machine/accounts | `agent-anatomy.md` § memory |
| `color` | Any unused one — run `validate_agent.py --all` to see what is taken | — |
| KB files it must read | Its domain file + `shared/concurrency.md` | `agent-anatomy.md` § Knowledge Base |
| Verification gate commands | Whatever that stack actually runs — ask, do not guess | — |
| What it owns / defers to other agents | — | `agent-anatomy.md` § Cross-agent routing |

Do not ask about the Memory Discipline block, the two global code rules, or the KB preamble
— those are fixed and come from the template.

### Step 3 — Generate

Write the interviewed values to a JSON spec in the scratchpad directory
(`new_agent.py --example` prints the shape), then:

```bash
AC="${CLAUDE_PLUGIN_ROOT}/skills/agent-creator/scripts"
"$AC/new_agent.py" --spec /path/to/spec.json
```

It refuses to overwrite without `--force`, warns on colour collisions, and prints the
wiring steps that remain.

Compose the `description` carefully — the examples must be joined with **literal `\n`
escapes**, not real newlines. See `agent-anatomy.md` § description for the exact format.

### Step 4 — Wire it up

Three things the script deliberately does not do, because each needs judgment:

1. **Routing table.** Add a row to the governing `CLAUDE.md` — `~/.claude/CLAUDE.md` for a
   user-scope agent, the repo's own for a project-scope one. Without this row nothing routes
   to the agent. Phrase the Task cell as the technologies and task types, matching the
   existing rows' density: `Mobile: Expo, React Native, gluestack-ui, NativeWind, EAS`.

2. **KB file.** If the agent's Knowledge Base table names a file that does not exist, create
   it from `assets/kb-file-template.md`, populated with the conventions surfaced during the
   interview — not left as an empty stub. Root KB (`~/.claude/docs-claude/kb/`) for
   cross-project truth, project KB (`<repo>/docs-claude/kb/`) for repo-specific truth; the
   distinction is spelled out in the KB README. Add a row to that README's Contents table.

3. **Deferral lines.** If the new agent owns work another agent currently does, add the
   routing line to that agent's `## Always` — e.g. *"Database schema and index design goes
   to `dba-administrator`."* Ownership without matching deferrals changes nothing.

### Step 5 — Validate

```bash
"$AC/validate_agent.py" ~/.claude/agents/<name>.md
```

Then read the body once for what a validator cannot check: are the examples genuinely
distinct, does the gate line name commands that exist in the target repos, does the KB
table's right-hand column say enough to make the agent open the file.

## Auditing or migrating an existing agent

Start with `"${CLAUDE_PLUGIN_ROOT}/skills/agent-creator/scripts/validate_agent.py" --all`, then follow
`references/audit-checklist.md`. The short version: fix frontmatter, rewrite the
`description` with real examples, convert checklist blocks into `## Always` (rules) and
`## Workflow` (steps) while moving deep detail out to a KB file, add the standard sections,
wire the routing row, re-validate.

A migrated agent body should come out **shorter** than the original — detail belongs in the
KB, where it loads on demand rather than on every invocation.

Some agents are legitimately non-standard. `devops-engineer` substitutes
`## Operational Guidelines` for `## Always` and `## Response Format` for `## Workflow`,
because it is an operations agent rather than a code-writing one; the validator accepts
those equivalents. `## Knowledge Base` and `## Memory Discipline` have no substitutes.

## Notes

- `name` must equal the filename. When they disagree, renaming the **file** is safer than
  renaming the field — the field is what other agents' deferral lines reference.
- Only `devops-engineer` omits `tools` (inheriting everything including MCPs), and per
  `~/.claude/CLAUDE.md` it is the only agent permitted to use MCPs. Do not give a new agent
  MCP access without raising it explicitly.
- Never pre-create `~/.claude/agent-memory/<name>/`; it appears on first write.
