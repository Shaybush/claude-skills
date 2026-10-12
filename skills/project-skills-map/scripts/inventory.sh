#!/usr/bin/env bash
# Cheap structural inventory of a repo — safe on very large trees.
# Uses `git ls-files` when available (instant, already excludes ignored junk).
# Usage: inventory.sh [repo_root] [--churn N]
set -uo pipefail

ROOT="${1:-.}"
[ "${ROOT#--}" != "$ROOT" ] && ROOT="."
CHURN_N=300
for arg in "$@"; do
  case "$arg" in --churn=*) CHURN_N="${arg#*=}" ;; esac
done
cd "$ROOT" || exit 1

EXCLUDE_RE='/(node_modules|\.git|__pycache__|\.venv|venv|dist|build|out|\.next|\.turbo|coverage|vendor|\.intlayer|migrations/versions|\.pytest_cache|target)/'
SRC_RE='\.(py|ts|tsx|js|jsx|mjs|cjs|go|rs|rb|java|kt|swift|php|cs|scala|ex|exs|vue|svelte|sql|graphql|proto|sh|gs)$'

echo "=============================================================="
echo "REPO: $(pwd)"
echo "=============================================================="

if git rev-parse --git-dir >/dev/null 2>&1; then
  echo "git HEAD:  $(git rev-parse --short HEAD 2>/dev/null || echo '(no commits)')"
  echo "git branch: $(git rev-parse --abbrev-ref HEAD 2>/dev/null)"
  FILES="$(git ls-files 2>/dev/null)"
  HAVE_GIT=1
else
  echo "git: not a repository"
  FILES="$(find . -type f 2>/dev/null | sed 's|^\./||')"
  HAVE_GIT=0
fi

SRC="$(printf '%s\n' "$FILES" | grep -Ev "$EXCLUDE_RE" | grep -E "$SRC_RE")"
TOTAL=$(printf '%s\n' "$FILES" | grep -c . )
SRC_TOTAL=$(printf '%s\n' "$SRC" | grep -c . )

echo "tracked files: $TOTAL   source files: $SRC_TOTAL"
echo

echo "--- WORKSPACE / PACKAGE MANIFESTS ---"
printf '%s\n' "$FILES" | grep -Ev "$EXCLUDE_RE" | grep -E '(^|/)(package\.json|pnpm-workspace\.yaml|turbo\.json|nx\.json|lerna\.json|pyproject\.toml|setup\.py|requirements[^/]*\.txt|go\.mod|Cargo\.toml|Gemfile|pom\.xml|build\.gradle[^/]*|composer\.json|appsscript\.json|Dockerfile|docker-compose\.ya?ml|render\.yaml)$' | head -40
echo

echo "--- LANGUAGE MIX (source files by extension) ---"
printf '%s\n' "$SRC" | sed -E 's/.*(\.[a-zA-Z0-9]+)$/\1/' | sort | uniq -c | sort -rn | head -15
echo

echo "--- SOURCE FILES BY DIRECTORY (depth 1) ---"
printf '%s\n' "$SRC" | awk -F/ 'NF>1{print $1} NF==1{print "(root)"}' | sort | uniq -c | sort -rn | head -20
echo

echo "--- SOURCE FILES BY DIRECTORY (depth 2) ---"
printf '%s\n' "$SRC" | awk -F/ 'NF>2{print $1"/"$2} NF==2{print $1} NF==1{print "(root)"}' | sort | uniq -c | sort -rn | head -30
echo

echo "--- SOURCE FILES BY DIRECTORY (depth 3) — candidate convention clusters ---"
printf '%s\n' "$SRC" | awk -F/ 'NF>3{print $1"/"$2"/"$3} NF==3{print $1"/"$2} NF<=2{print $1}' | sort | uniq -c | sort -rn | head -40
echo

if [ "$HAVE_GIT" = "1" ]; then
  echo "--- CHURN: dirs touched most in last $CHURN_N commits (what actually gets worked on) ---"
  git log -n "$CHURN_N" --name-only --pretty=format: 2>/dev/null \
    | grep -Ev "$EXCLUDE_RE" | grep -E "$SRC_RE" \
    | awk -F/ 'NF>3{print $1"/"$2"/"$3} NF==3{print $1"/"$2} NF<=2{print $1}' \
    | sort | uniq -c | sort -rn | head -25
  echo
fi

echo "--- EXISTING SKILLS ---"
if [ -d .claude/skills ]; then
  for d in .claude/skills/*/; do
    [ -f "$d/SKILL.md" ] || continue
    name=$(grep -m1 '^name:' "$d/SKILL.md" 2>/dev/null | sed 's/^name:[[:space:]]*//')
    echo "  ${name:-$(basename "$d")}  ($(wc -l < "$d/SKILL.md" | tr -d ' ') lines)  $d"
  done
else
  echo "  (none — .claude/skills does not exist)"
fi
find . -maxdepth 4 -path ./node_modules -prune -o -type d -name skills -print 2>/dev/null \
  | grep -v '^\./\.claude/skills$' | grep -v node_modules | sed 's/^/  also: /' | head -10
echo

echo "--- CONTEXT DOCS ---"
printf '%s\n' "$FILES" | grep -Ev "$EXCLUDE_RE" | grep -E '(^|/)(CLAUDE\.md|AGENTS\.md|README\.md|CONTRIBUTING\.md)$|^docs-claude/' | head -25
echo

echo "--- MANIFEST ---"
if [ -f .claude/skills-map.json ]; then
  echo "  .claude/skills-map.json present"
  grep -E '"(name|baseline_commit|updated_at)"' .claude/skills-map.json | head -30
else
  echo "  (no .claude/skills-map.json — first run)"
fi
