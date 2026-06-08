#!/usr/bin/env python3
'''PreToolUse secrets guard for Claude Code.

Runs before Read/Edit/Write/NotebookEdit/Bash. If the tool targets a secret
file (.env, private keys, credentials, a secrets/ dir), it writes an explanation
to stderr and exits 2, so Claude Code BLOCKS the call and Claude never sees the
file contents. Any other case exits 0 and the call proceeds untouched.

Hook contract: exit 0 = allow, exit 2 = block (stderr is returned to Claude).
Malformed or unknown input fails open (exit 0) so the guard never wedges work.
'''
import json
import re
import sys

# File tools whose target path we inspect directly.
PATH_TOOLS = {'Read', 'Edit', 'Write', 'MultiEdit', 'NotebookEdit'}

# A secrets directory anywhere in the path.
SECRET_DIR = re.compile(r'(?:^|/)\.?secrets?(?:/|$)', re.IGNORECASE)

# Secret-file signatures, matched against a path or anywhere inside a command.
# The .env branch skips example/template files (placeholders, not real secrets).
SECRET_FILE = re.compile(
    r'''(?ix)
    (?:^|/|\s|["'`=:])                                                  # left boundary
    (?:
        \.env(?:\.(?!(?:example|sample|template|dist|defaults)\b)[\w.-]+)?
      | \.aws/credentials
      | \.git-credentials
      | \.npmrc | \.pypirc | \.netrc | \.pgpass
      | id_(?:rsa|ed25519|ecdsa|dsa)
      | credentials\.json
      | service[-_]?account[\w.-]*\.json
      | [\w.-]+\.(?:pem|key|pfx|p12|keystore|jks)
    )
    (?:["'`\s:]|$)                                                      # right boundary
    ''',
)


def secret_reason(text):
    '''Return a short reason string if text references a secret, else None.'''
    if SECRET_DIR.search(text):
        return 'a secrets directory'
    if SECRET_FILE.search(text):
        return 'a secret or credential file'
    return None


def targets_for(tool, tool_input):
    '''Collect the strings to inspect for a given tool call.'''
    if tool in PATH_TOOLS:
        return [str(tool_input[k]) for k in ('file_path', 'notebook_path') if tool_input.get(k)]
    if tool == 'Bash':
        cmd = tool_input.get('command')
        return [str(cmd)] if cmd else []
    return []


def main():
    try:
        data = json.loads(sys.stdin.read())
    except (ValueError, TypeError):
        return 0
    tool = data.get('tool_name', '')
    tool_input = data.get('tool_input') or {}
    for target in targets_for(tool, tool_input):
        reason = secret_reason(target)
        if reason:
            sys.stderr.write(
                f'Blocked by secrets guard: this targets {reason}. '
                'Accessing secret files (.env, private keys, credentials) is not '
                'allowed and their contents must not be read. Do not retry this. '
                'Instead use a template such as .env.example, ask the user for the '
                'specific value, or reference the environment variable by name '
                'without reading the file.\n'
            )
            return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
