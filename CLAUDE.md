# Writing style - applies to every reply, file, commit, PR and ticket
- NEVER use the em-dash "—". Use a hyphen "-" instead (or a comma, or split the sentence). Scan your output for "—" before sending or writing it, and replace any you find.
- Full style directive (banned words, tone, sentence rhythm, response mechanics), loaded into every session:
@~/.claude/docs-claude/kb/shared/writing-style.md

# Agents - route the task to the right one
- ALWAYS delegate to sub-agents when possible. The root agent is an orchestrator: for almost every prompt it should only pick the agent(s), launch them (in parallel when the work is independent), and relay the result. Do the reading, searching, coding, and testing inside sub-agents so the root context window stays clean.
- Do the work in the root agent only for trivial lookups or when no agent fits.
- Sub-agents: if you discover a technique, gotcha, or convention the KB does not cover, end your report with a `KB suggestion` block. Target the KB directory of the agent that found it (`backend/`, `frontend/`, etc.), not `shared/`. Root agent: relay each one to the user and ask whether to add it. Protocol: `~/.claude/docs-claude/kb/shared/kb-capture.md`.

| Task | Agent |
|------|-------|
| Backend: Flask/FastAPI/Express, Python/Node, API routes | senior-backend-engineer |
| Frontend: React, Next.js, forms, React Query, shared UI packages | frontend-engineer |
| Mobile: Expo, React Native, gluestack-ui, NativeWind, EAS | react-native-engineer |
| LLM/AI: Anthropic/OpenAI APIs, prompts, RAG, embeddings, vector DBs | llm-coding-agent |
| Scheduled tasks: crons, workers, background/time-based jobs | scheduled-tasks-coder |
| Database: schema/index design, slow queries, migrations, PostgreSQL/MySQL/MongoDB/Redis | dba-administrator |
| Infra, deploy, GitHub, AWS/Render, sudo, MCP usage | devops-engineer |
| Debug and verify: iOS Simulator, browser (Claude in Chrome), UI bugs, console/network errors, after any change set or phase | debugger |

Reference: broad searches or "where does X live" across many files go to `Explore`. Anything the table doesn't cover goes to `general-purpose`. Never fall back to doing it in the root agent just because no row matches.

# Knowledge base - read before working, don't work from memory
- Standing conventions live in `~/.claude/docs-claude/kb/` (cross-project) and in each repo's own `docs-claude/kb/` (repo-specific). Start at the `README.md` of either for the index.
- Load the relevant file before that kind of work rather than reasoning from recall. Where a KB file and an assumption disagree, the file wins.
- Learned something durable? Update the KB file. A standing convention belongs there, not in agent memory. Memory is for discovered facts that may change.

# Debugging (debugger)
- `debugger` is the only agent that debugs or verifies runtime behavior (iOS Simulator, browser via Claude in Chrome, later backend routes via Swagger + curl). Implementation agents must not self-debug in a browser or simulator.
- Launch it after every change set and at the end of every phase (phase-execute included), passing a what-was-done summary: files changed, pages/routes/screens added, claims to check. It returns PASS / FAIL / BLOCKED with evidence and the likely file to fix; it never fixes. Route the fix to the owning implementation agent, then re-run `debugger`.
- Deliberate exception to the devops-only-MCP rule: `debugger` is granted a fixed allowlist of `mcp__claude-in-chrome__*` tools and no other MCPs. KB: `docs-claude/kb/debugger/`.

# Skills - per-module conventions
- A repo's `.claude/skills/` holds its module conventions. Load the matching skill (Skill tool) as soon as you know which files a task touches. Don't rediscover with Read/Grep. The project's CLAUDE.md routing table says which skill covers what.
- After a change that alters *how* a module works (new layer, changed contract, replaced library, a new rule others must follow), say the covering skill is now stale and offer to refresh it with `/project-skills-map`. Adding one more instance of an existing pattern is not a trigger; don't nag on routine changes.
- No `.claude/skills/` yet, or a new module/app just landed? Suggest `/project-skills-map` to survey the repo and author the missing skills.

# DevOps (devops-engineer)
- Only agent allowed to use MCPs; has sudo. Project devops info: `docs-claude/core/system-devops-admin.md`.
- GitHub: use `gh` CLI for everything (pushes, PRs, issues, releases, repos, API), e.g. `gh pr create`, `gh issue list`, `gh api`. Auth via `gh auth status`. Devops handles pushes.
- Python: have devops set up the venv with `uv sync` (apps share this server, so avoid clashes).
- Never pick ports yourself for Flask/FastAPI/Express. Consult devops.

# Planning
- Create every plan via the `/phase-plan:phase-plan` command. Never plan without it.
- Plans live at `docs-claude/plans/{NAME}.plan.md`. Don't print the plan to the console; just confirm it's done and reference the file.

# New Projects
- Scaffold every new project with the team template. Don't hand-roll package.json/folders:
  `pnpm create @two-steps-org/app <name> --apps <apps> --scope @<name> --no-git --yes`
- `<apps>`: comma-separated, chosen from `react`, `fastapi`, `flask`, `express`, `nextjs`. Pick per the project's actual stack.
- Replace `<name>` and `@<name>` with the real project name, e.g.:
  `pnpm create @two-steps-org/app cv-editor --apps fastapi,react --scope @cv-editor --no-git --yes`

# Keep these docs updated (concise, just enough for an LLM agent, to save tokens)
- Backend routes → `docs-claude/core/backend-routes.md` (update when adding routes).
- Web UI pages/templates → `docs-claude/core/webui-templates-index.md` (update when adding pages/templates).

# Conventions
- Never use a raw HTML element when the project's own `packages/ui` already has a component for it, e.g. use `@<scope>/ui/select` (`packages/ui/src/select.tsx`) instead of `<select>`, and `@<scope>/ui/button` (`packages/ui/src/button.tsx`) instead of `<button>`. Always check `packages/ui` first; if a matching component already exists in the project, use it instead of a native tag, a new one-off component, or a third-party component.
- MUST NOT add comments in code. Clean code principles: code must be self-explanatory through clear function/variable names and structure, not explained alongside it. This overrides any instinct to add a "why" comment for non-obvious rationale, e.g. never add a comment block justifying a test's assertion/query choice (such as explaining why `getAllByText` was used instead of `getByText`); express that through a descriptive name instead. Applies to inline comments, block comments, and docstrings alike.
- Prefix shell commands with `rtk` to save tokens (e.g. `rtk git status`); omit it when you need fuller output.
- Prefer CURL over writing test scripts; if you must write one, archive it when done.
- Every project needs a `render.yaml` per `~/.claude/docs-claude/kb/devops/render-yaml-standard.md`. Use the `projects:` format (`environments`, `runtime: docker`, `dockerfilePath`, `dockerContext`, `fromGroup`); never the flat `services:` format. See `~/.claude/docs-claude/kb/devops/render-yaml.md` for field docs.
