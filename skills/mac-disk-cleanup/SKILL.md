---
name: mac-disk-cleanup
description: Find and reclaim disk space on macOS — scans caches, dev artifacts, Docker, apps and personal media, reports what is safe versus what is not, then deletes only what the user explicitly picks.
allowed-tools:
  - Bash(bash:*)
  - Bash(python3:*)
  - Bash(df:*)
  - Bash(du:*)
  - Bash(find:*)
  - Bash(stat:*)
  - Bash(date:*)
  - Bash(rm:*)
  - Bash(docker:*)
  - Bash(brew:*)
  - Bash(npm:*)
  - Bash(pnpm:*)
  - Bash(uv:*)
  - Bash(xcrun:*)
  - Bash(osascript:*)
  - Read
  - AskUserQuestion
when_to_use: >
  Use when a macOS user is low on disk space or wants to find what is consuming it.
  Trigger phrases: "my disk is full", "my memory on this computer is almost full",
  "running out of space", "free up disk space", "what's taking up all my space",
  "find files I never use", "delete apps I don't use", "clean up my Mac",
  "clear caches", "node_modules are eating my disk", "Docker is huge",
  "האחסון שלי מלא", "לנקות מקום". Also use when a build, install, or Docker pull
  fails with a no-space-left-on-device error. macOS only — the paths and tools
  here are Darwin-specific.
argument-hint: "[scan-root]"
arguments:
  - scan_root
---

# macOS Disk Cleanup

Find what is eating a Mac's disk, present it ranked and risk-tiered, and reclaim only
what the user approves — measuring real freed space at every phase.

## Inputs
- `$scan_root`: Optional. Directory tree to hunt dev artifacts in. Defaults to `$HOME`.
  Pass something like `~/Desktop/projects` to scope the `node_modules`/`.venv` sweep.

## Goal
The user ends with materially more free space, a clear account of where every reclaimed
gigabyte came from, and an explicit list of what was deliberately left alone and why.
Nothing irreversible happens without them choosing it by name.

## Hard rules

Non-negotiable. These override any inference about what the user "probably" wants.

- **Never delete personal media unasked.** Photos, videos, Messages/WhatsApp/Telegram
  attachments, Downloads, Desktop documents. Always inventory by file type and size and
  show that breakdown *before* offering deletion. A 49 GB media store is typically 30 GB
  of irreplaceable content and 19 GB of disposable cache — the user must see that split
  to decide well.
- **Never prune named Docker volumes.** Images, build cache and anonymous volumes are
  fair game. Named compose volumes (`postgres_data`, `mongodb_data`, `redis_data`,
  `minio_data`, …) hold local dev database state. Report them, never delete them.
- **Never use sudo and never touch system paths.** Stay inside `$HOME` and
  `/Applications`. When something needs admin — Mac App Store apps are SIP-protected and
  resist `rm -rf` at any user privilege level — print the exact command for the user to
  run themselves.
- **Always measure before and after each phase.** Report the real `df` delta per phase,
  never an estimate, so the user can stop early once they have enough headroom.

## Steps

### 1. Baseline and scan
Capture free space, then run the bundled scanner:

```bash
bash <skill-dir>/scripts/scan.sh /tmp/mac-disk-scan.txt
```

**Run it in the background.** A full `du` sweep of `$HOME` routinely exceeds a two-minute
foreground timeout. Start it backgrounded and read the report file when it completes.

In parallel, dry-run the dev-artifact sweep so its numbers are ready:

```bash
python3 <skill-dir>/scripts/clean.py "$scan_root" --dry-run
```

**Success criteria**: `/tmp/mac-disk-scan.txt` exists and contains every section, and you
have a total for reclaimable `node_modules`/`.venv`.
**Artifacts**: baseline free-GB number; the scan report; dev-artifact total.

### 2. Attribute the space
Drill into whatever the report shows as oversized but unexplained — usually
`~/Library/{Group Containers,Containers,Application Support,Caches,Developer}`. Descend
until every large number has a named cause, not just a directory.

**Success criteria**: every item over ~5 GB is explained by a specific app or cache.
**Rules**: Use `find`, never bare globs — zsh aborts the whole command on an unmatched
glob, silently emptying your results.

### 3. Report
Two tables, ranked by size:

- **Safe to reclaim** — regenerates on demand, zero risk. Build caches, package-manager
  stores, browser binaries, stale updater installers.
- **Your call** — real data or working tools. Apps, personal media, named Docker volumes,
  project trees.

For apps, include a last-activity date. **Spotlight's `kMDItemLastUsedDate` returns null
for most apps and is not usable.** Age them by the mtime of their preference, container,
or Application Support directory instead — that is what `scan.sh` does. Flag that
background daemons (VPN clients, mouse drivers, updaters) touch their own files daily and
will look "active" regardless of actual use.

**Success criteria**: the user can see, in one screen, the ten biggest items and which
tier each falls in.

### 4. Ask — [human]
Use **AskUserQuestion**, never plain text. One question per risk tier, `multiSelect: true`,
every option labelled with its GB. Give each destructive tier an explicit opt-out option.

Tiers that work well: *dev caches*, *dev artifacts (node_modules/.venv)*, *Docker*,
*unused apps*, *personal media*.

**Success criteria**: an explicit selection exists for every tier you intend to touch.
**Rules**: Selecting "keep all apps" in one tier does not veto a specific app the user
names in free text — honour the more specific instruction. Never infer consent for a tier
the user did not answer.

### 5. Execute in phases
One Bash call per tier, each wrapped in a `df` before/after so the delta prints. Report
the running total after each phase.

Known behaviours to handle:
- `npm cache clean --force` fails outright if any cache file is root-owned. Just
  `rm -rf ~/.npm/_cacache ~/.npm/_npx ~/.npm/_logs` instead.
- `pnpm store prune` only releases *unreferenced* packages. The store stays large while
  `node_modules` trees still hardlink into it — prune again after removing them.
- `docker system prune -a --volumes` does **not** remove named volumes, which is the
  behaviour you want here. `Docker.raw` shrinks on its own after the prune.
- `xcrun simctl delete unavailable` frees nothing when every simulator is current-gen.
  Check before promising the space.
- Mac App Store apps cannot be removed with `rm -rf`. Hand the user the command.

**Success criteria**: each phase prints its own `+N GB`, and the sum is consistent with
the new `df` total.
**Human checkpoint**: Before deleting any personal media store, show the type/size
inventory and get a second explicit confirmation — even if the tier was already selected.

### 6. Final report
State the new free space against the baseline, a table of what each phase reclaimed,
anything the user must finish by hand (with the exact command), and an explicit
**"what I left alone and why"** section.

**Success criteria**: the user knows their new free space, has commands for any manual
step, and nothing was deleted that they did not select.
**Rules**: APFS reports space back lazily, so per-phase deltas may not sum exactly to the
`df` total. Say so rather than quietly fudging the numbers.

## Bundled scripts

- `scripts/scan.sh [report-path]` — one-pass system scan. Disk, home, Library, dev caches,
  apps with activity dates, Docker, files over 1 GB, Trash/Downloads, personal media
  stores. Run it backgrounded. Paths it cannot size print `locked` (macOS TCC).
- `scripts/clean.py [root] [--dry-run] [--include-build] [--min-mb N] [--top N]` — finds
  and removes `node_modules`, `.venv`, `venv`; `--include-build` adds `dist`, `build`,
  `.next`, `__pycache__`, `.turbo` and friends. De-duplicates hardlinked inodes so pnpm
  trees report true reclaimable size rather than inflated apparent size. Always
  `--dry-run` first.
