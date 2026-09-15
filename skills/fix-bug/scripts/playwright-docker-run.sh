#!/usr/bin/env bash
# Run a single Playwright spec inside the official Playwright Docker image,
# pointed at a dev server running on the host machine, with video recording
# (requires `use: { video: 'on' }` in playwright.config.ts — see the skill's
# references/docker-playwright-networking.md).
#
# Required env vars:
#   SPEC        Path to the spec file, relative to the repo/worktree root,
#               e.g. e2e/bug-1234.spec.ts
#   PORT        Port the host dev server is listening on, e.g. 3000
#   OUTPUT_DIR  Where Playwright should write test-results (videos land here)
#
# Optional env vars:
#   PROJECT     Playwright project name to run (e.g. chromium). Omitted by
#               default since not every playwright.config.ts defines named
#               projects.
#   GREP        --grep pattern to select a single test by title
#
# Run from the repo root (or the disposable worktree root for a "before"
# capture) — the current directory is what gets mounted into the container.
set -euo pipefail

: "${SPEC:?set SPEC to the spec file path}"
: "${PORT:?set PORT to the dev server port}"
: "${OUTPUT_DIR:?set OUTPUT_DIR for test-results}"

PW_VERSION="$(node -e '
  const pkg = require("./package.json");
  const v = (pkg.devDependencies || {})["@playwright/test"] || (pkg.dependencies || {})["@playwright/test"];
  if (!v) process.exit(1);
  console.log(v.replace(/^[\^~]/, ""));
')" || { echo "Could not find @playwright/test in package.json — install it first." >&2; exit 1; }

IMAGE="mcr.microsoft.com/playwright:v${PW_VERSION}-noble"
mkdir -p "$OUTPUT_DIR"

ARGS=(npx playwright test "$SPEC" --output="$OUTPUT_DIR")
[ -n "${PROJECT:-}" ] && ARGS+=(--project="$PROJECT")
[ -n "${GREP:-}" ] && ARGS+=(--grep "$GREP")

docker run --rm \
  --ipc=host \
  --add-host=host.docker.internal:host-gateway \
  -e "BASE_URL=http://host.docker.internal:${PORT}" \
  -v "$(pwd)":/work \
  -w /work \
  "$IMAGE" \
  "${ARGS[@]}"

echo "--- recorded videos ---"
find "$OUTPUT_DIR" -name '*.webm'
