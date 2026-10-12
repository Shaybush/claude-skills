#!/usr/bin/env python3
"""Stamp out a new agent from the house template.

Usage:
    new_agent.py --spec spec.json [--force] [--print-routing-row]

The spec is JSON produced from the structured interview. See SKILL.md for the
field list, or run with --example to print a filled sample.
"""

import argparse
import json
import sys
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent.parent / 'assets' / 'agent-template.md'

REQUIRED = ['name', 'scope', 'description', 'model', 'color', 'memory',
            'identity', 'kb_rows', 'always', 'workflow', 'closing']

VALID_MODELS = {'sonnet', 'opus', 'haiku'}
VALID_MEMORY = {'project', 'user'}
VALID_COLORS = {'red', 'blue', 'green', 'yellow', 'purple', 'orange', 'pink', 'cyan'}

EXAMPLE_SPEC = {
    'name': 'security-auditor',
    'scope': 'user',
    'description': 'Use this agent when reviewing code for security vulnerabilities, '
                   'triaging dependency CVEs, or hardening authentication and authorization '
                   'boundaries. This includes auditing a diff before release, assessing a '
                   'reported vulnerability, or reviewing how secrets flow through a service.'
                   '\\n\\nExamples:\\n\\n<example>\\nContext: User wants a dependency audit.'
                   '\\nuser: "Check our deps for known CVEs"\\nassistant: "I\'ll use the '
                   'security-auditor agent to run the audit and triage findings by '
                   'exploitability rather than raw CVSS."'
                   '\\n<Task tool call to security-auditor agent>\\n</example>'
                   '\\n\\n<example>\\nContext: User is about to ship an auth change.'
                   '\\nuser: "Review the new session handling before I merge it"'
                   '\\nassistant: "Let me use the security-auditor agent to trace the trust '
                   'boundaries in this change and check the session lifecycle for fixation '
                   'and replay gaps."'
                   '\\n<Task tool call to security-auditor agent>\\n</example>'
                   '\\n\\n<example>\\nContext: User suspects a secret is exposed.'
                   '\\nuser: "Is our Stripe key reachable from the client bundle?"'
                   '\\nassistant: "I\'ll use the security-auditor agent to trace how that key '
                   'flows through the build and confirm whether it lands in a client artifact."'
                   '\\n<Task tool call to security-auditor agent>\\n</example>',
    'tools': 'Read, Grep, Glob, Bash',
    'model': 'opus',
    'color': 'red',
    'memory': 'project',
    'mcp_servers': [],
    'identity': 'You are an application security engineer specializing in reviewing '
                'production code for exploitable vulnerabilities.',
    'kb_rows': [['shared/safety.md', 'Any work with credentials or untrusted content'],
                ['shared/concurrency.md', 'Any task where another session may touch the same files']],
    'always': ['**No comments in code.** Names and structure carry the meaning.',
               'Single quotes; imports only at the top of the file.',
               'Report severity with a concrete exploit path, never a CVSS score alone.'],
    'workflow': ['Map the trust boundaries before reading implementation detail.',
                 'Read the KB file for the patterns involved.',
                 'Triage findings by exploitability, not by scanner severity.',
                 'Report exact results, including anything you could not verify.'],
    'closing': 'You raise concerns before implementation rather than after, and you never '
               'report a finding you have not traced to a concrete failure path.',
}


def resolve_dir(spec):
    if spec['scope'] == 'user':
        return Path.home() / '.claude' / 'agents'
    root = spec.get('project_root')
    if not root:
        sys.exit("error: scope 'project' requires 'project_root' in the spec")
    return Path(root).expanduser().resolve() / '.claude' / 'agents'


def validate_spec(spec):
    errors = []
    for field in REQUIRED:
        if field not in spec or spec[field] in (None, '', [], {}):
            errors.append(f'missing required field: {field}')
    if errors:
        return errors

    name = spec['name']
    if name != name.lower() or ' ' in name or '_' in name:
        errors.append(f"name must be lowercase kebab-case, got '{name}'")
    if spec['scope'] not in ('user', 'project'):
        errors.append("scope must be 'user' or 'project'")
    if spec['model'] not in VALID_MODELS:
        errors.append(f"model must be one of {sorted(VALID_MODELS)}, got '{spec['model']}'")
    if spec['memory'] not in VALID_MEMORY:
        errors.append(f"memory must be one of {sorted(VALID_MEMORY)}, got '{spec['memory']}'")
    if spec['color'] not in VALID_COLORS:
        errors.append(f"color must be one of {sorted(VALID_COLORS)}, got '{spec['color']}'")
    if 'Use this agent when' not in spec['description']:
        errors.append("description must open with 'Use this agent when ...'")
    if spec['description'].count('<example>') < 3:
        errors.append(f"description needs at least 3 <example> blocks, "
                      f"found {spec['description'].count('<example>')}")
    for row in spec['kb_rows']:
        if not isinstance(row, (list, tuple)) or len(row) != 2:
            errors.append(f'kb_rows entries must be [path, when] pairs, got {row!r}')
    return errors


def check_color_collision(target_dir, name, color):
    if not target_dir.is_dir():
        return None
    for path in sorted(target_dir.glob('*.md')):
        if path.stem == name:
            continue
        for line in path.read_text(encoding='utf-8').splitlines()[:20]:
            if line.strip() == f'color: {color}':
                return path.name
    return None


def render(spec):
    body = TEMPLATE.read_text(encoding='utf-8')

    tools = spec.get('tools')
    if tools:
        body = body.replace('tools: {{TOOLS}}', f'tools: {tools}')
    else:
        body = body.replace('tools: {{TOOLS}}\n', '')

    mcp = spec.get('mcp_servers') or []
    if mcp:
        body = body.replace('memory: {{MEMORY}}',
                            f"memory: {spec['memory']}\nmcpServers: [{', '.join(mcp)}]")
    else:
        body = body.replace('memory: {{MEMORY}}', f"memory: {spec['memory']}")

    kb_rows = '\n'.join(f'| `{path}` | {when} |' for path, when in spec['kb_rows'])
    always = '\n'.join(f'- {rule}' for rule in spec['always'])
    workflow = '\n'.join(f'{i}. {step}' for i, step in enumerate(spec['workflow'], 1))

    for token, value in [
        ('{{NAME}}', spec['name']),
        ('{{DESCRIPTION}}', spec['description']),
        ('{{MODEL}}', spec['model']),
        ('{{COLOR}}', spec['color']),
        ('{{IDENTITY}}', spec['identity']),
        ('{{KB_ROWS}}', kb_rows),
        ('{{ALWAYS_RULES}}', always),
        ('{{WORKFLOW_STEPS}}', workflow),
        ('{{CLOSING}}', spec['closing']),
    ]:
        body = body.replace(token, value)
    return body


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--spec', help='path to the JSON spec')
    parser.add_argument('--force', action='store_true', help='overwrite an existing agent')
    parser.add_argument('--example', action='store_true', help='print a sample spec and exit')
    args = parser.parse_args()

    if args.example:
        print(json.dumps(EXAMPLE_SPEC, indent=2))
        return 0
    if not args.spec:
        parser.error('--spec is required (or use --example)')

    spec = json.loads(Path(args.spec).read_text(encoding='utf-8'))

    errors = validate_spec(spec)
    if errors:
        for err in errors:
            print(f'  ✗ {err}', file=sys.stderr)
        return 1

    target_dir = resolve_dir(spec)
    target = target_dir / f"{spec['name']}.md"
    if target.exists() and not args.force:
        print(f'error: {target} already exists (use --force to overwrite)', file=sys.stderr)
        return 1

    collision = check_color_collision(target_dir, spec['name'], spec['color'])
    if collision:
        print(f"  ! color '{spec['color']}' is already used by {collision}", file=sys.stderr)

    target_dir.mkdir(parents=True, exist_ok=True)
    target.write_text(render(spec), encoding='utf-8')

    claude_md = (Path.home() / '.claude' / 'CLAUDE.md' if spec['scope'] == 'user'
                 else Path(spec['project_root']).expanduser().resolve() / 'CLAUDE.md')

    print(f'✅ Wrote {target}')
    print()
    print('Remaining wiring (not automated — do these next):')

    steps = [
        (f'Add the routing row to {claude_md}:\n'
         f"     | {spec.get('routing_task', '<task description>')} | {spec['name']} |")
    ]
    missing = [p for p, _ in spec['kb_rows']
               if not (Path.home() / '.claude' / 'docs-claude' / 'kb' / p).exists()]
    if missing:
        steps.append(f"Create the KB files that do not yet exist: {', '.join(missing)}\n"
                     '     and add each to docs-claude/kb/README.md')
    steps.append(f'Run: validate_agent.py {target}')

    for i, step in enumerate(steps, 1):
        print(f'  {i}. {step}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
