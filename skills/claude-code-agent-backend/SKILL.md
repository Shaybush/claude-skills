---
name: claude-code-agent-backend
description: Scaffold or extend a local-only backend that spawns the `claude` CLI as a child process to power an in-app AI agent feature, streaming its output to the frontend over SSE and running on the developer's own Claude subscription instead of metered API billing.
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash(git status:*)
  - Bash(curl:*)
  - Agent
  - AskUserQuestion
when_to_use: |
  Use when the user wants an AI-agent-powered feature that runs on their own Claude
  subscription/login rather than paying per-token API costs — i.e. the app itself should shell
  out to the `claude` CLI (Claude Code) as its agent engine, instead of calling the Anthropic API
  directly. Trigger phrases: "build an agent using my Claude subscription", "create an app with
  Claude Code" / "use Claude Code as the backend", "run claude / claude code headlessly or
  programmatically", "avoid API token costs, use my subscription instead", "spawn claude as a
  child process/subprocess", "add an AI chat/agent feature powered by Claude Code".
argument-hint: "<feature-name> [agent-task] [data-scope]"
arguments:
  - feature_name
  - agent_task
  - data_scope
---

# Claude Code Agent Backend

Add an AI-agent-powered feature to an app by spawning the `claude` CLI as a child process per
turn, instead of calling the Anthropic API directly. The point of this pattern is that the
subprocess rides the developer's own authenticated Claude Code login/subscription — no separate
API key or per-token billing. Its output streams to the frontend over SSE, and everything the
agent can touch is fenced to an isolated scratch workspace + a narrow tool allowlist, never a
live repo checkout.

**Reference implementation** (when this repo is available — a concrete worked example of every
step below, running for two separate features, `/api/chat` and `/api/tailor`):
`cv-editor/apps/express/src/{chat,tailor}/*` (backend) and `cv-editor/apps/react/src/cv/chat/api.ts`
(frontend consumer).

## Inputs
- `$feature_name`: short slug for the new agent feature — used as the route path segment,
  turn-lock key, and workspace subdirectory name (e.g. `chat`, `tailor`, `cover-letter`). Ask if
  not given.
- `$agent_task`: plain-language description of what the agent should do — becomes the core of
  its system prompt (e.g. "edit the CV's JSON data based on the user's chat instructions"). Ask
  if not given.
- `$data_scope`: exactly which file(s)/data in the target project the agent needs to read and/or
  edit. Drives both the isolated workspace contents (step 4) and the tool allowlist (step 1). Ask
  if not given.

## Goal
Ship a new Claude-Code-powered agent feature: a local-only backend endpoint that spawns `claude`
per turn and streams it to the frontend over SSE, added to an existing matching backend or a
freshly scaffolded one. Done when: the route exists and works end to end, a frontend consumer
streams its events into the UI, typecheck/lint/test pass for both sides, and the manual
verification + guard-rejection checks in step 8 have actually been run — not just implied by
reading the code.

## Steps

### 1. Scope the feature
Pin down `$feature_name`, `$agent_task`, and `$data_scope` (ask for whichever weren't given).
From `$data_scope`, derive the *narrowest* tool allowlist that accomplishes `$agent_task` (e.g.
`Read,Edit,Grep` for editing one known file; add `Write`/`Glob` only if the agent must create
files or search a wider tree).

**Success criteria**: feature_name, agent_task, data_scope, and the tool allowlist are all
written down before any code is touched.
**Human checkpoint**: confirm the tool allowlist and exactly which files/directories the agent
may touch — this is the actual scope of `--dangerously-skip-permissions`, get explicit sign-off
before proceeding.

### 2. Locate or scaffold the local backend
Search the target repo for an existing instance of this pattern (grep for a
`child_process`/`subprocess` call invoking `claude`, alongside a loopback/Host-header guard). If
found, treat it as the base to extend — skip to step 5, adding a new route alongside the
existing one(s) and reusing its subprocess engine, config, and guard rather than duplicating them.
If nothing is found, scaffold a new one via the team template — `pnpm create @two-steps-org/app
<name> --apps <fastapi|flask|express> --scope @<name> --no-git --yes` — picking the framework to
match the rest of the target project's stack (ask if ambiguous).

**Artifacts**: path to the backend service directory (existing or newly scaffolded); which case
applies (extend vs. scaffold).
**Execution**: Task agent (senior-backend-engineer).
**Human checkpoint**: confirm the detection result — "found nothing, about to scaffold a
brand-new service" — before running the scaffold command.
**Success criteria**: a concrete backend service directory exists on disk before any
Claude-CLI-specific code is written.

### 3. Build or reuse the subprocess engine
Port the `startTurn`-equivalent: build the `claude` CLI args (`--print --output-format
stream-json --include-partial-messages --verbose --dangerously-skip-permissions --tools
<allowlist> --strict-mcp-config --safe-mode --effort <effort> --append-system-prompt
<systemPrompt>`, plus optional `--model` and `--resume <sessionId>` for conversation continuity),
spawn it (no shell, piped stdio, args passed as an array — never interpolated into a command
string) with `cwd` pointed at the isolated workspace from step 4, parse stdout as
newline-delimited JSON (buffering partial lines), capture `session_id` off any event that carries
one, write the turn's message to stdin then close it. Handle: spawn errors; an external timeout
that sends SIGTERM then SIGKILL after a grace period; and an externally triggered abort (e.g.
client disconnect) via the same SIGTERM→SIGKILL path.

**Rules**: the subprocess is headless (`--print`, non-interactive) — there is no TTY to answer
permission prompts, so `--dangerously-skip-permissions` is mandatory here, not optional. Its
safety comes entirely from step 1 (narrow allowlist) and step 4 (isolated cwd), not from anything
in this step.
**Execution**: Task agent (senior-backend-engineer).
**Success criteria**: given a message and a cwd, the wrapper streams parsed JSON events, resolves
with exit code/signal/sessionId/stderr tail once the process closes, and reliably kills a hung
process at the configured timeout.

### 4. Build the isolated per-turn workspace
Before each turn, materialize a scratch directory unique to this conversation/resource (e.g.
`<workspacesDir>/<feature_name>/<resourceId>`) containing only the exact files named in
`$data_scope` (plus a JSON schema file alongside any structured file the agent must keep valid).
Never point the subprocess's `cwd` at the real project or repo checkout directly. After the turn
exits, re-read whatever the agent may have changed back off that scratch directory (step 6
validates/persists it).

**Rules (hard invariant)**: this isolation *is* the safety boundary for
`--dangerously-skip-permissions` — running the CLI directly against the live repo/data store
instead is not a shortcut, it's a different, unreviewed security posture.
**Execution**: Task agent (senior-backend-engineer).
**Success criteria**: the agent process can only ever reach files deliberately staged into the
scratch dir for that turn.

### 5. Wire the SSE route
Validate the incoming request body (schema library matching the target stack — zod for TS,
pydantic for FastAPI/Flask). Acquire a per-resource turn lock keyed on whatever uniquely
identifies the conversation/resource (409 if a turn is already running for that key — never allow
two concurrent turns against the same workspace). Open an SSE stream (`text/event-stream`,
`Cache-Control: no-cache, no-transform`, `Connection: keep-alive`, plus an unref'd/daemon
heartbeat so it can't keep the process alive on its own). Start the turn from step 3, mapping each
raw Claude stream-json event down to a small, stable frontend-facing event vocabulary (e.g. `text`
for content deltas, `tool` for tool-use start, a catch-all passthrough) rather than leaking the
CLI's full internal event shape to the client. Register a disconnect handler that aborts the turn
if the client goes away.

**Rules**: always release the turn lock in a `finally`, even on error.
**Execution**: Task agent (senior-backend-engineer).
**Success criteria**: a client POSTing to the new route receives a live stream of mapped events
ending in a terminal event, and a second concurrent request against the same resource gets a 409
instead of starting a second subprocess.

### 6. Resolve the turn outcome
After the subprocess closes, re-read the file(s) it may have touched from the scratch workspace,
validate them, and diff against the pre-turn state. Persist only when the turn ended cleanly (no
spawn error, no abort, no non-zero exit/signal) **and** the data changed **and** it's still valid
— on any failure, discard whatever the agent wrote rather than persisting a possibly-inconsistent
result, even if the file did change during the run. Surface ambiguous-but-not-fatal cases as
user-facing notices, not errors (e.g. "finished without producing an assistant message", "didn't
change anything", "changed the file but the turn didn't finish cleanly, so it wasn't saved").

**Execution**: Task agent (senior-backend-engineer).
**Success criteria**: a forced-failure turn (e.g. kill the process mid-turn) never corrupts
persisted state, and a clean successful turn does persist.

### 7. Wire the frontend consumer
Use `fetch(POST, ...)`, not `EventSource` (it's GET-only and this route takes a JSON body). Read
`response.body` as a stream, decode it, and manually parse SSE frames (`event:`/`data:` pairs
separated by blank lines). Dispatch a typed event union into UI state as frames arrive. Check the
project's own shared UI package for existing chat/message/button/input components before writing
new ones — never hand-roll something a shared package already provides.

**Execution**: Task agent (frontend-engineer).
**Success criteria**: sending a message in the UI shows streamed text arriving incrementally, not
just a final blob after the whole turn completes.

### 8. Verify end-to-end
Run the target stack's typecheck/lint/test commands for both the backend and frontend changes.
Manually exercise the new route (curl for a raw SSE sanity check, then the actual browser UI) to
confirm: events stream correctly, a second turn on the same resource resumes the session (if
applicable), and a deliberately slow/hung turn gets aborted at the configured timeout.

**Human checkpoint**: manually verify the loopback/Origin guard actually rejects a disallowed
request (e.g. curl with a non-`127.0.0.1` `Host` header, or a disallowed `Origin`) and gets a
403 — don't just trust that reading the guard's code implies it works.

**Deployment note (case-by-case, not this skill's default path)**: the default guard
(loopback-only) assumes purely local/dev use and must never be exposed as-is. If the user
explicitly wants this reachable beyond localhost (e.g. self-hosted on a VPS for remote/multi-device
use), that's a materially different security posture: hand off to devops-engineer (per this
user's CLAUDE.md routing table for infra/VPS/deploy work) to run the service on the VPS, put
nginx or Traefik in front for DNS/TLS, and add a real authentication/login layer — since the
subprocess still runs under that VPS's own `claude` login and network topology no longer
guarantees only the trusted operator can reach it. Never deploy this service to a publicly
reachable host relying on the loopback guard alone.

**Success criteria**: typecheck/lint/test all pass, the manual streaming/resume/timeout checks
pass, and the guard's rejection behavior was actually exercised, not just read.
