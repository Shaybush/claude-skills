# Cloudflare skill — setup

One-time. Creates `scripts/.env` with your Cloudflare credentials. The scripts read this file themselves; the model never reads it (`**/.env` is gitignored).

## 1. Get credentials

- **Account ID** — Cloudflare dashboard → account home → right sidebar (*Account ID*).
- **API token** — dashboard → *My Profile* → *API Tokens* → *Create Token*. Scope it to only what's needed:
  - DNS / subdomains → *Zone : DNS : Edit*
  - New domains → *Zone : Zone : Edit*
  - R2 buckets → *Account : Workers R2 Storage : Edit*
  - Secrets Store → *Account : Secrets Store : Edit*

## 2. Create the .env

```bash
cd ~/.claude/skills/cloudflare/scripts
cp .env.example .env
```

Edit `.env` and fill in:

```
CF_ACCOUNT_ID='your-account-id'
CF_API_TOKEN='your-token'
```

## 3. Verify

```bash
cd ~/.claude/skills/cloudflare
python3 scripts/verify_token.py
```

Expect `"success": true` and `"status": "active"`.
