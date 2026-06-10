---
name: phase-plan-patch
description: Add patch/minor/major versioned changes to existing phases in a plan. Use when the user runs /phase-plan-patch <patch|minor|major> <phase-number> <description> or asks to amend, extend, or insert phases in an existing plan.
argument-hint: "<patch|minor|major> <phase-number> <description>"
disable-model-invocation: true # manual use only
---

Modify plan.md with versioned phase changes: $ARGUMENTS

## Version Types

### Patch (X.0.Y) - Small fix within a phase
Example: `/phase-plan-patch patch 2 fix typo in API endpoint`
- Adds phase 2.0.1, 2.0.2, etc.
- Does not affect other phases
- For bug fixes, small corrections

### Minor (X.Y.0) - Sub-step addition to a phase
Example: `/phase-plan-patch minor 2 add input validation`
- Adds phase 2.1.0, 2.2.0, etc.
- Does not affect other phases
- For additional features within the phase scope

### Major - Insert entire new phase
Example: `/phase-plan-patch major 2 add caching layer`
- Inserts new phase after phase 2 (becomes phase 3)
- Increments all subsequent phases by 1 (3→4, 4→5, etc.)
- For significant new work that needs its own phase

## Instructions

1. Read `docs-claude/plans/plan.md`
2. Parse the version type and target phase from arguments
3. Apply the appropriate change:
   - **Patch**: Add X.0.Y sub-section under phase X
   - **Minor**: Add X.Y.0 sub-section under phase X
   - **Major**: Insert new phase, renumber all following phases
4. Include the same structure (checkboxes, completion report template)
5. Save updated plan.md

---

## Usage

```
/phase-plan-patch patch 2 fix database connection string
/phase-plan-patch minor 3 add rate limiting to API
/phase-plan-patch major 2 implement caching layer between phases 2 and 3
```
