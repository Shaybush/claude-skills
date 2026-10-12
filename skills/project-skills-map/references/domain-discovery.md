# Domain Discovery

How to get from a directory listing to a defensible list of skills.

## Contents

- [Reading the inventory](#reading-the-inventory)
- [The signals that matter](#the-signals-that-matter)
- [Clustering rules](#clustering-rules)
- [Candidate domains by stack](#candidate-domains-by-stack)
- [Cross-cutting domains](#cross-cutting-domains)
- [Worked example](#worked-example)
- [Naming](#naming)
- [Scaling to massive repos](#scaling-to-massive-repos)

## Reading the inventory

`scripts/inventory.sh` prints, in order: workspace manifests, language mix, source counts at depth
1/2/3, **churn**, existing skills, context docs, manifest state.

Read it in this order:

1. **Manifests** tell you how many independent units exist. `pnpm-workspace.yaml` + `turbo.json` means
   a monorepo — expect skills per app *and* per shared package. A lone `pyproject.toml` means one unit,
   so domains will be internal layers instead.
2. **Language mix** tells you how many worlds you are in. A repo that is 383 `.tsx` + 286 `.py` has
   two convention systems that must not be described by one skill.
3. **Depth-3 counts** are your candidate list.
4. **Churn** ranks it. This is the single most valuable column.

## The signals that matter

**Churn over size.** A 400-file directory nobody has touched in six months does not need a skill; a
30-file directory in every third commit does. Churn is evidence that agents will be sent here.

**Sibling-file repetition.** When a directory holds `x.hooks.ts` / `x.keys.ts` / `x.types.ts` repeated
per domain, that trio *is* the convention — a very strong skill signal. Same for
`<name>_routes.py` + `<name>_service.py` + `<name>_repository.py`.

**Naming discipline.** Consistent naming across many files means a rule exists that nobody wrote down.

**Depth of the answer.** If doing the task correctly requires touching 4+ files in 3+ directories
(add a page → route + menu + permission + i18n + inventory doc), that is a skill. One-file tasks
rarely are.

**Deliberate weirdness.** Anything that made you say "huh, that's not how you'd normally do it" is the
highest-value content a skill can carry. Hunt for it.

Cheap probes before committing to a domain:

```bash
ls apps/web/api/*/                      # is the sibling-trio real?
git log --oneline -15 -- apps/server/services/
grep -rl "useQuery" apps/web/api | head # how many instances of the pattern?
```

## Clustering rules

**Merge when** files are layers of one task (route → service → repository), when two candidates would
always be loaded together, or when one is unusably thin alone.

**Split when** the same word means two different systems (web i18n vs. server i18n), when one skill
would exceed ~500 lines, or when two audiences never overlap (component authors vs. page builders).

**Prefer the workflow boundary over the directory boundary.** Some of the best skills map to no single
directory at all — "changing DB data safely", "granting a role access to a page". If a task is
recurring, dangerous, and cross-cutting, it deserves a skill even though `inventory.sh` never printed
it as a row. These are the ones a directory-walker misses, so ask explicitly: *what does this team do
repeatedly that spans folders?*

## Candidate domains by stack

Starting points, not a checklist. Keep only what passes the four tests in SKILL.md.

**Next.js / React app** — routing & pages (`app/`), client data layer (React Query hooks), forms
(RHF + zod), shared component library, state/store, i18n.
Watch for: whether `api/` is route handlers or a client layer over a separate backend — getting this
wrong is the classic failure.

**Flask / FastAPI / Express** — endpoints (route→service→repository), models & migrations, auth
guards, background jobs, testing, error/response envelope.
Watch for: the response-envelope and pagination contract; agents invent their own otherwise.

**Monorepo** — one skill per app, plus one per *shared* package that others import. Skip
`eslint-config`/`typescript-config` unless they are unusually custom. A `packages/ui` consumed
everywhere almost always earns one.

**React Native / Expo** — screens & navigation, native UI package, animations/gestures, EAS build
config, storage/permissions.

**Google Apps Script** — `appsscript.json` scopes & triggers, clasp push/deploy flow, container-bound
vs. standalone, quota and execution-time limits, `PropertiesService` conventions.

**Data / ML** — pipeline stages, feature definitions, experiment tracking, notebook→module promotion.

**Infra** — IaC layout, environment promotion, secrets, deploy runbook.

## Cross-cutting domains

Almost never visible as a directory, almost always worth a skill:

- **Data mutation safety** — seeding, backfills, one-off fixes; the dev-vs-prod guard.
- **Authorization** — where the ability lives and every place that mirrors it.
- **Observability** — the logging/tracing shape everything must follow.
- **Release** — versioning, changelog, deploy gate.

## Worked example

A Turborepo with Next.js web + Flask server + shared UI, ~1000 source files. Depth-3 and churn gave:

```
 175 apps/web/components      179 churn
  97 apps/web/app             122 churn
  96 packages/ui/src           54 churn
  86 apps/web/api              60 churn
  61 apps/server/tests        110 churn
  57 apps/server/services     239 churn
  51 apps/server/models       125 churn
  32 apps/server/routes       148 churn
  31 apps/server/repositories  52 churn
```

Resulting domains — note how few map 1:1 to a row:

| Skill                      | Covers                                     | Rationale                                            |
| -------------------------- | ------------------------------------------ | ---------------------------------------------------- |
| `server-api-endpoint`      | `routes/` + `services/` + `repositories/`  | Three rows, one request path → **merged**             |
| `server-models-migrations` | `models/` + `migrations/`                  | Schema change is always both                          |
| `server-testing`           | `tests/`                                   | Suite is deliberately mock-based; agents assume a DB  |
| `web-data-layer`           | `apps/web/api/`                            | Looks like route handlers, is a client layer → trap   |
| `web-page`                 | `apps/web/app/`                            | Page = route + menu + permission + i18n + doc row     |
| `web-forms`                | `components/**/*-form*`                    | Cuts across a row, not a row itself                   |
| `ui-component`             | `packages/ui` + `styles` + `storybook`     | Three units, one authoring workflow → **merged**      |
| `web-i18n` / `server-i18n` | web `i18n/` / server `utils/i18n/`         | One word, two systems → **split**                     |
| `db-data-scripts`          | no directory                               | Cross-cutting, dangerous, recurring                   |
| `role-based-access`        | ability + menu + guards + backend mirror   | Cross-cutting                                         |

`apps/web/components` was the highest-churn row and got **no** general skill — "a React component"
carries no repo-specific convention beyond what `ui-component` already states. Only the *forms* slice
of it was non-obvious. High churn justifies a look, never a skill by itself.

## Naming

`<area>-<subject>`, kebab-case, area first so related skills sort together: `server-api-endpoint`,
`web-data-layer`, `ui-component`. Skip the project name — the skill already lives in the project.
Name the task, not the folder (`db-data-scripts`, not `scripts-dir`).

## Scaling to massive repos

- Decide domains from `inventory.sh` and `git log` only. Reading files to *choose* domains does not
  scale; reading them to *write* a chosen skill is the subagent's job.
- Cap the first pass at ~8 domains, highest churn first. Say what you deferred.
- Batch subagents ≤4 at a time; each returns a summary, never file contents.
- In a repo with independent sub-projects, consider directory-scoped skills
  (`apps/web/.claude/skills/`) so they only load in that tree. Default to repo root otherwise.
- If `inventory.sh` is slow (>10s), the repo is not fully git-tracked — narrow with
  `inventory.sh apps/web` and run per sub-tree.
