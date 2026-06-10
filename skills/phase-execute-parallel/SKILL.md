---
name: phase-execute-parallel
description: Run multiple project phases in parallel. Use when the user runs /phase-execute-parallel <phase-numbers> [plan-file] or asks to execute several plan phases at once. Launches each phase as a parallel subagent, then runs a mandatory code-simplifier pass.
argument-hint: "<phase-numbers> [plan-file]"
disable-model-invocation: true # manual use only
---

Execute Phases $1 in parallel:

## Target Plan (optional)

- `$2` (optional): the plan file to load from `docs-claude/plans/`.
  - Accepts a bare name (`DT-555`) or a full filename (`DT-555.plan.md`) — resolve to the matching `*.plan.md` under `docs-claude/plans/`.
  - If omitted, fall back to the single active plan under `docs-claude/plans/` (the `*.plan.md` without a date suffix).
  - Load it first and treat it as the source of truth for all phases.

## Phase Execution

- **Update execution status → IN-PROGRESS** (do this first, before any work): in `docs-claude/plans/commands-execution.md` (the file `/phase-plan` creates; header `TODO command | STATUS`; status lifecycle `NOT STARTED` → `IN-PROGRESS` → `DONE`), find the line for this run and set its STATUS to `IN-PROGRESS`. Match the `/phase-execute-parallel $1 <name>` line for the resolved `<name>` (`$2` if given, otherwise the active plan's filename stem); if the phases were instead registered on separate `/phase-execute <phase> <name>` lines, mark each of them. If the file or a matching line is missing, skip this step (never create entries here — `/phase-plan` owns them).
- Date: today
- Parse the comma-separated phase numbers (e.g. "1,2" or "1,2,3")
- Create todo checklist for ALL phases
- Launch each phase as a separate subagent running in parallel
- Subagents: assign yourselves to tasks
- Mark tasks as you complete them
- At end: note any issues/blockers for next phase
- Check if there are steps which already implemented, based on it if needed
- Always insert author and date which specify which subagents were assigned to different phases
- If you are further than phase 1, assume you completed all the previous phases and you have all the information you need in the target plan file under docs-claude/plans/ folder
- Don't add any plan accomplish to docs-claude/plans/ since everything is in the target plan file.

## Post-Phase Steps (after ALL parallel phases are done)

1. **MANDATORY: Run code-simplifier agent** on ALL changes made during these phases
   - Use Task tool with subagent_type='code-simplifier:code-simplifier'
   - Focus on every file modified/created during these phases
   - Do NOT skip this step

2. **If the LAST phase of the plan is among the phases just executed**, rename the plan file to mark it as completed:
   - Detect the active plan file under `docs-claude/plans/` (the one being executed)
   - Confirm there are no further phases after the highest-numbered phase just completed
   - Get today's date in `dd-mm-yyyy` format (dashes are used because `/` is a path separator and cannot appear in filenames; date order matches `dd/mm/yyyy`)
   - Rename the file by inserting `_<dd-mm-yyyy>` before `.plan.md`
     - Example: `DT-555.plan.md` → `DT-555_18-05-2026.plan.md`
     - Example: `i18n.plan.md` → `i18n_18-05-2026.plan.md`
   - Use `git mv` if the file is tracked, otherwise `mv`
   - Do NOT rename if the filename already contains a date suffix (idempotent)

3. **Update execution status → DONE** (do this last): in `docs-claude/plans/commands-execution.md`, set the STATUS of the same line(s) you set to `IN-PROGRESS` to `DONE` — after all parallel phases and the steps above have succeeded. If the file or line is missing, skip.

---

## Usage

```
/phase-execute-parallel 1,2          # Execute phases 1 and 2 of the active plan in parallel
/phase-execute-parallel 1,2,3        # Execute phases 1, 2, and 3 of the active plan in parallel
/phase-execute-parallel 1,2 DT-555   # Execute phases 1 and 2 of docs-claude/plans/DT-555.plan.md
```
