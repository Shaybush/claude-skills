---
name: phase-plan
description: Create a phased implementation plan for a task, saved to docs-claude/plans/. Use when the user runs /phase-plan <task description> or asks to plan a task in phases. Runs a mandatory interactive sanity-questions loop before writing the plan, then registers per-phase execution commands.
argument-hint: "<task description>"
disable-model-invocation: true # manual use only
---

**Task:** $ARGUMENTS

---

Create a phased implementation plan in `docs-claude/plans/plan.md` for the task above.

## Plan Structure Requirements

### 1. Phases with Todo Checkboxes

Break down into logical phases, each with checkboxes so devs can mark progress:

```markdown
### Phase X: [Phase Name]

**Assigned to**: [subagent name(s)]
**Date Started**:
**Status**: [ ] Not Started | [ ] In Progress | [ ] Completed

- [ ] Task 1
- [ ] Task 2
- [ ] Task 3
```

### 2. Implementation Questionnaire (at end of each phase)

Devs fill this in so project managers can track what was done:

```markdown
#### Phase X Completion Report

| Question                                 | Response |
| ---------------------------------------- | -------- |
| What was implemented?                    |          |
| Were there any deviations from the plan? |          |
| Issues/blockers encountered?             |          |
| How were issues resolved?                |          |
| Any technical debt introduced?           |          |
| Recommendations for next phase?          |          |

**Completed by**: [subagent name]
**Date Completed**:
```

### 3. Optional Info for Other Phases

Include relevant info that other phases may need:

```markdown
#### Notes for Future Phases

- **Config changes**: [env vars, settings]
- **New dependencies**: [packages, services]
- **API changes**: [endpoints added/modified]
- **Database changes**: [migrations, schema]
- **Documentation updates needed**:
```

## Important:

- ask sanity questions to deep understanding what the job are.

## Sanity Questions Loop (MANDATORY before writing the plan)

The sanity questions are an **interactive loop**, not a one-shot. Do NOT write the plan until the loop ends.

1. Ask a numbered list of sanity questions (1, 2, 3, ...).
2. Wait for the user's answers.
3. Parse each numbered answer. Each answer may be one of:
   - A direct choice/answer (e.g. `1 - B`)
   - A choice with a modification (e.g. `2 - C but add alignment to right support`)
   - A counter-question from the user (e.g. `3 - what does it mean?`)
   - A mix of the above in the same response
4. For each counter-question from the user:
   - Answer it clearly and concisely.
   - If your answer surfaces new ambiguity, add new sanity questions to the next round.
5. Restate the **remaining open questions** (the ones the user asked back about, plus any new ones you generated). Re-number them starting from 1 for the new round to keep things clean.
6. Repeat steps 2–5 until the user has answered everything with no counter-questions and you have no new questions.
7. Only after the loop is fully resolved, summarize all decisions and write the plan to `docs-claude/plans/<name>.plan.md`, then register the execution commands (see **After Writing the Plan: Register Execution Commands** below).

### Example loop turn

User answers:
```
1 - B
2 - C but add alignment to right support
3 - what does it mean?
```

You should:
- Record `1 = B` and `2 = C + right-alignment support` as resolved.
- Answer question 3 (explain what it means).
- Ask a new round only with the still-open items, e.g.:
  ```
  Still need to confirm:
  1. (was 3) Given the explanation above, which option do you prefer — A or B?
  2. (new) Should X also apply to Y?
  ```

Never proceed to plan writing while any question is unresolved.

## After Writing the Plan: Register Execution Commands

After the plan `docs-claude/plans/<name>.plan.md` is written, register one execution command per phase in `docs-claude/plans/commands-execution.md` so another agent can run them in order.

- **File**: `docs-claude/plans/commands-execution.md`
- **If it does not exist**: create it with this header as the first line:
  ```
  TODO command | STATUS
  ```
- **If it already exists**: only append the new lines at the end. Never overwrite, reorder, or change existing entries.
- **One line per phase, in phase order.** `<name>` is the plan filename stem (without `.plan.md`) — the same value passed as the optional plan argument to `/phase-execute`.

Line format:
```
claude --dangerously-skip-permissions --effort max "/phase-execute <phase> <name>" | NOT STARTED
```

- Sequential phases → one `/phase-execute <N> <name>` line each.
- Phases that are independent and may run together → group into a single `/phase-execute-parallel <a,b,...> <name>` line.
- New entries always start with status `NOT STARTED`. The executing agent updates STATUS (`NOT STARTED` → `IN-PROGRESS` → `DONE`).

### Example (plan `i18n-multilang`, 4 phases where 3 & 4 run in parallel)
```
TODO command | STATUS
claude --dangerously-skip-permissions --effort max "/phase-execute 1 i18n-multilang" | NOT STARTED
claude --dangerously-skip-permissions --effort max "/phase-execute 2 i18n-multilang" | NOT STARTED
claude --dangerously-skip-permissions --effort max "/phase-execute-parallel 3,4 i18n-multilang" | NOT STARTED
```

## Usage

```
/phase-plan create refresh token logic in the backend side
/phase-plan add user authentication with JWT
/phase-plan implement payment gateway integration
```
