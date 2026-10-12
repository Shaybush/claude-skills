# Manifest & incremental refresh

`.claude/skills-map.json` is what makes a re-run cheap. Without it every run is a full re-survey and
you rewrite skills that were already correct.

Commit it. It is a project record, not a cache.

## Schema

```json
{
  "version": 1,
  "baseline_commit": "3c89c021...",
  "updated_at": "2026-09-10",
  "skills": [
    {
      "name": "web-data-layer",
      "path": ".claude/skills/web-data-layer",
      "globs": ["apps/web/api/**"],
      "anchors": ["apps/web/api/auth/auth.hooks.ts"],
      "description": "React Query hook layer over the Flask backend",
      "last_authored_commit": "3c89c021..."
    }
  ],
  "ignored": [
    { "glob": "packages/typescript-config/**", "reason": "config only, no recurring task" }
  ]
}
```

**`globs`** decide everything — they answer "did this skill's world change?" Too broad and the skill
is permanently stale; too narrow and real changes slip past. Match what the skill actually documents,
including cross-cutting slices:

```
apps/web/api/**                    a directory the skill owns
apps/web/components/**/*-form*     a slice cutting across a directory
apps/server/{models,migrations}/** NOT supported — write two globs instead
```

Supported: `**`, `*`, `?`. Brace expansion is not; list separate globs. Literal `[` and `(` are matched
literally, so Next.js paths like `app/[locale]/(pages)/**` work as written.

**`last_authored_commit`** is per skill, so refreshing one does not reset the others.

**`ignored`** is the memory of every "no". Without it, each run re-proposes the same rejected areas and
the user re-explains the same reasoning.

## Commands

```bash
M="python3 $HOME/.claude/skills/project-skills-map/scripts/skills_manifest.py"

$M init --adopt                 # seed from existing .claude/skills/*, baseline at HEAD
$M status                       # stale / uncovered / fresh
$M status --mode full           # classify the whole tree, not just the diff
$M status --json                # machine-readable
$M set --name X --globs 'a/**' 'b/**' --anchors path --description "..."
$M set --name X --keep-commit --globs ...   # fix globs without claiming a re-author
$M ignore --glob 'p/**' --reason '...'
$M bump --name X                # mark X authored at HEAD
$M remove --name X
$M --root /path --manifest /tmp/t.json status   # inspect another repo, write nowhere
```

`status` counts **uncommitted work too**, so a skill shows stale as soon as you edit its files —
before you commit.

## How staleness is decided

For each skill: diff `last_authored_commit..HEAD`, keep files matching that skill's globs. Any hit →
STALE, with the file list. Changed source files matching no skill glob and no ignore glob → UNCOVERED,
aggregated by directory.

Consequences worth knowing:

- A skill with **no globs** always reports stale with `reason: no globs recorded`. That is the adopt
  path telling you to finish the job, not a real staleness signal.
- Non-source files (`.md`, `.json`, `.css`) never count as uncovered, but *do* count as stale for a
  skill whose globs match them. Deliberate: a changed config inside a documented domain matters; a
  stray markdown file does not deserve its own skill.
- No git → `status` falls back to a full scan and cannot compute staleness. Say so rather than
  implying the skills are verified.

## Refresh recipe

```bash
$M status
git diff --stat <last_authored_commit>..HEAD -- apps/web/api
git diff <last_authored_commit>..HEAD -- apps/web/api | head -200
```

Read the diff before opening the skill. Then judge:

| What the diff shows                                  | Action                                    |
| ---------------------------------------------------- | ----------------------------------------- |
| More instances of the documented pattern             | Nothing. `bump` and move on.              |
| A new file role / a changed contract                 | Patch the affected section.               |
| The documented pattern replaced                      | Rewrite that section; keep the gotchas.   |
| The domain split in two                              | Propose a new skill; back to Phase 1.     |
| Files deleted, domain gone                           | `remove`, delete the dir, drop the row.   |

**Patch, do not regenerate.** A mature skill holds gotchas discovered over months that no diff will
re-reveal. Regenerating throws them away and looks like progress.

After patching, `set` the skill (this stamps HEAD) and re-run `status` to confirm it left the stale
bucket.

## Uncovered work

Uncovered is aggregated by directory:

```
UNCOVERED source files: 159
    114  apps/server
     36  apps/web
      9  packages/shared
```

Use `--depth 3` for a finer split. Then either extend an existing skill's globs (if it already covers
the concept and the glob was just too narrow) or take it to Phase 1 as a new domain. If neither, it
belongs in `ignored` — with a real reason.

Uncovered is expected to be non-zero forever. Most files in most repos do not need a skill. Chasing
zero produces exactly the thin, unhelpful skills this whole approach exists to avoid.

## Failure modes

- **Stale skill nobody notices** → the CLAUDE.md maintenance rule; check `status` at the start of any
  session that will touch a documented domain.
- **Globs drift** as directories move. If a skill never goes stale, its globs are probably wrong —
  verify with `status --mode full`, which prints per-skill covered file counts.
- **Manifest not committed** → every clone re-surveys from scratch. Commit it.
- **Baseline bumped without doing the work** → skills silently claim to be current. Only `bump` what
  you verified.
