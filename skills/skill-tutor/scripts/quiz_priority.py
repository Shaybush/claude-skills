# ABOUTME: Calculate quiz priority using spaced repetition
# ABOUTME: Returns tutorials sorted by review urgency

import os
import sys
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional


# Fibonacci-like intervals based on score (days)
INTERVALS = {
    1: 2,
    2: 2,
    3: 5,
    4: 5,
    5: 13,
    6: 13,
    7: 34,
    8: 34,
    9: 89,
    10: 89,
}


def extract_frontmatter(content: str) -> dict:
    """Extract YAML frontmatter from tutorial content."""
    match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return {}

    frontmatter = {}
    for line in match.group(1).split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            frontmatter[key.strip()] = value.strip()
    return frontmatter


def parse_date(date_str: str) -> Optional[datetime]:
    """Parse DD-MM-YYYY date string."""
    if not date_str or date_str == "null":
        return None
    try:
        return datetime.strptime(date_str, "%d-%m-%Y")
    except ValueError:
        return None


def calculate_priority(tutorial_path: Path) -> dict:
    """Calculate quiz priority for a tutorial."""
    content = tutorial_path.read_text(encoding="utf-8")
    frontmatter = extract_frontmatter(content)

    name = tutorial_path.stem
    concepts = frontmatter.get("concepts", "[]")
    score_str = frontmatter.get("understanding_score", "null")
    last_quizzed_str = frontmatter.get("last_quizzed", "null")

    score = None if score_str == "null" else int(score_str)
    last_quizzed = parse_date(last_quizzed_str)

    now = datetime.now()

    # Never quizzed - highest priority
    if score is None:
        return {
            "name": name,
            "path": str(tutorial_path),
            "score": None,
            "last_quizzed": None,
            "days_overdue": float('inf'),
            "priority": 1,
            "reason": "Never quizzed",
        }

    # Calculate days since quiz
    if last_quizzed:
        days_since = (now - last_quizzed).days
        interval = INTERVALS.get(score, 89)
        days_overdue = days_since - interval

        if days_overdue > 0:
            # Lower score = higher priority when overdue
            priority = 2 + (10 - score) / 10
            reason = f"Overdue by {days_overdue} days (score: {score})"
        else:
            priority = 10 - days_overdue / interval
            reason = f"Due in {-days_overdue} days"
    else:
        days_overdue = float('inf')
        priority = 1.5
        reason = "Has score but no quiz date"

    return {
        "name": name,
        "path": str(tutorial_path),
        "score": score,
        "last_quizzed": last_quizzed_str if last_quizzed else None,
        "days_overdue": days_overdue,
        "priority": priority,
        "reason": reason,
    }


def get_quiz_priorities() -> list[dict]:
    """Get all tutorials sorted by quiz priority."""
    tutorials_dir = Path.home() / "skill-tutor-tutorials" / "tutorials"

    if not tutorials_dir.exists():
        return []

    priorities = []
    for tutorial_file in tutorials_dir.glob("*.md"):
        if tutorial_file.name == "tutorials_index.md":
            continue
        try:
            priority = calculate_priority(tutorial_file)
            priorities.append(priority)
        except Exception as e:
            print(f"[WARN] Could not process {tutorial_file}: {e}")

    # Sort by priority (lower = more urgent)
    priorities.sort(key=lambda x: x["priority"])
    return priorities


def main() -> None:
    """Main entry point."""
    priorities = get_quiz_priorities()

    if not priorities:
        print("[INFO] No tutorials found. Create some first!")
        return

    print("Quiz Priority (most urgent first):\n")

    for i, p in enumerate(priorities, 1):
        score_str = f"score {p['score']}" if p['score'] else "unquizzed"
        print(f"  {i}. {p['name']} ({score_str})")
        print(f"     {p['reason']}")
        print()

    if priorities:
        top = priorities[0]
        print(f"[OK] Recommended quiz: {top['name']}")
        print(f"     Reason: {top['reason']}")


if __name__ == "__main__":
    main()
