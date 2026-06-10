# Agents — route the task to the right one
| Task | Agent |
|------|-------|
| Backend: Flask/FastAPI/Express, Python/Node, API routes | senior-backend-engineer |
| Frontend: React, Next.js, forms, React Query, shared UI packages | frontend-engineer |
| LLM/AI: Anthropic/OpenAI APIs, prompts, RAG, embeddings, vector DBs | llm-coding-agent |
| Scheduled tasks: crons, workers, background/time-based jobs | scheduled-tasks-coder |
| Infra, deploy, GitHub, AWS/Render, sudo, MCP usage | devops-engineer |

# DevOps (devops-engineer)
- Only agent allowed to use MCPs; has sudo. Project devops info: `docs-claude/core/system-devops-admin.md`.
- GitHub: SSH key (SHA256) is already configured — devops handles pushes.
- Python: have devops set up the venv with `uv sync` (apps share this server — avoid clashes).
- Never pick ports yourself for Flask/FastAPI/Express — consult devops.

# Planning
- Create every plan via the `/phase-plan` command — never plan without it.
- Plans live at `docs-claude/plans/{NAME}.plan.md`. Don't print the plan to the console; just confirm it's done and reference the file.

# Keep these docs updated (concise — just enough for an LLM agent, to save tokens)
- Backend routes → `docs-claude/core/backend-routes.md` (update when adding routes).
- Web UI pages/templates → `docs-claude/core/webui-templates-index.md` (update when adding pages/templates).

# Conventions
- Prefix shell commands with `rtk` to save tokens (e.g. `rtk git status`); omit it when you need fuller output.
- Prefer CURL over writing test scripts; if you must write one, archive it when done.
- Every project needs a `render.yaml` per `~/.claude/kb/render-yaml-standard.md` — use the `projects:` format (`environments`, `runtime: docker`, `dockerfilePath`, `dockerContext`, `fromGroup`); never the flat `services:` format. See `~/.claude/kb/render-yaml.md` for field docs.
