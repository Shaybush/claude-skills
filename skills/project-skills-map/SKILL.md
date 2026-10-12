---
name: project-skills-map
description: "Survey a whole repository, decide which parts deserve their own Claude skill, and author or refresh those skills with skill-creator — then wire a routing table into CLAUDE.md so the right skill loads automatically. Use this skill whenever the user wants to bootstrap skills for a project ('add skills to this repo', 'create skills for each module', 'document our conventions as skills'), whenever they ask to audit, refresh, update or re-check existing skills after the code moved on ('are my skills stale', 'update the skills', 'we changed X, fix its skill'), and whenever a large refactor, new module, or new app has landed and the project's skills may no longer describe reality. Also use it when a repo has no .claude/skills yet and the user is about to hand-write one skill at a time."
---

# Project Skills Map

Turn a repository into a set of **module-scoped skills**, then keep them true as the code changes.

Two things make this work, and both are non-negotiable:

1. **Never read the whole repo.** Decide domains from cheap structural signal (`scripts/inventory.sh`),
   then let one subagent per domain do the deep reading in parallel.
2. **Never redo settled work.** `.claude/skills-map.json` records which globs each skill covers and the
   commit it was authored at. A re-run diffs against that and touches only what actually moved.

## Which mode am I in?

Run the orientation step first; it answers this for you.

```bash
SKILLS_MAP="$HOME/.claude/skills/project-skills-map"   # adjust if installed per-project
"$SKILLS_MAP/scripts/inventory.sh" .
python3 "$SKILLS_MAP/scripts/skills_manifest.py" status
```

| What you see                                | Mode          | Go to   |
| ------------------------------------------- | ------------- | ------- |
| No `.claude/skills-map.json`, no skills      | **Bootstrap** | Phase 1 |
| Skills exist but no manifest                 | **Adopt**     | Phase 0 |
| Manifest exists                              | **Refresh**   | Phase 0 |

### Phase 0 — Adopt / Refresh

Manifest schema, glob semantics, and the full refresh recipe are in
`references/manifest-and-refresh.md` — read it before your first `set`.

**Adopt** (skills exist, manifest does not) — reconstruct the record before changing anything:

```bash
python3 "$SKILLS_MAP/scripts/skills_manifest.py" init --adopt
```

This seeds one entry per existing skill with **empty globs**. Fill them in by reading each SKILL.md's
description and body for the paths it claims, then:

```bash
python3 "$SKILLS_MAP/scripts/skills_manifest.py" set --name web-data-layer --globs 'apps/web/api/**'
```

Adoption baselines every skill at HEAD, which asserts "these skills are currently true." If the user
says some are already stale, `set --keep-commit` them to an older commit, or just treat them as stale
in Phase 3.

**Refresh** — `status` prints three buckets. Work them in this order:

- **STALE** — covered files changed since the skill was authored → Phase 3, *update* path.
- **UNCOVERED** — changed source files no skill claims → Phase 1, but scoped to just those paths.
- **FRESH** — leave alone. Do not rewrite a skill because you could.

Most refreshes touch one or two skills. That is success, not under-delivery.

## Phase 1 — Choose the domains

This is the judgment step and the whole value of the skill. Read
`references/domain-discovery.md` before proposing anything.

**Dispatch explorer agents, do not explore yourself.** Split the inventory into sections (one per app,
package, or top-level directory group that needs understanding) and launch one `Explore` subagent per
section, **at most 4 in flight**, all in a single message so they run concurrently. In Refresh mode,
send explorers only to the STALE and UNCOVERED sections.

**Huge sections get several explorers.** When one section is too big for a ~25 file budget (a large
app, a monorepo package with many modules), launch multiple `Explore` agents on that same section,
each assigned a disjoint slice of it (by subdirectory or by layer). Give each the same brief with its
own slice paths and tell it which slices its siblings own. Merge their reports as if they were one
section's answer.

Brief for each explorer:

> Explore `<section paths>` in this repo (read-only). Find the recurring task shapes a developer
> repeats here (new route, new screen, new migration, etc.), count the existing instances of each,
> and name the wrong-but-plausible thing a competent agent would do instead of the local pattern.
> Apply the four tests from the skill (recurring, patterned, non-obvious, scattered).
> Budget ~25 file reads; prefer grep over broad reads.
>
> Return, per candidate domain: proposed skill name, globs, 3-6 anchor files, instance count, the
> wrong-but-plausible thing it prevents, and a verdict (earns a skill, or reject with a reason). Also
> list any section content that belongs to a domain owned by another section. Do not write any files.

Merge the returned candidates yourself: dedupe domains that span sections, merge candidates that
would always load together, and record every rejection. The main agent reads the explorers' reports,
not the section files.

**A domain is a recurring task shape, not a folder.** In a repo where `routes/`, `services/`, and
`repositories/` are three layers of one request, that is *one* skill, not three. Conversely `i18n`
splits into two skills when the server and web halves are genuinely different systems.

A candidate earns a skill only if **all four** hold:

1. **Recurring** — the churn table shows people work here repeatedly.
2. **Patterned** — there are ≥3 consistent existing instances to generalize from.
3. **Non-obvious** — a competent agent following framework docs would plausibly do it
   *differently and wrongly*. This is the sharpest test: if you cannot name the wrong-but-plausible
   thing the skill prevents, there is no skill here.
4. **Scattered** — the answer spans several files, so rediscovery is expensive.

Reject: generic framework knowledge with no local deviation; areas with one or two instances; config
touched twice a year; generated or vendored code; anything already fully covered by `CLAUDE.md`.

Record every rejection so the next run does not re-litigate it:

```bash
python3 "$SKILLS_MAP/scripts/skills_manifest.py" ignore --glob 'packages/typescript-config/**' \
  --reason 'config only, no recurring task'
```

**Sizing.** Aim for 5–12 skills in a typical repo. When two candidates would always be loaded
together, merge them. When one candidate's SKILL.md would exceed ~500 lines, split it. On a first
pass over a massive repo, cap at the ~8 highest-churn domains and say plainly that a second pass can
cover the rest — a small set of true skills beats twenty thin ones.

## Phase 2 — Confirm before authoring

Show the user a table and get a yes. Authoring is the expensive part; a wrong domain list wastes all
of it.

| Domain | Paths | Why it earns a skill (the wrong-but-plausible thing it prevents) | New/Update |
| ------ | ----- | ---------------------------------------------------------------- | ---------- |

Ask directly about anything you are unsure of, and mention what you are deliberately skipping and
why. If the user only wants a subset, honor it exactly.

## Phase 3 — Author in parallel

One subagent per confirmed domain, **at most 4 in flight**, launched in a single message per batch.
Each writes its own files, so they never conflict. Reuse the explorer's anchor files and findings in
the brief so the author does not rediscover the section from scratch.

Give every subagent this brief, filled in:

> Write (or update) the `<name>` skill at `.claude/skills/<name>/SKILL.md` for this repo.
>
> Scope: `<globs>`. Anchor files to study: `<3-6 concrete paths>`.
>
> Load the `skill-creator` skill and follow its **"Write the SKILL.md"** and **"Skill Writing Guide"**
> sections for format, frontmatter, and progressive disclosure. Skip its eval/benchmark loop.
>
> Read the anchor files and enough neighbors to state the pattern with confidence. Budget ~25 file
> reads; prefer grep over broad reads.
>
> The skill must contain: the house pattern with a real snippet from this repo, the file map
> (`path:line` where it helps), the gotchas that bite here, and an end-to-end checklist for the
> common task. Document what the code **actually does**, including deliberate oddities — never what
> best practice says it should do. If a README contradicts the code, the code wins; say so in the skill.
>
> Put anything over ~300 lines in `references/` and point at it from SKILL.md.
>
> Return: the file path, the description line, the globs the skill covers, and 3 bullets on what you
> found. Do not paste the file back.

**Update path** (STALE skills): do not rewrite from scratch. Read the actual diff first —
`git diff <last_authored_commit>..HEAD -- <globs>` — then patch the specific sections that moved and
leave the rest alone. Tell the subagent exactly that, and pass it the diff stat. A refresh that
rewrites a good skill loses hard-won detail.

After each subagent returns:

```bash
python3 "$SKILLS_MAP/scripts/skills_manifest.py" set --name <name> --globs <globs...> \
  --anchors <paths...> --description "<one line>"
```

## Phase 4 — Wire CLAUDE.md

A skill nobody loads is worth nothing. Add or refresh the routing table plus the staleness rule the
user relies on — exact templates and the marker convention are in `references/claude-md-wiring.md`.

The block is delimited by `<!-- BEGIN skills-map -->` / `<!-- END skills-map -->` so later runs
regenerate it without disturbing hand-written parts of CLAUDE.md. Never edit outside the markers
without asking.

The maintenance rule inside that block is what makes Claude suggest re-running this skill after a
module's logic changes. Do not omit it.

## Phase 5 — Validate and report

```bash
# quick_validate.py needs pyyaml — run it through uv so you do not have to install anything
uv run --quiet --with pyyaml python \
  "$HOME/.claude/plugins/marketplaces/claude-plugins-official/plugins/skill-creator/skills/skill-creator/scripts/quick_validate.py" \
  .claude/skills/<name>
python3 "$SKILLS_MAP/scripts/skills_manifest.py" status
```

`status` should now show the domains you covered as FRESH. Then report:

- skills created, skills updated, skills left alone (and why)
- what is still uncovered and whether it deserves a pass
- the CLAUDE.md rows added

Do not bump the baseline past work you have not actually verified.

## Non-negotiables

- **Confirm before authoring.** Phase 2 is not optional.
- **The code is the truth.** Never write an aspirational convention into a skill.
- **Descriptions carry the triggering.** Every skill's description names its paths *and* the phrases
  a user would say. Undertriggering is the common failure.
- **Record rejections.** An unrecorded "no" gets re-litigated every run.
- **Idempotent.** Re-running with no code change must produce no edits.

## Reference files

| File | Read it when |
| ---- | ------------ |
| `references/domain-discovery.md` | Phase 1 — choosing domains (always) |
| `references/manifest-and-refresh.md` | Phase 0/3 — manifest schema, globs, patching a stale skill |
| `references/claude-md-wiring.md` | Phase 4 — the CLAUDE.md block templates |
| `scripts/inventory.sh` | Phase 0 — structural scan (`inventory.sh . --churn=300`) |
| `scripts/skills_manifest.py` | Phases 0/3/5 — track coverage and staleness |
