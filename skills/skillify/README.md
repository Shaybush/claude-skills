# skillify

A skill that turns the session you just finished into a reusable skill.

You ran through a process — maybe doc generation, maybe a release sequence, maybe a debugging workflow. It worked. You don't want to walk Claude through it again from scratch next time. `/skillify` reads the session, interviews you about it, and writes a clean SKILL.md.

## Why this exists

The repetition rule says "anything you ask Claude to do twice, make it a skill." The friction is the second word: *make*. Sitting down to write a SKILL.md after you've just finished the real work is exactly the moment your motivation is gone. Skillify removes that friction — it captures the workflow while the session is still warm.

The other thing it does, which a one-shot generator wouldn't, is **interview you**. It doesn't try to guess the skill from the transcript. It analyzes the session, proposes a name and shape, then walks you through four rounds of structured questions — high-level confirmation, steps and execution mode, per-step success criteria, trigger phrases. The skill that comes out reflects how you actually want the workflow to run, not what a model inferred from your tool calls.

## How it works

1. Reads the current session's JSONL from `~/.claude/projects/.../*.jsonl` — pulls your messages (where you corrected course is gold) and the tool calls (which become the skill's `allowed-tools`).
2. Analyzes the session for the repeatable process, the inputs, the steps, and the success criteria.
3. Interviews you in four rounds via `AskUserQuestion`:
   - Round 1: skill name + description + high-level goal
   - Round 2: step list, arguments, inline vs forked execution, save location
   - Round 3: per-step success criteria, human checkpoints, parallelism, hard rules
   - Round 4: trigger phrases and gotchas
4. Writes the SKILL.md with frontmatter, numbered steps, per-step `Success criteria`, and any annotations the interview surfaced.

## Installation

```bash
git clone https://github.com/Nitzan94/claude-code-skills.git
cp -r claude-code-skills/skills/skillify ~/.claude/skills/
```

## Usage

At the end of a session whose workflow you want to capture:

```
/skillify [optional description of the process]
```

Or just say "skillify this" / "make this a skill" / "save this workflow" — the description triggers it.

## What you end up with

A SKILL.md at either `.claude/skills/<name>/SKILL.md` (project-local) or `~/.claude/skills/<name>/SKILL.md` (personal, follows you everywhere), with:

- Frontmatter: `name`, `description`, `when_to_use` (with trigger phrases), `allowed-tools`, optional `arguments` and `context: fork`
- Numbered steps, each with a required **Success criteria** line
- Optional per-step annotations: **Execution** (Direct / Task agent / Teammate / [human]), **Artifacts**, **Human checkpoint**, **Rules**

The format is the same one the skill itself uses — every skillify-generated skill is a candidate input for the next skillify run if you want to refine it.

## License

MIT
