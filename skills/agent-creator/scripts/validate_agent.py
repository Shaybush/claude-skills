#!/usr/bin/env python3
"""Lint agent definitions against the house standard.

Usage:
    validate_agent.py <path/to/agent.md> [more.md ...]
    validate_agent.py --all [--dir ~/.claude/agents]

Exit code is non-zero if any ERROR is reported. WARNs do not fail the run.
"""

import argparse
import re
import sys
from pathlib import Path

VALID_MODELS = {'sonnet', 'opus', 'haiku'}
VALID_MEMORY = {'project', 'user'}
VALID_COLORS = {'red', 'blue', 'green', 'yellow', 'purple', 'orange', 'pink', 'cyan'}

REQUIRED_SECTIONS = {
    '## Knowledge Base': (),
    '## Memory Discipline': (),
    '## Always': ('## Operational Guidelines',),
    '## Workflow': ('## Response Format',),
}

MEMORY_MARKERS = [
    'Memory is for the rare fact worth recalling in a FUTURE session',
    'NEVER save',
    'One good memory beats ten',
]

LEGACY_MARKERS = {
    'context manager': 'references a "context manager" that does not exist in this setup',
    'checklist:': 'uses a legacy checklist block instead of ## Always / ## Workflow',
    'When invoked:': 'uses the legacy "When invoked:" opener instead of an identity paragraph',
}

KB_ROOT = Path.home() / '.claude' / 'docs-claude' / 'kb'
GLOBAL_CLAUDE_MD = Path.home() / '.claude' / 'CLAUDE.md'


def parse_frontmatter(text):
    if not text.startswith('---\n'):
        return None, text
    end = text.find('\n---\n', 4)
    if end == -1:
        return None, text
    raw = text[4:end]
    body = text[end + 5:]
    fields = {}
    for line in raw.split('\n'):
        if not line.strip() or line.startswith('#') or line.startswith(' '):
            continue
        if ':' not in line:
            continue
        key, _, value = line.partition(':')
        fields[key.strip()] = value.strip()
    return fields, body


def routing_table_names(claude_md):
    if not claude_md.is_file():
        return None
    names = set()
    for line in claude_md.read_text(encoding='utf-8').splitlines():
        if line.startswith('|') and line.count('|') >= 3:
            cell = line.rsplit('|', 2)[1].strip().strip('`')
            if re.fullmatch(r'[a-z0-9-]+', cell):
                names.add(cell)
    return names


def check(path, colors_seen, routed):
    errors, warns = [], []
    text = path.read_text(encoding='utf-8')
    fm, body = parse_frontmatter(text)

    if fm is None:
        return ['no YAML frontmatter found'], []

    name = fm.get('name')
    if not name:
        errors.append('missing required field: name')
    elif name != path.stem:
        errors.append(f"name '{name}' does not match filename '{path.stem}.md' "
                      f"(rename the file to {name}.md, or change the field)")

    desc = fm.get('description', '')
    if not desc:
        errors.append('missing required field: description')
    else:
        if 'Use this agent when' not in desc:
            warns.append("description does not open with 'Use this agent when ...'")
        n_examples = desc.count('<example>')
        if n_examples == 0:
            errors.append('description has no <example> blocks — the router has nothing '
                          'concrete to match on')
        elif n_examples < 3:
            warns.append(f'description has only {n_examples} <example> block(s); '
                         'the standard is 3-5 covering distinct trigger shapes')
        if n_examples != desc.count('</example>'):
            errors.append('unbalanced <example> / </example> tags in description')

    model = fm.get('model')
    if not model:
        errors.append('missing required field: model')
    elif model not in VALID_MODELS:
        errors.append(f"model '{model}' is not one of {sorted(VALID_MODELS)}")

    memory = fm.get('memory')
    if not memory:
        warns.append('no memory: field — this agent has no memory store '
                     "(add 'project' or 'user')")
    elif memory not in VALID_MEMORY:
        errors.append(f"memory '{memory}' is not one of {sorted(VALID_MEMORY)}")

    color = fm.get('color')
    if not color:
        warns.append('no color: field — the agent has no terminal identity')
    elif color not in VALID_COLORS:
        warns.append(f"color '{color}' is unconventional; used elsewhere: {sorted(VALID_COLORS)}")
    elif color in colors_seen:
        errors.append(f"color '{color}' collides with {colors_seen[color]}")
    if color:
        colors_seen.setdefault(color, path.name)

    tools = fm.get('tools')
    if tools is not None:
        if tools.rstrip().endswith(','):
            errors.append('tools list has a trailing comma')
        for tool in [t.strip() for t in tools.split(',') if t.strip()]:
            if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_-]*', tool):
                warns.append(f"tools entry '{tool}' does not look like a valid tool name")

    for section, equivalents in REQUIRED_SECTIONS.items():
        if section in body:
            continue
        alt = next((e for e in equivalents if e in body), None)
        if alt is None:
            errors.append(f'missing required section: {section}')

    if '## Memory Discipline' in body:
        for marker in MEMORY_MARKERS:
            if marker not in body:
                warns.append(f'Memory Discipline block has drifted from the boilerplate '
                             f'(missing: "{marker[:40]}...")')
                break

    if '## Always' in body:
        always = body.split('## Always', 1)[1].split('\n## ', 1)[0]
        if 'No comments in code' not in always:
            warns.append("## Always is missing the global 'No comments in code.' rule")
        if 'Single quotes' not in always:
            warns.append("## Always is missing the global 'Single quotes; imports only at "
                         "the top of the file.' rule")

    for path_str in re.findall(r'^\|\s*`([^`]+\.md)`\s*\|', body, re.MULTILINE):
        if path_str.startswith('~') or path_str.startswith('/'):
            continue
        if not (KB_ROOT / path_str).exists():
            errors.append(f'Knowledge Base row points at a file that does not exist: '
                          f'{KB_ROOT / path_str}')

    for marker, why in LEGACY_MARKERS.items():
        if marker.lower() in body.lower():
            warns.append(f'legacy pattern — {why}')

    if routed is not None and name and name not in routed:
        warns.append(f"'{name}' is absent from the CLAUDE.md routing table — "
                     'nothing will route to it')

    return errors, warns


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('paths', nargs='*', help='agent .md files to check')
    parser.add_argument('--all', action='store_true', help='check every agent in --dir')
    parser.add_argument('--dir', default=str(Path.home() / '.claude' / 'agents'),
                        help='agents directory for --all (default: ~/.claude/agents)')
    args = parser.parse_args()

    if args.all:
        agent_dir = Path(args.dir).expanduser()
        paths = sorted(agent_dir.glob('*.md'))
        if not paths:
            print(f'no agents found in {agent_dir}', file=sys.stderr)
            return 1
    elif args.paths:
        paths = [Path(p).expanduser() for p in args.paths]
    else:
        parser.error('give one or more paths, or --all')

    routed = routing_table_names(GLOBAL_CLAUDE_MD)
    colors_seen = {}
    total_errors = 0

    for path in paths:
        if not path.is_file():
            print(f'✗ {path}: not found')
            total_errors += 1
            continue
        errors, warns = check(path, colors_seen, routed)
        total_errors += len(errors)
        if not errors and not warns:
            print(f'✅ {path.name}')
            continue
        print(f"{'✗' if errors else '⚠'} {path.name}")
        for err in errors:
            print(f'    ERROR  {err}')
        for warn in warns:
            print(f'    warn   {warn}')

    print()
    print(f'{len(paths)} agent(s) checked, {total_errors} error(s)')
    return 1 if total_errors else 0


if __name__ == '__main__':
    sys.exit(main())
