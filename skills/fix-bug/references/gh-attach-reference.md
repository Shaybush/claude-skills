# gh CLI file attachments — reference

GitHub CLI can upload local images and videos and reference them inline in an issue, PR, or comment, without opening a browser. GA since gh v2.99.0 (2026-09-01).

## Supported commands

`gh issue create`, `gh issue edit`, `gh issue comment`, `gh pr create`, `gh pr edit`, `gh pr comment`.

## Syntax

```bash
gh pr create --title "DT-123: fix mobile nav overflow" --body "..." \
  --attach ./before.webm --attach ./after.webm
gh pr comment 42 --attach ./after.webm
gh issue create --title "..." --body "..." --attach './screenshot.png#The broken layout'
```

- Repeatable: pass `--attach` once per file, up to 50 files per command. The same file cannot be attached twice in one command.
- Alt text: append `#Alt text` to the path — **images only**. Video renders as a player and cannot take alt text.
- If the body already references a local file via `![alt](./path.png)`, that reference is rewritten to point at the uploaded asset instead of being duplicated. Anything attached but not referenced in the body gets appended at the end of the comment.

## Formats & limits

- Images: PNG, JPEG, GIF, WebP, SVG — 10MB max each.
- Video: MP4, MOV, WebM — 10MB max on free plans, 100MB max on paid plans.
- Requires push/write access to the target repository.
- github.com only — GitHub Enterprise Server isn't supported yet (as of gh v2.99–2.100).

## If a file is oversized

Compress before attaching rather than skipping it:

```bash
ffmpeg -i before.webm -crf 32 -b:v 0 before-small.webm
```

Re-check the size and raise `-crf` (higher = smaller file, lower quality) until it clears the limit.
