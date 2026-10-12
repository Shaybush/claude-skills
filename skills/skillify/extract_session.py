#!/usr/bin/env python3
"""
ABOUTME: Extract session context for the skillify skill.
ABOUTME: Mimics Anthropic's getSessionMemoryContent() + extractUserMessages().

Finds the current session's JSONL file and extracts:
1. User messages (filtered, deduped, capped)
2. Session memory summary (if available on disk)

Usage: python3 extract_session.py
"""

import json
import os
import sys
from pathlib import Path


def find_current_session_jsonl() -> Path | None:
    """Find the most recently modified session JSONL in the project dir."""
    claude_dir = Path.home() / ".claude" / "projects"
    if not claude_dir.exists():
        return None

    # Find the most recent .jsonl file across all project dirs
    candidates = sorted(
        claude_dir.rglob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True
    )
    return candidates[0] if candidates else None


def extract_user_messages(jsonl_path: Path, max_messages: int = 50) -> list[str]:
    """Extract user messages from session JSONL, filtering noise."""
    messages = []
    with open(jsonl_path) as f:
        for line in f:
            try:
                obj = json.loads(line.strip())
            except json.JSONDecodeError:
                continue

            if obj.get("type") != "user":
                continue

            content = obj.get("message", {}).get("content", "")
            if isinstance(content, str):
                text = content.strip()
            elif isinstance(content, list):
                text = "\n".join(
                    b.get("text", "")
                    for b in content
                    if isinstance(b, dict) and b.get("type") == "text"
                ).strip()
            else:
                continue

            # Filter noise
            if not text or len(text) < 5:
                continue
            if text.startswith("<system-reminder>") and "</system-reminder>" in text:
                # Strip system reminders, keep any user text after them
                parts = text.split("</system-reminder>")
                text = parts[-1].strip() if len(parts) > 1 else ""
                if not text or len(text) < 5:
                    continue
            if text.startswith("<task-notification>"):
                continue

            # Cap individual messages
            if len(text) > 1000:
                text = text[:1000] + "..."

            messages.append(text)

    # Return the last N messages (most relevant for skillify)
    return messages[-max_messages:]


def find_session_memory(jsonl_path: Path) -> str | None:
    """Find session memory summary.md for this session."""
    # Session memory path: {project_dir}/{session_id}/session-memory/summary.md
    session_id = jsonl_path.stem  # filename without .jsonl
    session_dir = jsonl_path.parent / session_id / "session-memory" / "summary.md"
    if session_dir.exists():
        return session_dir.read_text()
    return None


def main():
    jsonl = find_current_session_jsonl()
    if not jsonl:
        print("No session data found.")
        return

    # Session memory
    memory = find_session_memory(jsonl)
    if memory:
        print("## Session Memory\n")
        print(memory)
        print()

    # User messages
    messages = extract_user_messages(jsonl)
    if messages:
        print("## User Messages\n")
        for i, msg in enumerate(messages, 1):
            print(f"**[{i}]** {msg}\n")
    else:
        print("No user messages found.")


if __name__ == "__main__":
    main()
