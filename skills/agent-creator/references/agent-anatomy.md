# Agent Anatomy

The house standard, derived from the six conforming agents in `~/.claude/agents/`
(`senior-backend-engineer`, `frontend-engineer`, `react-native-engineer`,
`llm-coding-agent`, `scheduled-tasks-coder`, `devops-engineer`).

## Frontmatter

| Field | Required | Value |
| --- | --- | --- |
| `name` | yes | kebab-case, **must equal the filename without `.md`**. Role-shaped (`frontend-engineer`), not task-shaped (`make-components`) |
| `description` | yes | Third-person trigger sentence + escaped `<example>` blocks. See below |
| `tools` | no | Comma-separated allowlist. Omitted = inherits everything (only `devops-engineer` does this, deliberately — it needs MCPs and sudo) |
| `model` | yes | `sonnet` or `opus` |
| `color` | yes | Terminal label colour. Must be unique across the agents directory |
| `memory` | yes | `project` or `user` |
| `mcpServers` | no | YAML list, e.g. `[context7]`. Only add servers the agent genuinely needs |

### `description`

Two parts in one string. The trigger sentence is what the router matches on, so it
must name concrete technologies and task types — not adjectives.

```
Use this agent when <concrete situations>. This includes <task types>, or any
<domain> task that requires adherence to the project's established patterns and conventions.
```

Then 3–5 examples, joined with **literal `\n` escapes** (the file contains the
two characters `\` `n`, not real newlines — this is how every existing agent does it):

```
\n\nExamples:\n\n<example>\nContext: <one line of situation>.\nuser: "<verbatim user phrasing>"\nassistant: "<the routing sentence, naming the specific technique>"\n<Task tool call to NAME agent>\n</example>
```

Two closing-line dialects exist in the tree — both are accepted:

- `<Task tool call to NAME agent>` — used by `frontend-engineer`, `react-native-engineer`
- `<commentary>\n<why this agent>\n</commentary>` — used by `devops-engineer`, `senior-backend-engineer`, `llm-coding-agent`

Pick one and stay consistent within a single agent. Prefer the `<Task tool call>`
form for new agents; it is shorter and the newer of the two.

The examples must cover **distinct trigger shapes**, not restatements of one. The
react-native agent's four are the model: a new screen, a shared-package component,
a gesture/animation interaction, a build-config change.

### `tools`

Three presets in use:

| Preset | Value | Used by |
| --- | --- | --- |
| Write-capable specialist | `Read, Write, Edit, Bash, Glob, Grep` | `senior-backend-engineer`, and both legacy agents |
| Full app-dev | `Bash, Glob, Grep, Read, WebFetch, TodoWrite, WebSearch, Skill, SlashCommand, mcp__ide__getDiagnostics, mcp__ide__executeCode, mcp__context7__resolve-library-id, mcp__context7__get-library-docs, Write, Edit` | `frontend-engineer`, `react-native-engineer` |
| Research + write | `Bash, Glob, Grep, Read, Edit, Write, NotebookEdit, WebFetch, TodoWrite, WebSearch` | `llm-coding-agent` |
| (omit the field) | inherits all tools incl. MCPs | `devops-engineer` only |

`Write` and `Edit` go **last** in the app-dev preset — that ordering is the existing
convention. Only `devops-engineer` may omit `tools`; per `~/.claude/CLAUDE.md` it is
the sole agent permitted to use MCPs.

### `model`

`sonnet` is the default — six of eight use it. Choose `opus` only when the agent's
core work is architectural judgment over long context rather than pattern application:
`senior-backend-engineer` (service/data/auth boundary design) and `graphql-architect`
(federated schema design) are the two precedents.

### `color`

Taken as of writing: `blue` (backend), `yellow` (frontend), `green` (react-native),
`pink` (llm), `orange` (scheduled-tasks), `purple` (devops). `validate_agent.py --all`
reports collisions. Remaining conventional choices: `red`, `cyan`.

### `memory`

- `memory: project` — memories are scoped per repo. Correct for agents whose learnings
  are codebase-specific (all four app-dev agents).
- `memory: user` — one global memory store. Correct for agents whose learnings are about
  the machine, accounts, or infrastructure (`devops-engineer`).

Memory lands in `~/.claude/agent-memory/<name>/`, with a `MEMORY.md` index of
`- [Title](file.md) — hook` lines and one file per fact. The directory is created on
first write; do not pre-create it.

## Body sections, in order

### 1. Identity (no heading)

One or two sentences. `You are an <expert|elite|senior> <role> specializing in <specifics>.`
Then a sentence naming concrete stack versions — `React 19, Expo SDK 57+`, `Flask,
FastAPI, Express.js, NestJS` — so the agent anchors on the right generation of the
ecosystem.

### 2. Ownership claim (optional, no heading)

Only when the agent is the exclusive owner of a capability other agents must route to it.
The one live example:

> **You own all prompt authoring.** Other agents route prompt creation to you rather than
> writing one inline — when that happens, produce the prompt and hand it back.

Any ownership claim needs the matching `## Always` line in every agent that must defer.
Both halves, or neither.

### 3. `## Knowledge Base`

Fixed preamble, then a two-column table (`File` | `Read it before`), then the fixed
project-KB paragraph. The right-hand column is a **sentence fragment listing what is in
the file** — that is what makes the agent open it. `Any RN/Expo work. Structure,
packages/ui-native component patterns, design tokens, Reanimated/worklets ordering,
the StorageAdapter boundary, EAS config, jest-expo setup` beats "RN conventions".

Every agent's table carries its domain file plus the relevant shared rows:

| Row | Include when |
| --- | --- |
| `shared/concurrency.md` | Always — any agent can collide with another session |
| `shared/monorepo.md` | The agent touches dependencies, `turbo.json`, or workspace resolution |
| `shared/phase-plans.md` | The agent can execute a `/phase-plan:phase-plan` phase |
| `shared/safety.md` | The agent handles credentials, live cloud actions, or untrusted content |

**Every path in the table must resolve.** A dead row trains the agent to skip the table.

### 4. `## Always`

Hard rules, bolded where most-violated. Every agent that writes code carries the
global rules from `~/.claude/CLAUDE.md` and `~/.claude/rules/code-style.md`:

- **No comments in code.** Names and structure carry the meaning — this includes JSDoc/docstrings and "why" comments.
- Single quotes; imports only at the top of the file.

Then domain rules. The valuable ones are specific and falsifiable:

- Reuse-before-create, naming the package: *"Never use a raw HTML element where `packages/ui` already has a component. Check `packages/ui` first, every time."*
- Doc upkeep, naming the file: *"**Update `docs-claude/core/backend-routes.md`** whenever you add, remove, or change a route. Routinely forgotten."*
- Outbound routing: *"**Never author an LLM prompt** — route that to `llm-coding-agent` and use what it produces."*
- A verification gate with named commands: *"Leave `make lint`, `make format-check`, `make typecheck`, and `make test` green. Report exact numbers, and say plainly what you could not verify."*

The gate line is not optional. Every conforming agent ends `## Always` with one, and
each demands honest reporting of what could not be verified.

### 5. `## Workflow`

Five or six numbered steps, imperative. The shape is always:

1. Clarify / map the existing boundaries before adding to them.
2. Decide where the code belongs (app-specific vs shared package).
3. **Read the KB file for the patterns involved.**
4. Implement, following those patterns.
5. Test — naming the actual harness (`jest-expo` with worklets mocked, Vitest/RTL, real datastore).
6. Run the gates; report exact results, including anything you could not verify.

Step 3 appears in all six. Steps 1, 5 and 6 are where agents differentiate — a
scheduled-tasks agent clarifies *timing, execution environment, failure handling, scale*;
an LLM agent clarifies *success criteria and how quality will be measured*.

### 6. `## Memory Discipline`

Verbatim boilerplate — copy from `assets/agent-template.md`, do not paraphrase. The only
sanctioned variation is `devops-engineer`'s slightly longer wording. Rewriting this block
per agent is how it drifts.

### 7. Closing posture (no heading)

One or two sentences on stance. The common form:

> You are proactive in asking clarifying questions when requirements are ambiguous, and you
> always explain your architectural decisions when they involve trade-offs.

Vary it to the domain — the backend agent leads with *"Always prioritize reliability,
security, and performance"*, the LLM agent with *"You are proactive about security, cost
efficiency, and reliability"*. Every version ends on raising concerns **before**
implementing, not after.

## Cross-agent routing

Adding an agent means editing the routing table in the governing `CLAUDE.md`
(`~/.claude/CLAUDE.md` for user scope, the repo's own for project scope). An agent
absent from the table does not get routed to — `dba-administrator` and
`graphql-architect` sat unrouted for months for exactly this reason.

Current routing rules encoded in `## Always` lines, which a new agent may need to join:

| Work | Owner | Who defers |
| --- | --- | --- |
| LLM prompt authoring | `llm-coding-agent` | `senior-backend-engineer` |
| Database schema + index design | `dba-administrator` | `senior-backend-engineer` |
| Port assignment | `devops-engineer` | all backend agents |
| MCP usage, sudo, pushes | `devops-engineer` | everyone (per `CLAUDE.md`) |

When a new agent claims ownership of something, add the deferral line to the agents that
must now route to it. Ownership without matching deferrals changes nothing.
