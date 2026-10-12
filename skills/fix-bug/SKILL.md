---
name: fix-bug
description: This skill should be used when the user reports a bug — via a Jira ticket number or a plain-language description — and wants it fixed end-to-end with recorded proof. It creates a ticket-named worktree, records the bug reproducing live via Playwright in Docker ("before"), locates and fixes the root cause (delegating to the stack-specific agent per the routing table), re-records the same repro now passing ("after"), then opens a GitHub PR with both videos attached via gh's --attach flag (GA in gh v2.99.0+).
---

# Fix Bug — Reproduce, Fix, Verify, Ship

End-to-end bug pipeline: turn a ticket number or a plain description into a reviewed PR that carries its own video proof — the bug reproducing, then the same steps passing after the fix — attached directly via `gh pr create --attach`.

## Step 0 — Resolve what's broken

- **Ticket number given** (e.g. `DT-123`): have `devops-engineer` fetch the issue's summary/description/repro steps via the Jira MCP tools (`mcp__atlassian__getJiraIssue` etc.) — per this project's convention, only `devops-engineer` calls MCP tools directly.
- **Plain description given, no ticket**: per the house worktree-naming rule, a worktree branch must be named after a Jira ticket number, and must be asked for if unclear — stop and ask for the ticket number before creating anything. Don't invent one.
- Preflight: `gh --version` ≥ 2.99.0 (upgrade via `brew upgrade gh` if older — `--attach` needs it), `docker info` succeeds, `gh auth status` shows an authenticated account with push access.

The `scripts/…` and `references/…` paths below are relative to `${CLAUDE_PLUGIN_ROOT}/skills/fix-bug/`.

## Step 1 — Pick the owner and enter a worktree

Match the bug to this project's agent-routing table (frontend-engineer / senior-backend-engineer / react-native-engineer / llm-coding-agent / scheduled-tasks-coder). Ask the user if the affected app/stack genuinely isn't clear from the description.

- Already are that specialist? Continue directly with Steps 2–5 yourself.
- Otherwise, delegate Steps 2–5 as one task to that agent. It's a fresh agent with no context, so its prompt must include the full bug description/repro steps and ticket number — and since not every agent has this skill loaded (e.g. `senior-backend-engineer` has no `Skill` tool), include the literal path to `${CLAUDE_PLUGIN_ROOT}/skills/fix-bug/scripts/playwright-docker-run.sh` — resolved to an absolute path, since the delegated agent does not inherit `CLAUDE_PLUGIN_ROOT` in its prompt — and how to call it, not just "use the fix-bug skill."

First action, by whoever does the work: `EnterWorktree({name: "<TICKET-NUMBER>"})` — never a random or auto-generated branch name. Install dependencies once right after entering; both captures below reuse this same worktree.

## Step 2 — Record "before" (bug still live, nothing fixed yet)

Recording first, before touching any code, guarantees the video reflects the actually-reported bug rather than some already-half-fixed state.

Write or locate a Playwright spec for the reported repro with a real assertion (e.g. an element's bounding box actually fits its container — not just "didn't crash"). Scope both video and base URL to just this spec file, rather than editing the shared `playwright.config.ts`:

```ts
test.use({ baseURL: process.env.BASE_URL, video: 'on' });
```

Start the worktree's dev server, then run the capture with this skill's script:

```bash
SPEC=<testDir>/bug-<ticket>.spec.ts PORT=<port> OUTPUT_DIR=$(mktemp -d -t fix-bug-before) \
  "${CLAUDE_PLUGIN_ROOT}/skills/fix-bug/scripts/playwright-docker-run.sh"
```

See `references/docker-playwright-networking.md` for reaching the host dev server from the container (`host.docker.internal`, Vite's `allowedHosts`, CORS). This run is expected to **fail** — that's confirmation the spec actually captures the reported bug. If it unexpectedly passes, the repro is wrong; fix the spec, not the app, before continuing. Copy the resulting `*.webm` out as `before.webm`.

## Step 3 — Locate and fix

Find the root cause and implement the fix in the worktree, same as any other bug fix.

## Step 4 — Record "after" + gate

Re-run the identical spec via the identical script (fresh `OUTPUT_DIR`) against the now-fixed dev server. This run **must pass** — it's the actual proof, not a formality. If it still fails, keep iterating on the fix; do not move on to Step 5 with a failing run. Copy the result out as `after.webm`.

## Step 5 — Commit

Stage only the real changes by name — the fix, the new/updated spec file — never `git add -A`/`.` (a stray temporary Vite `allowedHosts` edit, if one was needed for Step 2's networking, should never get staged; revert it if you made one). Commit on the ticket branch.

Call `ExitWorktree({action: "keep"})` before reporting back if you're the delegated specialist finishing here — the worktree and branch stay on disk for devops-engineer to pick up in Step 6.

## Step 6 — Ship: push + open the PR with attachments

Delegate to `devops-engineer` — GitHub operations and pushes are its job:

- `EnterWorktree({path: "<worktree-path>"})` to join the same worktree
- `git push -u origin <ticket-branch>`
- ```bash
  gh pr create \
    --title "<TICKET>: <short summary>" \
    --body "Fixes <TICKET>.

  ## Root cause
  <...>

  ## Verification
  Automated Playwright regression test, run in Docker — before/after attached." \
    --attach ./before.webm \
    --attach ./after.webm
  ```
- Report the PR URL back.

See `references/gh-attach-reference.md` for exact limits/syntax (video has no alt-text, size caps, etc.).

## Step 7 — Clean up

Keep the worktree — it's live work tied to an open PR, not disposable. Delete the local `before.webm`/`after.webm` copies once the PR upload succeeds — they're attach-only artifacts, never committed to git.

## Important notes

- This skill fixes the bug — it isn't a pure verification step. If the fix already exists and only needs verifying/attaching to an existing PR, just run Steps 2 and 4 directly against the current working tree (no second worktree needed) and use `gh pr comment --attach` instead of `gh pr create --attach`.
- Non-UI bugs (pure API/backend): Playwright's `request` fixture can still capture a meaningful before/after without a browser (hit the endpoint, capture the response) — a browser video isn't the only valid proof.
- `--attach` also works on `gh issue create/edit/comment` and `gh pr edit/comment`, not just `pr create`.
- Video formats: MP4/MOV/WebM (Playwright's own `.webm` output needs no conversion). Images: PNG/JPEG/GIF/WebP/SVG.
- github.com only as of this writing — GitHub Enterprise Server isn't supported yet.
