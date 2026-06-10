---
name: phase-execute
description: Run a specific numbered phase of a plan from docs-claude/plans/. Use when the user runs /phase-execute <phase-number> [plan-file] or asks to execute or run a phase of a plan. Tracks todos, updates execution status, and runs a mandatory code-simplifier pass at the end.
argument-hint: "<phase-number> [plan-file]"
disable-model-invocation: true # manual use only
---

Execute Phase $1:

## Target Plan (optional)

- `$2` (optional): the plan file to load from `docs-claude/plans/`.
  - Accepts a bare name (`DT-555`) or a full filename (`DT-555.plan.md`) — resolve to the matching `*.plan.md` under `docs-claude/plans/`.
  - If omitted, fall back to the single active plan under `docs-claude/plans/` (the `*.plan.md` without a date suffix).
  - Load it first and treat it as the source of truth for this phase.

## Phase Execution

- **Update execution status → IN-PROGRESS** (do this first, before any work): in `docs-claude/plans/commands-execution.md` (the file `/phase-plan` creates; header `TODO command | STATUS`; status lifecycle `NOT STARTED` → `IN-PROGRESS` → `DONE`), find the line for this run and set its STATUS to `IN-PROGRESS`. Match the line whose command is `/phase-execute $1 <name>` — or a `/phase-execute-parallel ...` line that includes phase $1 — for the resolved `<name>` (`$2` if given, otherwise the active plan's filename stem). If the file or a matching line is missing, skip this step (never create entries here — `/phase-plan` owns them).
- Date: today
- Create todo checklist for this phase
- Subagents: assign yourselves to tasks
- Mark tasks as you complete them
- At end: note any issues/blockers for next phase
- Check if there are steps which already implemented, based on it if needed
- Always insert author and date which specify which subagents were assigned to different phases
- If you are further than phase 1, assume you completed all the previous phases and you have all the information you need in the target plan file under docs-claude/plans/ folder
- Don't add any plan accomplish to docs-claude/plans/ since everything is in the target plan file.

## Post-Phase Steps (after phase work is done)

1. **MANDATORY: Run code-simplifier agent** on ALL changes made during this phase
   - Use Task tool with "/simplify" command
   - Focus on every file modified/created during this phase
   - Do NOT skip this step

2. **If this is the LAST phase of the plan**, rename the plan file to mark it as completed:
   - Detect the active plan file under `docs-claude/plans/` (the one being executed)
   - Confirm there are no further phases after the one just completed
   - Get today's date in `dd-mm-yyyy` format (dashes are used because `/` is a path separator and cannot appear in filenames; date order matches `dd/mm/yyyy`)
   - Rename the file by inserting `_<dd-mm-yyyy>` before `.plan.md`
     - Example: `DT-555.plan.md` → `DT-555_18-05-2026.plan.md`
     - Example: `i18n.plan.md` → `i18n_18-05-2026.plan.md`
   - Use `git mv` if the file is tracked, otherwise `mv`
   - Do NOT rename if the filename already contains a date suffix (idempotent)

3. **Update execution status → DONE** (do this last): in `docs-claude/plans/commands-execution.md`, set the STATUS of the same line you set to `IN-PROGRESS` (the `/phase-execute $1 <name>` line) to `DONE` — after the phase work and the steps above have succeeded. If the file or line is missing, skip.

---

## Usage

```
/phase-execute 1               # Execute phase 1 of the active plan, code-simplifier at end
/phase-execute 2               # Execute phase 2 of the active plan, code-simplifier at end
/phase-execute 1 DT-555        # Execute phase 1 of docs-claude/plans/DT-555.plan.md
/phase-execute 2 i18n.plan.md  # Execute phase 2 of docs-claude/plans/i18n.plan.md
```
