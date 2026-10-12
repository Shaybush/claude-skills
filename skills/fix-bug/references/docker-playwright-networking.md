# Running Playwright in Docker against a host-run dev server

Playwright inside the official `mcr.microsoft.com/playwright:vX.Y.Z-<base>` image runs as a separate Linux host from the machine running `pnpm dev` / `npm run dev` in the worktree. `localhost` inside the container resolves to the container itself, not the dev server — this silently produces "connection refused" or a blank-page video, not an obvious error.

## Fix: use host.docker.internal, scoped to the spec file

Point the test at `http://host.docker.internal:<port>` instead of `localhost`, and set it — along with video recording — inside the bug's own spec file rather than editing the shared `playwright.config.ts`:

```ts
test.use({ baseURL: process.env.BASE_URL, video: 'on' });
```

This needs no revert: the spec file is a permanent regression test, and the override lives only in that file, not in checked-in shared config.

- Docker Desktop (macOS/Windows): `host.docker.internal` resolves automatically.
- Linux Docker Engine: needs `--add-host=host.docker.internal:host-gateway` on the `docker run` command (already included in `scripts/playwright-docker-run.sh`).

## Vite-specific gotcha

Vite's dev server validates the `Host` header and rejects requests from unrecognized hosts — a request arriving as `host.docker.internal` gets blocked before it ever reaches the app. This one genuinely requires a config edit, since it's server config, not Playwright's:

```ts
server: { allowedHosts: ['host.docker.internal'] }
```

Vite hot-reloads cleanly on both the edit and the revert. Revert it right after Step 4's capture, and don't let it slip into the commit — Step 5 stages files by name for exactly this reason.

## CORS gotcha

If the frontend calls a separate API origin, requests from inside the container still carry an `Origin` header the API's CORS allow-list may not recognize. If a run fails with a network/CORS error instead of the expected assertion failure, check the API's CORS configuration before concluding the fix itself is broken.

## Matching the Docker image to the project

The image's bundled browser binaries must match the installed `@playwright/test` version — a mismatch causes obscure failures (e.g. protocol version errors) that look unrelated to the actual bug. `scripts/playwright-docker-run.sh` reads the version from `package.json` automatically; don't hardcode an image tag.

## Installing dependencies in the worktree

`EnterWorktree` gives a clean checkout with no `node_modules`. Install once, right after entering (`pnpm install`) — the before and after captures both run in this same worktree, so there's no need to reinstall between them.
