# ABOUTME: Initialize skill-tutor tutorials directory structure
# ABOUTME: Creates ~/skill-tutor-tutorials/ with required folders

import os
import sys
from pathlib import Path
from datetime import datetime


def setup_tutor() -> None:
    """Initialize the skill tutor tutorials directory."""
    home = Path.home()
    base_dir = home / "skill-tutor-tutorials"

    directories = [
        base_dir,
        base_dir / "tutorials",
        base_dir / "topics",
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"[OK] Created: {directory}")

    # Create index file if not exists
    index_file = base_dir / "tutorials_index.md"
    if not index_file.exists():
        index_file.write_text(f"""# Tutorials Index

Created: {datetime.now().strftime('%d-%m-%Y')}

## Completed Tutorials
(none yet)

## In Progress
(none yet)

## Planned
(none yet)
""", encoding="utf-8")
        print(f"[OK] Created: {index_file}")
    else:
        print(f"[INFO] Already exists: {index_file}")

    print("\n[OK] Skill tutor setup complete!")
    print(f"[INFO] Tutorials will be stored in: {base_dir}")


if __name__ == "__main__":
    setup_tutor()
