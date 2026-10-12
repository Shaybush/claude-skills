# Skill Tutor

A Claude Code skill that turns Claude into your personal tutor. Creates personalized tutorials using YOUR actual projects, tracks learning progress, and uses spaced repetition for retention.

## Why This Exists

Most AI tutoring is generic: "Here's how X works" with foo/bar examples. This skill is different:

- **Uses YOUR code** - tutorials reference your actual projects (or creates relevant examples if you don't have projects yet)
- **Tracks progress** - knows what you've learned, what needs review

**No projects? No problem.** The tutor adapts - asks what you're building and creates practical examples.
- **Spaced repetition** - quizzes you at optimal intervals for retention
- **Mental models, not procedures** - teaches HOW to think, not just WHAT to do

## Installation

1. Copy the `skill-tutor` folder to your Claude Code skills directory:
   ```bash
   # Windows
   cp -r skill-tutor ~/.claude/skills/

   # Mac/Linux
   cp -r skill-tutor ~/.claude/skills/
   ```

2. Run setup to create the tutorials directory:
   ```bash
   python ~/.claude/skills/skill-tutor/scripts/setup_tutor.py
   ```

## Usage

In Claude Code, just say:

| Command | What it does |
|---------|--------------|
| `teach me [topic]` | Creates personalized tutorial on any topic |
| `quiz me` | Spaced repetition quiz on what you've learned |
| `continue` | See what's next based on your learning path |
| `review progress` | See learning summary and recommendations |

Or invoke directly with `/skill-tutor`.

## How It Works

### First Time Setup

The tutor conducts a brief interview to understand:
- Your technical background
- Current projects (source of examples)
- Learning style preference

This creates `~/skill-tutor-tutorials/learner_profile.md`.

### Tutorial Creation

When you ask to learn something, the tutor:

1. Reads your learner profile
2. Researches the topic (web search if needed)
3. Creates a personalized tutorial using YOUR projects as examples
4. Saves to `~/skill-tutor-tutorials/tutorials/[topic].md`

### Spaced Repetition

The quiz system uses Fibonacci-like intervals:

| Score | Next Review |
|-------|-------------|
| 1-2   | 2 days      |
| 3-4   | 5 days      |
| 5-6   | 13 days     |
| 7-8   | 34 days     |
| 9-10  | 89 days     |

Run `quiz me` and the system picks the most urgent topic based on:
1. Never-quizzed tutorials (highest priority)
2. Overdue low-scoring concepts
3. Mastered concepts due for review

## Teaching Philosophy

The skill follows four principles:

1. **Mental Models, Not Procedures** - Teach HOW to think, not WHAT to do
2. **Real Examples, Not Abstract** - Use the learner's actual work
3. **Show the Journey** - "Here's what you'd try... why it fails... the insight"
4. **One Deep > Ten Shallow** - Master one concept before moving on

See `references/principles.md` for the full teaching philosophy.

## Directory Structure

```
~/skill-tutor-tutorials/
├── learner_profile.md      # Your background, projects, learning style
├── tutorials/              # Personalized tutorials by topic
│   ├── prompt-caching.md
│   ├── context-engineering.md
│   └── ...
└── topics/
    └── knowledge_map.md    # Connections between concepts
```

## Example Tutorial Output

The tutor creates tutorials with this structure:

- **Why This Matters** - Connect to your goals
- **The Problem** - What challenge this addresses
- **The Insight** - Core mental model experts have
- **In Your Project** - Concrete examples from YOUR code
- **The Pattern** - How to apply it
- **Common Mistakes** - What to avoid
- **Practice** - Exercise using your own project

## Scripts

- `scripts/setup_tutor.py` - Initialize the tutorials directory
- `scripts/quiz_priority.py` - Calculate which topic to quiz next

## License

MIT

## Contributing

Issues and PRs welcome. The skill is designed to be extended - add your own teaching principles to `references/principles.md`.
