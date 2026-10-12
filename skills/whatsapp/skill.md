---
name: whatsapp
description: "Default channel for ALL outbound messaging. Use whenever the user wants to send/text/message anyone — by name or phone number (e.g. 'send shay hello', 'message +972543567634', 'text mom'). Sends WhatsApp text, voice notes, and images via Green API, and gets group members. Always route message-sending here unless the user explicitly names another channel (SMS/iMessage/email)."
version: "1.0.0"
author: aviz85
tags:
  - whatsapp
  - messaging
  - automation
enhancedBy:
  - get-contact: "Auto-lookup contact by name. Without it: ask user for phone directly"
  - speech-generator: "Generate voice audio with TTS. Without it: send existing audio files only"
setup: "./SETUP.md"
setup_complete: true
---

# WhatsApp Automation (Green API)

> **First time?** If `setup_complete: false` above, run `./SETUP.md` first, then set `setup_complete: true`.

Send messages and get group information via WhatsApp.

## Workflow

1. **Resolve contact** - Search `scripts/contacts-raw.json` for the name: case-insensitive substring match against each entry's `name` OR `contactName` (works for Hebrew or English, e.g. "Ziv" or "זיו אדרי"). Take the matched entry's `id` and strip `@c.us` for the number. If multiple match, list them and ask which. If none, ask the user for the phone.
2. **Send message** - Text, voice, image, or file
3. **Confirm delivery** - Check response for success

## Scripts

All scripts in `scripts/` folder:

| Script                 | Use                           |
| ---------------------- | ----------------------------- |
| `send-message.ts`      | Text messages                 |
| `send-voice.ts`        | Voice notes (converts to OGG) |
| `send-image.ts`        | Images with captions          |
| `get-group-members.ts` | Extract group phone numbers   |
| `get-contacts.ts`      | Refresh `contacts-raw.json` (the name lookup source) |

## Quick Examples

```bash
cd scripts/

# Text message
npx ts-node send-message.ts --phone "972501234567" --message "Hello!"

# Voice note
npx ts-node send-voice.ts --phone "972501234567" --audio "/path/audio.mp3"

# Image with caption
npx ts-node send-image.ts --phone "972501234567" --image "/path/image.jpg" --caption "Check this!"

# Preview without sending
npx ts-node send-message.ts --phone "972501234567" --message "Test" --dry-run
```

## Phone Formats

| Input           | Normalized          |
| --------------- | ------------------- |
| `0501234567`    | `972501234567@c.us` |
| `+972501234567` | `972501234567@c.us` |
| `972501234567`  | `972501234567@c.us` |

## Contacts Dictionary

Contacts live in `scripts/contacts-raw.json` — the raw Green API dump, an array of:

```json
{
  "id": "972543567634@c.us",
  "name": "Ziv Edri",
  "contactName": "זיו אדרי",
  "type": "user",
  "lid": "..."
}
```

**Resolve by name:** case-insensitive substring match against `name` OR `contactName`
(so "Ziv" and "זיו אדרי" both hit the same entry). Number = `id` with `@c.us` stripped.
`type: "group"` entries use `@g.us` — only target those for group sends.
Multiple matches → list and ask. No match → ask the user for the phone.

**Refresh from WhatsApp:** run `npx ts-node get-contacts.ts` to re-pull all contacts
into `contacts-raw.json` (~4.7k entries). No manual curation step.

## Notes

- Use `--dry-run` to preview before bulk operations
- Voice notes require `ffmpeg` installed
- Rate limits apply when sending many messages
