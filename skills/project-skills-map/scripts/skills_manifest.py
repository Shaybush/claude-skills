#!/usr/bin/env python3
"""Track which skills cover which paths, and what changed since each was authored.

Manifest lives at <repo>/.claude/skills-map.json. Stdlib only.

  init [--adopt]        create the manifest, optionally seeding from existing skills
  status [--json]       what is stale / uncovered since each skill was authored
  set                   upsert one skill entry
  ignore                record a path as deliberately skill-free
  bump                  mark skills as authored at the current commit
  remove                drop a skill entry
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from datetime import date
from pathlib import Path

MANIFEST_REL = '.claude/skills-map.json'
VERSION = 1

SOURCE_SUFFIXES = {
    '.py', '.ts', '.tsx', '.js', '.jsx', '.mjs', '.cjs', '.go', '.rs', '.rb',
    '.java', '.kt', '.swift', '.php', '.cs', '.scala', '.ex', '.exs', '.vue',
    '.svelte', '.sql', '.graphql', '.proto', '.sh', '.gs',
}


def run_git(root: Path, *args: str) -> str | None:
    try:
        out = subprocess.run(
            ['git', '-C', str(root), *args],
            capture_output=True, text=True, check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return out.stdout.strip()


def head_commit(root: Path) -> str | None:
    return run_git(root, 'rev-parse', 'HEAD')


def changed_since(root: Path, base: str) -> list[str] | None:
    """Files changed between base and HEAD, plus uncommitted work."""
    if not base:
        return None
    committed = run_git(root, 'diff', '--name-only', f'{base}..HEAD')
    if committed is None:
        return None
    dirty = run_git(root, 'status', '--porcelain') or ''
    files = set(f for f in committed.splitlines() if f)
    for line in dirty.splitlines():
        path = line[3:].strip()
        if ' -> ' in path:
            path = path.split(' -> ', 1)[1]
        if path:
            files.add(path)
    return sorted(files)


def tracked_files(root: Path) -> list[str]:
    listed = run_git(root, 'ls-files')
    if listed is not None:
        return [f for f in listed.splitlines() if f]
    return [
        str(p.relative_to(root))
        for p in root.rglob('*')
        if p.is_file() and not any(
            part in {'.git', 'node_modules', '__pycache__', 'dist', 'build', '.next', '.venv'}
            for part in p.parts
        )
    ]


def glob_to_re(glob: str) -> re.Pattern[str]:
    """Translate a path glob to a regex. Supports **, *, ?."""
    i, out = 0, ['^']
    while i < len(glob):
        ch = glob[i]
        if glob.startswith('**/', i):
            out.append('(?:.*/)?')
            i += 3
        elif glob.startswith('**', i):
            out.append('.*')
            i += 2
        elif ch == '*':
            out.append('[^/]*')
            i += 1
        elif ch == '?':
            out.append('[^/]')
            i += 1
        else:
            out.append(re.escape(ch))
            i += 1
    out.append('$')
    return re.compile(''.join(out))


class Matcher:
    def __init__(self, globs: list[str]):
        self.patterns = [glob_to_re(g) for g in globs]

    def matches(self, path: str) -> bool:
        return any(p.match(path) for p in self.patterns)


def manifest_path(root: Path, override: str | None) -> Path:
    return Path(override) if override else root / MANIFEST_REL


def load(root: Path, override: str | None) -> dict:
    path = manifest_path(root, override)
    if not path.exists():
        return {'version': VERSION, 'baseline_commit': None, 'skills': [], 'ignored': []}
    return json.loads(path.read_text())


def save(root: Path, override: str | None, data: dict) -> Path:
    path = manifest_path(root, override)
    path.parent.mkdir(parents=True, exist_ok=True)
    data['updated_at'] = date.today().isoformat()
    path.write_text(json.dumps(data, indent=2) + '\n')
    return path


def discover_skills(root: Path) -> list[dict]:
    """Read existing SKILL.md frontmatter so an already-skilled repo can be adopted."""
    found = []
    for skill_md in sorted(root.glob('.claude/skills/*/SKILL.md')):
        name = skill_md.parent.name
        description = ''
        text = skill_md.read_text(errors='replace')
        if text.startswith('---'):
            end = text.find('\n---', 3)
            fm = text[3:end if end > 0 else len(text)]
            match = re.search(r'^name:\s*(.+)$', fm, re.M)
            if match:
                name = match.group(1).strip().strip('"\'')
            match = re.search(r'^description:\s*(.+)$', fm, re.M | re.S)
            if match:
                description = match.group(1).strip()[:400]
        found.append({
            'name': name,
            'path': str(skill_md.parent.relative_to(root)),
            'globs': [],
            'description': description,
            'last_authored_commit': None,
        })
    return found


def aggregate(paths: list[str], depth: int = 2, top: int = 25) -> list[tuple[str, int]]:
    counter: Counter[str] = Counter()
    for path in paths:
        parts = path.split('/')
        key = '/'.join(parts[:depth]) if len(parts) > depth else '/'.join(parts[:-1]) or '.'
        counter[key] += 1
    return counter.most_common(top)


def is_sourceish(path: str) -> bool:
    return Path(path).suffix in SOURCE_SUFFIXES


def cmd_init(args, root: Path) -> int:
    data = load(root, args.manifest)
    if data['skills'] and not args.force:
        print(f'Manifest already exists with {len(data["skills"])} skill(s). Use --force to reset.')
        return 1
    head = head_commit(root)
    data['version'] = VERSION
    data['baseline_commit'] = head
    if args.adopt:
        data['skills'] = discover_skills(root)
        for skill in data['skills']:
            skill['last_authored_commit'] = head
    path = save(root, args.manifest, data)
    print(f'Wrote {path}')
    print(f'baseline_commit: {head or "(no git)"}')
    if args.adopt:
        print(f'Adopted {len(data["skills"])} existing skill(s) — globs are EMPTY, fill them with `set`:')
        for skill in data['skills']:
            print(f'  - {skill["name"]}')
    return 0


def cmd_set(args, root: Path) -> int:
    data = load(root, args.manifest)
    head = head_commit(root)
    entry = next((s for s in data['skills'] if s['name'] == args.name), None)
    if entry is None:
        entry = {'name': args.name}
        data['skills'].append(entry)
    entry['path'] = args.path or f'.claude/skills/{args.name}'
    if args.globs:
        entry['globs'] = args.globs
    if args.anchors:
        entry['anchors'] = args.anchors
    if args.description:
        entry['description'] = args.description
    if not args.keep_commit:
        entry['last_authored_commit'] = head
    save(root, args.manifest, data)
    print(f'{args.name}: {len(entry.get("globs", []))} glob(s) @ {entry.get("last_authored_commit") or "(no git)"}')
    return 0


def cmd_ignore(args, root: Path) -> int:
    data = load(root, args.manifest)
    data.setdefault('ignored', [])
    existing = next((i for i in data['ignored'] if i['glob'] == args.glob), None)
    if existing:
        existing['reason'] = args.reason
    else:
        data['ignored'].append({'glob': args.glob, 'reason': args.reason})
    save(root, args.manifest, data)
    print(f'ignored: {args.glob} — {args.reason}')
    return 0


def cmd_remove(args, root: Path) -> int:
    data = load(root, args.manifest)
    before = len(data['skills'])
    data['skills'] = [s for s in data['skills'] if s['name'] != args.name]
    save(root, args.manifest, data)
    print('removed' if len(data['skills']) < before else 'not found')
    return 0


def cmd_bump(args, root: Path) -> int:
    data = load(root, args.manifest)
    head = head_commit(root)
    targets = data['skills'] if args.all else [s for s in data['skills'] if s['name'] in (args.name or [])]
    for skill in targets:
        skill['last_authored_commit'] = head
    data['baseline_commit'] = head
    save(root, args.manifest, data)
    print(f'bumped {len(targets)} skill(s) to {head or "(no git)"}')
    return 0


def cmd_status(args, root: Path) -> int:
    data = load(root, args.manifest)
    head = head_commit(root)
    skills = data.get('skills', [])
    ignored = data.get('ignored', [])
    ignore_matcher = Matcher([i['glob'] for i in ignored]) if ignored else None

    baseline = data.get('baseline_commit')
    mode = args.mode or ('diff' if baseline and skills else 'full')

    if mode == 'diff':
        pool = changed_since(root, baseline)
        if pool is None:
            print('! could not diff against baseline; falling back to full scan', file=sys.stderr)
            mode, pool = 'full', tracked_files(root)
    else:
        pool = tracked_files(root)

    report: dict = {'mode': mode, 'head': head, 'baseline': baseline,
                    'file_count': len(pool), 'stale': [], 'fresh': [], 'uncovered': {}}

    covered_any = Matcher([g for s in skills for g in s.get('globs', [])]) if skills else None

    for skill in skills:
        globs = skill.get('globs', [])
        if not globs:
            report['stale'].append({'name': skill['name'], 'reason': 'no globs recorded',
                                    'changed': [], 'changed_count': 0})
            continue
        matcher = Matcher(globs)
        if mode == 'diff':
            since = skill.get('last_authored_commit') or baseline
            own_pool = pool if since == baseline else (changed_since(root, since) or pool)
        else:
            own_pool = pool
        hits = [f for f in own_pool if matcher.matches(f)]
        if mode == 'diff' and hits:
            report['stale'].append({'name': skill['name'], 'reason': 'covered files changed',
                                    'changed': hits[:args.sample], 'changed_count': len(hits)})
        elif mode == 'diff':
            report['fresh'].append(skill['name'])
        else:
            report['fresh'].append(f'{skill["name"]} ({len(hits)} files covered)')

    uncovered = [
        f for f in pool
        if is_sourceish(f)
        and not (covered_any and covered_any.matches(f))
        and not (ignore_matcher and ignore_matcher.matches(f))
    ]
    report['uncovered'] = {
        'count': len(uncovered),
        'by_dir': [{'dir': d, 'files': n} for d, n in aggregate(uncovered, args.depth)],
        'sample': uncovered[:args.sample],
    }

    if args.json:
        print(json.dumps(report, indent=2))
        return 0

    print(f'mode={mode}  head={head or "(no git)"}  baseline={baseline or "(none)"}  files_in_scope={len(pool)}')
    print()
    if report['stale']:
        print('STALE — covered files changed since the skill was authored:')
        for item in report['stale']:
            print(f'  {item["name"]}: {item["reason"]} ({item["changed_count"]} file(s))')
            for f in item['changed']:
                print(f'      {f}')
    else:
        print('STALE — none')
    print()
    print(f'FRESH — {", ".join(report["fresh"]) if report["fresh"] else "none"}')
    print()
    print(f'UNCOVERED source files: {report["uncovered"]["count"]}')
    for row in report['uncovered']['by_dir']:
        print(f'  {row["files"]:5d}  {row["dir"]}')
    if ignored:
        print()
        print('IGNORED (decided against a skill previously):')
        for item in ignored:
            print(f'  {item["glob"]} — {item["reason"]}')
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--root', default='.', help='repo root (default: cwd)')
    parser.add_argument('--manifest', help='override manifest path (testing)')
    sub = parser.add_subparsers(dest='cmd', required=True)

    p = sub.add_parser('init', help='create the manifest')
    p.add_argument('--adopt', action='store_true', help='seed from existing .claude/skills/*')
    p.add_argument('--force', action='store_true')
    p.set_defaults(fn=cmd_init)

    p = sub.add_parser('status', help='what is stale / uncovered')
    p.add_argument('--mode', choices=['diff', 'full'])
    p.add_argument('--json', action='store_true')
    p.add_argument('--depth', type=int, default=2)
    p.add_argument('--sample', type=int, default=12)
    p.set_defaults(fn=cmd_status)

    p = sub.add_parser('set', help='upsert a skill entry')
    p.add_argument('--name', required=True)
    p.add_argument('--globs', nargs='+')
    p.add_argument('--anchors', nargs='+')
    p.add_argument('--path')
    p.add_argument('--description')
    p.add_argument('--keep-commit', action='store_true')
    p.set_defaults(fn=cmd_set)

    p = sub.add_parser('ignore', help='record a deliberate non-skill area')
    p.add_argument('--glob', required=True)
    p.add_argument('--reason', required=True)
    p.set_defaults(fn=cmd_ignore)

    p = sub.add_parser('bump', help='mark skills authored at HEAD')
    p.add_argument('--name', nargs='*')
    p.add_argument('--all', action='store_true')
    p.set_defaults(fn=cmd_bump)

    p = sub.add_parser('remove', help='drop a skill entry')
    p.add_argument('--name', required=True)
    p.set_defaults(fn=cmd_remove)

    args = parser.parse_args()
    return args.fn(args, Path(args.root).resolve())


if __name__ == '__main__':
    sys.exit(main())
