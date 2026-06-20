---
name: cloudflare
description: "Manage Cloudflare via the v4 API. Use whenever the user wants to work with their Cloudflare account — add a subdomain / DNS record, create or delete a domain (zone), create or list R2 buckets, add a secret to the Secrets Store, or verify their API token. Each operation is a script in scripts/ that loads the token from scripts/.env itself, so credentials are never read by the model."
---

# Cloudflare (v4 API)

Run Cloudflare operations through the scripts in `scripts/`. Each script loads credentials from `scripts/.env` at runtime and prints the JSON response. **Never read `scripts/.env`** — a secrets guard blocks credential files, and the scripts don't need the model to; they read it themselves.

> **First time?** Follow `./SETUP.md` to create `scripts/.env`. If a call prints `Missing scripts/.env`, setup hasn't been done.

## Workflow

1. Pick the script for the task from the table below.
2. Run it with `python3 scripts/<script>.py [flags]` (add `--help` to see flags).
3. Read the JSON response — check `success: true`; on failure the script exits non-zero and prints `errors[].message`.

## Scripts

All scripts live in `scripts/`. Run from the skill folder.

| Script | Use |
| --- | --- |
| `verify_token.py` | Check the API token is active |
| `dns_create.py` | Create a DNS record / subdomain |
| `dns_list.py` | List DNS records on a zone (find record IDs) |
| `dns_delete.py` | Delete a DNS record by ID |
| `zone_create.py` | Add a new domain (zone) |
| `zone_list.py` | List zones, or resolve a domain to its zone ID (`--name`) |
| `zone_delete.py` | Delete a zone (domain) |
| `r2_create.py` | Create an R2 bucket |
| `r2_list.py` | List R2 buckets |
| `r2_delete.py` | Delete an R2 bucket (must be empty) |
| `secret_add.py` | Add a secret to the Secrets Store |
| `secret_list.py` | List Secrets Store secrets (names only) |

`_cf.py` is the shared helper (auth + requests); not run directly except `python3 scripts/_cf.py` for its self-check.

## Quick examples

```bash
cd ~/.claude/skills/cloudflare

# Verify token
python3 scripts/verify_token.py

# Add a subdomain: sub.example.com -> 203.0.113.10, proxied
python3 scripts/dns_create.py --zone example.com --name sub.example.com --content 203.0.113.10 --proxied

# Point a subdomain at another host (CNAME)
python3 scripts/dns_create.py --zone example.com --type CNAME --name app.example.com --content myapp.onrender.com

# List records to get an ID, then delete one
python3 scripts/dns_list.py --zone example.com --name sub.example.com
python3 scripts/dns_delete.py --zone example.com --id <RECORD_ID>

# Add a new domain (then set the returned name_servers at the registrar)
python3 scripts/zone_create.py --name example.com

# Create / list an R2 bucket
python3 scripts/r2_create.py --name my-bucket --location weur
python3 scripts/r2_list.py

# Add a secret to the Secrets Store
python3 scripts/secret_add.py --name MY_SECRET --value 's3cr3t-value'
```

## Notes

- `--zone` takes the **domain name**; scripts resolve it to the zone ID automatically.
- `dns_create.py`: `--proxied` only valid for A/AAAA/CNAME; MX needs `--priority`.
- `zone_create.py` does not move the domain — the user must point the registrar at the returned `name_servers` before it activates.
- Secret values are write-only; no script returns a value after it's set. `--value` is passed as an argument (briefly visible in the process list).
- Token scopes per task: DNS → *Zone:DNS:Edit*; zones → *Zone:Zone:Edit*; R2 → *Account:Workers R2 Storage:Edit*; secrets → *Account:Secrets Store:Edit*.

## Adding an operation

Drop a new `scripts/<verb>.py` that imports `api`/`out` from `_cf.py` and add a row to the table. No other wiring needed — `_cf.py` handles any method/path.
